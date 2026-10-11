"""功能遗漏控制：与参考实现只差一处——渲染时不区分最小/完全引用，直接把各组件原样拼接
（放弃“按用途编码空格与不适用保留字符”的义务），但解析、映射视图与已编码文本保持不变。
"""

from urllib.parse import urlsplit


class URL:
    def __init__(self, url=''):
        parts = urlsplit(url)
        self.scheme = parts.scheme
        self.netloc = parts.netloc
        self.path_raw = parts.path
        self.query_raw = parts.query
        self.fragment_raw = parts.fragment

    def to_text(self, full_quote=False):
        # 控制点：忽略 full_quote，组件原样拼接
        text = ''
        if self.scheme:
            text += self.scheme + '://' if self.netloc else self.scheme + ':'
        text += self.netloc
        text += self.path_raw
        if self.query_raw:
            text += '?' + self.query_raw
        if self.fragment_raw:
            text += '#' + self.fragment_raw
        return text


class QueryView:
    def __init__(self, query_raw):
        self._raw = query_raw

    def _pairs(self):
        if not self._raw:
            return []
        out = []
        for part in self._raw.split('&'):
            if not part:
                continue
            key, _, value = part.partition('=')
            out.append((key, value))
        return out

    def keys(self):
        return [k for k, _ in self._pairs()]

    def items(self):
        return list(self._pairs())

    def get(self, key, default=None):
        for k, v in self._pairs():
            if k == key:
                return v
        return default

    def getlist(self, key):
        return [v for k, v in self._pairs() if k == key]


def url_view(url=''):
    return QueryView(urlsplit(url).query)
