from collections import OrderedDict

def ansi_alternate(p):
    text, out, i = p["text"], [], 0
    while i < len(text):
        end = None
        if text[i] == "\x1b" and i + 1 < len(text):
            char = text[i+1]
            if "@" <= char <= "Z" or "\\" <= char <= "_":
                end = i + 2
            elif char == "[":
                j = i + 2
                while j < len(text) and "0" <= text[j] <= "?":
                    j += 1
                while j < len(text) and " " <= text[j] <= "/":
                    j += 1
                if j < len(text) and "@" <= text[j] <= "~":
                    end = j + 1
        if end is None:
            out.append(text[i] if text[i] != "\x1b" else ""); i += 1
        else:
            i = end
    return "".join(out)


def solve(payload):
    return ansi_alternate(payload)
