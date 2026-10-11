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
        >>> url_path = UrlPath()
        >>> url_path.add('foo')
        >>> url_path.add('bar')

        url_path.segments = ['foo', 'bar']
        """
        self.segments.append(segment)

import unittest


class UrlPathTestAdd(unittest.TestCase):
    def test_add_1(self):
        url_path = UrlPath()
        url_path.add('foo')
        url_path.add('bar')
        self.assertEqual(url_path.segments, ['foo', 'bar'])

    def test_add_2(self):
        url_path = UrlPath()
        url_path.add('aaa')
        url_path.add('bbb')
        self.assertEqual(url_path.segments, ['aaa', 'bbb'])

    def test_add_3(self):
        url_path = UrlPath()
        url_path.add('123')
        self.assertEqual(url_path.segments, ['123'])

    def test_add_4(self):
        url_path = UrlPath()
        url_path.add('ddd')
        self.assertEqual(url_path.segments, ['ddd'])

    def test_add_5(self):
        url_path = UrlPath()
        url_path.add('eee')
        self.assertEqual(url_path.segments, ['eee'])


class UrlPathTestParse(unittest.TestCase):
    def test_parse_1(self):
        url_path = UrlPath()
        url_path.parse('/foo/bar/', 'utf-8')
        self.assertEqual(url_path.segments, ['foo', 'bar'])
        self.assertEqual(url_path.with_end_tag, True)

    def test_parse_2(self):
        url_path = UrlPath()
        url_path.parse('aaa/bbb', 'utf-8')
        self.assertEqual(url_path.segments, ['aaa', 'bbb'])
        self.assertEqual(url_path.with_end_tag, False)

    def test_parse_3(self):
        url_path = UrlPath()
        url_path.parse('/123/456/', 'utf-8')
        self.assertEqual(url_path.segments, ['123', '456'])
        self.assertEqual(url_path.with_end_tag, True)

    def test_parse_4(self):
        url_path = UrlPath()
        url_path.parse('/123/456/789', 'utf-8')
        self.assertEqual(url_path.segments, ['123', '456', '789'])
        self.assertEqual(url_path.with_end_tag, False)

    def test_parse_5(self):
        url_path = UrlPath()
        url_path.parse('/foo/bar', 'utf-8')
        self.assertEqual(url_path.segments, ['foo', 'bar'])
        self.assertEqual(url_path.with_end_tag, False)

    def test_parse_6(self):
        url_path = UrlPath()
        url_path.parse('', 'utf-8')
        self.assertEqual(url_path.segments, [])
        self.assertEqual(url_path.with_end_tag, False)

    def test_parse_7(self):
        url_path = UrlPath()
        url_path.parse('//', 'utf-8')
        self.assertEqual(url_path.segments, [])
        self.assertEqual(url_path.with_end_tag, True)

if __name__ == '__main__':
    unittest.main()
