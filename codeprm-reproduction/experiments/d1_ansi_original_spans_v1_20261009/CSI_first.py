def _short_spans(text):
    import re
    return [(match.start(), match.end()) for match in re.finditer(r"\x1b[@-Z\\-_]", text)]

def _csi_spans(text):
    import re
    return [(match.start(), match.end()) for match in re.finditer(r"\x1b\[[0-?]*[ -/]*[@-~]", text)]

def solve(payload):
    text = payload["text"]
    csi = _csi_spans(text)
    short = _short_spans(text)
    erased = [False] * len(text)
    for begin, end in csi + short:
        for position in range(begin, end):
            erased[position] = True
    return "".join(char for position, char in enumerate(text) if not erased[position])
