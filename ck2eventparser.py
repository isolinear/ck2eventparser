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
pd_value << ( pd_number | pd_text | Group(pd_dict) )

pd_simple_value << ( pd_number | pd_text )
pd_multi_simple_values = delimitedList(Group(pd_symbol + Suppress('=') + pd_simple_value), delim=White(' '))

pd_dict << Dict(Suppress('{') + Optional(pd_multi_simple_values) + Optional(pd_event) + Suppress('}'))
pd_comment = pythonStyleComment
pd_event.ignore(pd_comment)


def convert_numbers(s, l, toks):
    n = toks[0]
    try:
        return int(n)
    except ValueError, ve:
        return float(n)


pd_number.setParseAction(convert_numbers)


def parse_event_file(path):
    event_text = open(path, "rb").read()
    event_text = event_text.replace('\xa0', ' ')
    results = pd_event.parseString(event_text)
    pprint.pprint(results.asList())
    return results

if __name__ == "__main__":
    import sys
    parse_event_file(sys.argv[1])