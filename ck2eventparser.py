from pyparsing import *
import pyparsing as pp
import logging, pprint
import ck2locparser

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p', level=logging.INFO)

loc_parser = None

class CK2EventParser(object):

    def __init__(self):
        super(CK2EventParser, self).__init__()
        self.pd_text = Forward()
        self.pd_string = dblQuotedString.setParseAction(removeQuotes)
        self.pd_symbol = Word(alphanums + "_" + "-" + "." + ":")
        self.pd_reference = Suppress('[') + Optional(self.pd_symbol) + Suppress(']')
        self.pd_text << ( self.pd_string | self.pd_symbol | self.pd_reference)
        self.pd_number = Combine(Optional('-') + ( '0' | Word('123456789', nums) ) +
                            Optional('.' + Word(nums)) +
                            Optional(Word('eE', exact=1) + Word(nums + '+-', nums)))
        self.pd_event = Forward()
        self.pd_value = Forward()
        self.pd_simple_value = Forward()
        self.pd_dict = Forward()
        self.pd_entry = Group(self.pd_symbol + Suppress('=') + self.pd_value)
        self.pd_event << delimitedList(self.pd_entry, delim=LineEnd())
        self.pd_multi_simple_values = Suppress('{') + delimitedList(self.pd_entry, delim=White(' ')) + Suppress('}')
        self.pd_multi_simple_numbers = Suppress('{') + delimitedList(self.pd_number, delim=White(' ')) + Suppress('}')
        self.pd_value << ( self.pd_number | self.pd_text | self.pd_dict | self.pd_multi_simple_values | self.pd_multi_simple_numbers)
        self.pd_dict << Suppress('{') + Optional(self.pd_event) + Suppress('}')
        self.pd_comment = pythonStyleComment
        self.pd_event.ignore(self.pd_comment)
        self.pd_number.setParseAction(self.__class__.convert_numbers)
        self.callbacks = {"trigger":None, "option":None, "mean_time_to_happen":None}


    @property
    def parse_element(self):
        return self.pd_event

    def parse(self, text, as_list=True, use_localization_dir=None):
        if use_localization_dir:
            global loc_parser
            if (not loc_parser) or (loc_parser.localization_dir != use_localization_dir):
                loc_parser = ck2locparser.LocalizationParser(use_localization_dir)
            self.pd_entry.setParseAction(self.postprocess)
        results = self.parse_element.parseString(text)
        if as_list:
            return results.asList()
        return results

    @classmethod
    def convert_numbers(cls, s, l, toks):
        n = toks[0]
        try:
            return int(n)
        except ValueError, ve:
            return float(n)

    def postprocess(self, s, l, toks):
        global loc_parser
        tok = toks[0]
        if hasattr(tok, "__len__"):
            if isinstance(l, basestring):
                pass
            elif len(tok) >= 2 and (tok[0] == 'name' or tok[0] == 'desc' or tok[0]=='tooltip' or tok[0] == 'text'):
                if not loc_parser:
                    raise ValueError("Need to specify a localization file parser")
                # print "TOK", tok[0], tok[1], locparser.strings[tok[1]][0].encode("iso-8859-1")
                if loc_parser.strings.get(tok[1]):
                    toks[0][1] = loc_parser.strings[tok[1]][0]
                else:
                    logging.warning("failed to find the token %s" % (tok[1]))
                return toks
            elif tok[0] in self.callbacks:
                if self.callbacks.get(tok[0]):
                    self.callbacks[tok[0]](s[l:pp.getTokensEndLoc()])

    def register_callback(self, key, handler):
        if key in self.callbacks:
            self.callbacks[key] = handler
        else:
            raise ValueError("Not a supported callback endpoint.  Supported endpoints are %s" % (','.join(self.callbacks.keys())))

class CK2TopLevelEventParser(CK2EventParser):

    def __init__(self):
        super(CK2TopLevelEventParser, self).__init__()
        self.pd_top_level_event = Forward()
        self.pd_top_level_entry = Forward()
        self.pd_top_level_value = Forward()
        self.pd_top_level_dict = Forward()
        self.pd_top_level_dict << originalTextFor(Suppress('{') + Optional(self.pd_multi_simple_values) + Optional(self.pd_event) + Suppress('}'))
        self.pd_top_level_entry << Group(self.pd_symbol + Suppress('=') + self.pd_top_level_value)
        self.pd_top_level_event << delimitedList(self.pd_top_level_entry, delim=LineEnd())
        self.pd_top_level_value << (self.pd_number | self.pd_text | self.pd_top_level_dict)
        self.pd_top_level_event.ignore(self.pd_comment)

    @property
    def parse_element(self):
        return self.pd_top_level_event

class CK2EventValueParser(CK2EventParser):

    def __init__(self):
        super(CK2EventValueParser, self).__init__()

    @property
    def parse_element(self):
        return self.pd_value


class CK2Event(object):

    def __init__(self, e_type, text):
        self.id = ""
        self.e_type = e_type
        self.raw = text
        self.trigger_text = ""
        self.options = []
        self.data = None

    def __repr__(self):
        return "<CK2Event e_type=%s text=%s>" % (self.e_type, self.raw[:16].encode('utf-8'))

    def trigger_callback(self, trigger_text):
        #print "called into here with", trigger_text
        self.trigger_text = trigger_text
        #print "after setting:", self.trigger

    def options_callback(self, options_text):
        self.options.append(options_text)

    def mtth_callback(self, mtth_text):
        self.mtth = mtth_text

# def convert_to_dict(result):
#     return [convert_list_of_lists_to_dict(l) for l in result]
#
# def convert_list_of_lists_to_dict(l):
#     if hasattr(l, "__len__") :
#         if isinstance(l, basestring):
#             return l
#         elif len(l) == 2:
#             if isinstance(l[0], basestring):
#                 key = l[0]
#                 value = convert_list_of_lists_to_dict(l[1])
#                 return {key:value}
#             else:
#                 return [convert_list_of_lists_to_dict(sub_l) for sub_l in l]
#         elif len(l) > 2:
#             return [convert_list_of_lists_to_dict(sub_l) for sub_l in l]
#         else:
#             return l
#     else:
#         return l




def parse_event_file(path, localization_dir="localisation"):
    event_text = open(path, "rb").read()
    event_text = event_text.replace('\xe2', ' ')
    event_text = event_text.replace('\xa0', ' ')
    top_parser = CK2TopLevelEventParser()
    results = top_parser.parse(event_text)
    event_parser = CK2EventValueParser()
    for result in results:
        event = CK2Event(result[0], result[1])
        event_parser.register_callback("trigger", event.trigger_callback)
        event_parser.register_callback("option", event.options_callback)
        event_parser.register_callback("mean_time_to_happen", event.mtth_callback)
        event.data = event_parser.parse(result[1],
                                        use_localization_dir=localization_dir
        )
        print event.e_type, " = "
        pprint.pprint(event.data)
        #print "RAW TRIGGER ", event.trigger_text
        #print event.options
    return results


if __name__ == "__main__":
    import sys
    localization_dir = None
    if len(sys.argv) > 2:
        localization_dir = sys.argv[2]
    results = parse_event_file(sys.argv[1], localization_dir)
    #pprint.pprint(results.asList())
    #results2 = convert_to_dict(results.asList())
    #pprint.pprint(results2)
