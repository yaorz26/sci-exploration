import urllib.parse

class UrlPath:
    """
    The  class is a utility for encapsulating and manipulating the path component of a URL, including adding nodes, parsing path strings, and building path strings with optional encoding.
    """

    def __init__(self):
        """
        Initializes the UrlPath object with an empty list of segments and a flag indicating the presence of an end tag.
        """
        self.segments = []
        self.with_end_tag = False

    def add(self, segment):
        """
        Adds a segment to the list of segments in the UrlPath.
        :param segment: str, the segment to add.
        """
        self.segments.append(segment)

    def parse(self, path, charset):
        """
        Parses a given path string and populates the list of segments in the UrlPath.
        :param path: str, the path string to parse.
        :param charset: str, the character encoding of the path string.
        """
        fixed_path = self.fix_path(path)
        self.segments = fixed_path.split('/')
        if self.segments and self.segments[-1] == '':
            self.segments.pop()
        if self.with_end_tag and self.segments and self.segments[-1] != '':
            self.segments.append('')

    @staticmethod
    def fix_path(path):
        """
        Fixes the given path string by removing leading and trailing slashes.
        :param path: str, the path string to fix.
        :return: str, the fixed path string.
        """
        return path.strip('/')

    def build(self, encoding='utf-8'):
        """
        Builds the path string from the list of segments with optional encoding.
        :param encoding: str, the character encoding of the path string.
        :return: str, the built path string.
        """
        path = '/'.join(self.segments)
        if encoding:
            path = urllib.parse.quote(path, encoding=encoding)
        return path