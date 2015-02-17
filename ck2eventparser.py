from pyparsing import *
import pprint
import ck2locparser

class CK2EventParser(object):

    def __init__(self, localization_dir="localisation"):
        super(CK2EventParser, self).__init__()
        self.pd_text = Forward()
        self.pd_string = dblQuotedString.setParseAction(removeQuotes)
        self.pd_symbol = Word(alphanums + "_" + "-" + ".")
        self.pd_text << ( self.pd_string | self.pd_symbol )
        self.pd_number = Combine(Optional('-') + ( '0' | Word('123456789', nums) ) +
                            Optional('.' + Word(nums)) +
                            Optional(Word('eE', exact=1) + Word(nums + '+-', nums)))
        self.pd_event = Forward()
        self.pd_value = Forward()
        self.pd_simple_value = Forward()
        self.pd_dict = Forward()
        self.pd_entry = Group(self.pd_symbol + Suppress('=') + self.pd_value)
        self.pd_event << delimitedList(self.pd_entry, delim=LineEnd())
        self.pd_value << ( self.pd_number | self.pd_text | self.pd_dict )
        self.pd_multi_simple_values = delimitedList(self.pd_entry, delim=White(' '))
        self.pd_dict << Suppress('{') + Optional(self.pd_multi_simple_values) + Optional(self.pd_event) + Suppress('}')
        self.pd_comment = pythonStyleComment
        self.pd_event.ignore(self.pd_comment)
        self.pd_number.setParseAction(self.__class__.convert_numbers)
        if localization_dir:
            self.loc_parser = ck2locparser.LocalizationParser(localization_dir)
            self.pd_entry.setParseAction(self.insert_english_strings)

    @property
    def parse_element(self):
        return self.pd_event

    def parse(self, text, as_list=True):
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

    def insert_english_strings(self, s, l, toks):
        tok = toks[0]
        if hasattr(tok, "__len__"):
            if isinstance(l, basestring):
                pass
            elif len(tok) >= 2 and (tok[0] == 'name' or tok[0] == 'desc'):
                if not self.loc_parser:
                    raise ValueError("Need to specify a localization file parser")
                # print "TOK", tok[0], tok[1], locparser.strings[tok[1]][0].encode("iso-8859-1")
                if self.loc_parser.strings.get(tok[1]):
                    toks[0][1] = self.loc_parser.strings[tok[1]][0]
                return toks


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




def parse_event_file(path):
    event_text = open(path, "rb").read()
    event_text = event_text.replace('\xe2', ' ')
    event_text = event_text.replace('\xa0', ' ')
    top_parser = CK2TopLevelEventParser()
    results = top_parser.parse(event_text)
    event_parser = CK2EventValueParser()
    for result in results:
        name = result[0]
        print "%s = " % (name)
        event_data = event_parser.parse(result[1])
        pprint.pprint(event_data)
    return results


if __name__ == "__main__":
    import sys
    results = parse_event_file(sys.argv[1])
    #pprint.pprint(results.asList())
    #results2 = convert_to_dict(results.asList())
    #pprint.pprint(results2)
