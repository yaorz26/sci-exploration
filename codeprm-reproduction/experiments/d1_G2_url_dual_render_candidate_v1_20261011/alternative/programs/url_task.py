"""另一种合法组织：不依赖 urllib.parse，自己按 RFC 3986 附录 B 的形态做正则拆分；
渲染时先构造“组件→文本”部件表，再统一引用，最后拼接。公开行为与参考实现一致。
"""

import re

_URL_RE = re.compile(
    r'^(?:(?P<scheme>[^:/?#]+):)?'
    r'(?:(?P<_sep>//)(?P<authority>[^/?#]*))?'
    r'(?P<path>[^?#]*)'
    r'(?:\?(?P<query>[^#]*))?'
    r'(?:#(?P<fragment>.*))?$'
)

_UNRESERVED = set('~-._0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
_SUBDELIMS = set("!$&'()*+,;=")
_MINIMAL_EXTRA = set(':@/? %')        # 面向显示：允许空格原样
_FULL_EXTRA = set(':@/?%')            # 面向发送：不保留空格


def _quote(text, extra_safe):
    """按 extra_safe 引用；'%' 在 safe 中即不重复编码已有 %XX；空格仅在 safe 含空格时保留。"""
    out = []
    for ch in text:
        if ch in _UNRESERVED or ch in _SUBDELIMS or ch in extra_safe:
            out.append(ch)
        else:
            for byte in ch.encode('utf-8'):
                out.append('%%%02X' % byte)
    return ''.join(out)


def _split(url):
    m = _URL_RE.match(url)
    return m.groupdict() if m else {'scheme': None, '_sep': None, 'authority': None,
                                    'path': '', 'query': None, 'fragment': None}


class URL:
    def __init__(self, url=''):
        parts = _split(url)
        self._parts = parts

    def to_text(self, full_quote=False):
        p = self._parts
        extra = _FULL_EXTRA if full_quote else _MINIMAL_EXTRA
        chunks = []
        if p['scheme']:
            chunks.append(p['scheme'])
            chunks.append('://' if p['_sep'] else ':')
        if p['authority'] is not None:
            chunks.append(p['authority'])
        chunks.append(_quote(p['path'] or '', extra))
        if p['query'] is not None:
            chunks.append('?' + _quote(p['query'], extra))
        if p['fragment'] is not None:
            chunks.append('#' + _quote(p['fragment'], extra))
        return ''.join(chunks)


class QueryView:
    def __init__(self, query_raw):
        self._raw = query_raw or ''

    def _pairs(self):
        pairs = []
        for part in self._raw.split('&'):
            if not part:
                continue
            key, sep, value = part.partition('=')
            pairs.append((key, value if sep else ''))
        return pairs

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
    return QueryView(_split(url)['query'])
