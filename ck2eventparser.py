from pyparsing import *
import pprint

pd_text = Forward()
pd_string = dblQuotedString.setParseAction(removeQuotes)
pd_symbol = Word(alphanums + "_" + "-" + ".")
pd_text << ( pd_string | pd_symbol )
pd_number = Combine(Optional('-') + ( '0' | Word('123456789', nums) ) +
                    Optional('.' + Word(nums)) +
                    Optional(Word('eE', exact=1) + Word(nums + '+-', nums)))

pd_event = Forward()
pd_value = Forward()
pd_simple_value = Forward()
pd_dict = Forward()
pd_entry = Group(pd_symbol + Suppress('=') + pd_value)
pd_event << delimitedList(pd_entry, delim=LineEnd())
pd_value << ( pd_number | pd_text | pd_dict )

pd_simple_value << ( pd_number | pd_text )
pd_multi_simple_values = delimitedList(Group(pd_symbol + Suppress('=') + pd_simple_value), delim=White(' '))

pd_dict << Suppress('{') + Optional(pd_multi_simple_values) + Optional(pd_event) + Suppress('}')
pd_comment = pythonStyleComment
pd_event.ignore(pd_comment)


def convert_numbers(s, l, toks):
    n = toks[0]
    try:
        return int(n)
    except ValueError, ve:
        return float(n)

def convert_to_dict(result):
    return [convert_list_of_lists_to_dict(l) for l in result]

def convert_list_of_lists_to_dict(l):
    if hasattr(l, "__len__") :
        if isinstance(l, basestring):
            return l
        elif len(l) == 2:
            if isinstance(l[0], basestring):
                key = l[0]
                value = convert_list_of_lists_to_dict(l[1])
                return {key:value}
            else:
                return [convert_list_of_lists_to_dict(sub_l) for sub_l in l]
        elif len(l) > 2:
            return [convert_list_of_lists_to_dict(sub_l) for sub_l in l]
        else:
            return l
    else:
        return l


pd_number.setParseAction(convert_numbers)

def parse_event_file(path):
    event_text = open(path, "rb").read()
    event_text = event_text.replace('\xe2', ' ')
    event_text = event_text.replace('\xa0', ' ')
    results = pd_event.parseString(event_text)
    return results


if __name__ == "__main__":
    import sys
    results = parse_event_file(sys.argv[1])
    pprint.pprint(results.asList())
    results2 = convert_to_dict(results.asList())
    pprint.pprint(results2)
