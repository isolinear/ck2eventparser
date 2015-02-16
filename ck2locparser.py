import unicodecsv as csv
import os, logging, os.path

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p', level=logging.INFO)


class LocalizationParser(object):

    def __init__(self, localization_dir=None):
        self.strings = {}
        if localization_dir:
            for f in os.listdir(localization_dir):
                filepath = os.path.join(localization_dir,f)
                if not os.path.isdir(filepath):
                    self.parse_file(filepath)
                    logging.debug("parsed %s" % filepath)

    def parse_file(self, path):
        with open(path, 'rUb') as csvfile:
            reader = csv.reader(csvfile, encoding="ISO-8859-1", delimiter=";")
            for row in reader:
                if row[0].startswith("#"):
                    continue
                if self.strings.get(row[0]):
                    logging.warning("Warning: %s exists" % row[0])
                else:
                    self.strings[row[0]] = row[1:]
        return self.strings

