class URLHandler:
    def __init__(self, url):
        self.url = url

    def get_scheme(self):
        scheme_end = self.url.find("://")
        if scheme_end != -1:
            return self.url[:scheme_end]
        return None

    def get_host(self):
        scheme_end = self.url.find("://")
        if scheme_end != -1:
            url_without_scheme = self.url[scheme_end + 3:]
            host_end = url_without_scheme.find("/")
            if host_end != -1:
                return url_without_scheme[:host_end]
            return url_without_scheme
        return None

    def get_path(self):
        scheme_end = self.url.find("://")
        if scheme_end != -1:
            url_without_scheme = self.url[scheme_end + 3:]
            host_end = url_without_scheme.find("/")
            if host_end != -1:
                return url_without_scheme[host_end:]
        return None

    def get_query_params(self):
        query_start = self.url.find("?")
        fragment_start = self.url.find("#")
        if query_start != -1:
            query_string = self.url[query_start + 1:fragment_start]
            params = {}
            if len(query_string) > 0:
                param_pairs = query_string.split("&")
                for pair in param_pairs:
                    key_value = pair.split("=")
                    if len(key_value) == 2:
                        key, value = key_value
                        params[key] = value
            return params
        return None

    def get_fragment(self):
        fragment_start = self.url.find("#")
        if fragment_start != -1:
            return self.url[fragment_start + 1:]
        return None

import unittest


class URLHandlerTestGetScheme(unittest.TestCase):
    def test_get_scheme_1(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#page")
        temp = urlhandler.get_scheme()
        self.assertEqual(temp, "https")

    def test_get_scheme_2(self):
        urlhandler = URLHandler(
            "https://www.bing.com/search?pglt=41&q=humaneval&cvid=4dc2da2bb4bc429eb498c85245ae5253&aqs=edge.0.0l7j69i61j69i60.10008j0j1&FORM=ANNTA1&PC=U531&mkt=zh-CN")
        temp = urlhandler.get_scheme()
        self.assertEqual(temp, "https")

    def test_get_scheme_3(self):
        urlhandler = URLHandler("https://github.com/openai/human-eval")
        temp = urlhandler.get_scheme()
        self.assertEqual(temp, "https")

    def test_get_scheme_4(self):
        urlhandler = URLHandler("aaa://github.com/openai/human-eval")
        temp = urlhandler.get_scheme()
        self.assertEqual(temp, "aaa")

    def test_get_scheme_5(self):
        urlhandler = URLHandler("bbb://github.com/openai/human-eval")
        temp = urlhandler.get_scheme()
        self.assertEqual(temp, "bbb")

    def test_get_scheme_6(self):
        urlhandler = URLHandler("abcdefg")
        temp = urlhandler.get_scheme()
        self.assertIsNone(temp)


class URLHandlerTestGetHost(unittest.TestCase):
    def test_get_host_1(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#page")
        temp = urlhandler.get_host()
        self.assertEqual(temp, "www.baidu.com")

    def test_get_host_2(self):
        urlhandler = URLHandler(
            "https://www.bing.com/search?pglt=41&q=humaneval&cvid=4dc2da2bb4bc429eb498c85245ae5253&aqs=edge.0.0l7j69i61j69i60.10008j0j1&FORM=ANNTA1&PC=U531&mkt=zh-CN")
        temp = urlhandler.get_host()
        self.assertEqual(temp, "www.bing.com")

    def test_get_host_3(self):
        urlhandler = URLHandler("https://github.com/openai/human-eval")
        temp = urlhandler.get_host()
        self.assertEqual(temp, "github.com")

    def test_get_host_4(self):
        urlhandler = URLHandler("https://aaa.com/openai/human-eval")
        temp = urlhandler.get_host()
        self.assertEqual(temp, "aaa.com")

    def test_get_host_5(self):
        urlhandler = URLHandler("https://bbb.com/openai/human-eval")
        temp = urlhandler.get_host()
        self.assertEqual(temp, "bbb.com")

    def test_get_host_6(self):
        urlhandler = URLHandler("abcdefg")
        temp = urlhandler.get_host()
        self.assertIsNone(temp)

    def test_get_host_7(self):
        urlhandler = URLHandler("https://bbb.com")
        temp = urlhandler.get_host()
        self.assertEqual(temp, "bbb.com")

    def test_get_host_8(self):
        urlhandler = URLHandler("https://bbb.com/")
        temp = urlhandler.get_host()
        self.assertEqual(temp, "bbb.com")


class URLHandlerTestGetPath(unittest.TestCase):
    def test_get_path_1(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#page")
        temp = urlhandler.get_path()
        self.assertEqual(temp, "/s?wd=aaa&rsv_spt=1#page")

    def test_get_path_2(self):
        urlhandler = URLHandler(
            "https://www.bing.com/search?pglt=41&q=humaneval&cvid=4dc2da2bb4bc429eb498c85245ae5253&aqs=edge.0.0l7j69i61j69i60.10008j0j1&FORM=ANNTA1&PC=U531&mkt=zh-CN")
        temp = urlhandler.get_path()
        self.assertEqual(temp,
                         "/search?pglt=41&q=humaneval&cvid=4dc2da2bb4bc429eb498c85245ae5253&aqs=edge.0.0l7j69i61j69i60.10008j0j1&FORM=ANNTA1&PC=U531&mkt=zh-CN")

    def test_get_path_3(self):
        urlhandler = URLHandler("https://github.com/openai/human-eval")
        temp = urlhandler.get_path()
        self.assertEqual(temp, "/openai/human-eval")

    def test_get_path_4(self):
        urlhandler = URLHandler("https://github.com/aaa/human-eval")
        temp = urlhandler.get_path()
        self.assertEqual(temp, "/aaa/human-eval")

    def test_get_path_5(self):
        urlhandler = URLHandler("https://github.com/bbb/human-eval")
        temp = urlhandler.get_path()
        self.assertEqual(temp, "/bbb/human-eval")

    def test_get_path_6(self):
        urlhandler = URLHandler("abcdefg")
        temp = urlhandler.get_path()
        self.assertIsNone(temp)


class URLHandlerTestGetQueryParams(unittest.TestCase):
    def test_get_query_params_1(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#page")
        temp = urlhandler.get_query_params()
        self.assertEqual(temp, {"wd": "aaa", "rsv_spt": "1"})

    def test_get_query_params_2(self):
        urlhandler = URLHandler(
            "https://www.bing.com/search?pglt=41&q=humaneval&cvid=4dc2da2bb4bc429eb498c85245ae5253&aqs=edge.0.0l7j69i61j69i60.10008j0j1&FORM=ANNTA1&PC=U531#")
        temp = urlhandler.get_query_params()
        self.assertEqual(temp, {"pglt": "41", "q": "humaneval", "cvid": "4dc2da2bb4bc429eb498c85245ae5253",
                                "aqs": "edge.0.0l7j69i61j69i60.10008j0j1", "FORM": "ANNTA1", "PC": "U531"})

    def test_get_query_params_3(self):
        urlhandler = URLHandler("https://github.com/openai/human-eval")
        temp = urlhandler.get_query_params()
        self.assertEqual(temp, None)

    def test_get_query_params_4(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=bbb&rsv_spt=1#page")
        temp = urlhandler.get_query_params()
        self.assertEqual(temp, {"wd": "bbb", "rsv_spt": "1"})

    def test_get_query_params_5(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=ccc&rsv_spt=1#page")
        temp = urlhandler.get_query_params()
        self.assertEqual(temp, {"wd": "ccc", "rsv_spt": "1"})

    def test_get_query_params_6(self):
        urlhandler = URLHandler("https://www.baidu.com/s?&#page")
        temp = urlhandler.get_query_params()
        self.assertEqual(temp, {})


class URLHandlerTestGetFragment(unittest.TestCase):
    def test_get_fragment_1(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#page")
        temp = urlhandler.get_fragment()
        self.assertEqual(temp, "page")

    def test_get_fragment_2(self):
        urlhandler = URLHandler(
            "https://www.bing.com/search?pglt=41&q=humaneval&cvid=4dc2da2bb4bc429eb498c85245ae5253&aqs=edge.0.0l7j69i61j69i60.10008j0j1&FORM=ANNTA1&PC=U531&mkt=zh-CN")
        temp = urlhandler.get_fragment()
        self.assertEqual(temp, None)

    def test_get_fragment_3(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#aaa")
        temp = urlhandler.get_fragment()
        self.assertEqual(temp, "aaa")

    def test_get_fragment_4(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#bbb")
        temp = urlhandler.get_fragment()
        self.assertEqual(temp, "bbb")

    def test_get_fragment_5(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#ccc")
        temp = urlhandler.get_fragment()
        self.assertEqual(temp, "ccc")


class URLHandlerTest(unittest.TestCase):
    def test_urlhandler(self):
        urlhandler = URLHandler("https://www.baidu.com/s?wd=aaa&rsv_spt=1#page")
        temp = urlhandler.get_scheme()
        self.assertEqual(temp, "https")
        temp = urlhandler.get_host()
        self.assertEqual(temp, "www.baidu.com")
        temp = urlhandler.get_path()
        self.assertEqual(temp, "/s?wd=aaa&rsv_spt=1#page")
        temp = urlhandler.get_query_params()
        self.assertEqual(temp, {"wd": "aaa", "rsv_spt": "1"})
        temp = urlhandler.get_fragment()
        self.assertEqual(temp, "page")

if __name__ == '__main__':
    unittest.main()
