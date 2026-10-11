"""参考实现：完整组织。基于 urllib.parse 拆分/重组，两种渲染用途共用一次解析结果。

语义约定（见 requirement.md，2026-10-11 修正）：
  - 最小引用（to_text()）：面向显示，含空格的 safe 集合，违规字符（空格等）保持原样；
  - 完全引用（to_text(full_quote=True)）：面向发送，不含空格的 safe 集合，把空格等编码为 %XX；
  - 已存在的 %XX 序列在两种用途下都不重复编码（把 '%' 放进 safe 集合即可）；
  - 查询串中已有的 '+' 视为字面加号，不还原成空格。
"""

from urllib.parse import quote, urlsplit

_SAFE_DISPLAY = "!$&'()*+,-./:;=?@_~ %"   # 允许原样空格：面向显示
_SAFE_NETWORK = "!$&'()*+,-./:;=?@_~%"    # 不允许原样空格：面向发送


class URL:
    def __init__(self, url=''):
        parts = urlsplit(url)
        self.scheme = parts.scheme
        self.netloc = parts.netloc
        self.path_raw = parts.path
        self.query_raw = parts.query
        self.fragment_raw = parts.fragment

    def _render(self, full_quote=False):
        safe = _SAFE_NETWORK if full_quote else _SAFE_DISPLAY
        text = ''
        if self.scheme:
            text += self.scheme + '://' if self.netloc else self.scheme + ':'
        text += self.netloc
        text += quote(self.path_raw, safe=safe, encoding='utf-8')
        if self.query_raw:
            text += '?' + quote(self.query_raw, safe=safe, encoding='utf-8')
        if self.fragment_raw:
            text += '#' + quote(self.fragment_raw, safe=safe, encoding='utf-8')
        return text

    def to_text(self, full_quote=False):
        return self._render(full_quote=full_quote)


class QueryView:
    """同一份查询串的公开映射视图：不修改原串，只按需解析。"""

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
