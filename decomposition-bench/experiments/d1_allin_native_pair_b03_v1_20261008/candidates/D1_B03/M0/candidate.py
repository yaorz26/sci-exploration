def solve(payload):
    text = payload.get("text", "")
    result = []
    i = 0
    while i < len(text):
        if text[i] == '\x1b':  # ESC character
            if i + 1 < len(text) and text[i + 1] == '[':
                # Handle ANSI escape sequence starting with ESC[
                j = i + 2
                while j < len(text) and text[j].isalnum() or text[j] in ' ;':
                    j += 1
                if j < len(text) and (text[j] >= '@' and text[j] <= '~'):
                    i = j
                else:
                    result.append(text[i])
            else:
                # Handle other ANSI escape sequences
                j = i + 1
                while j < len(text) and text[j].isalnum():
                    j += 1
                if j < len(text) and (text[j] >= '@' and text[j] <= '~'):
                    i = j
                else:
                    result.append(text[i])
        else:
            result.append(text[i])
        i += 1
    return ''.join(result)
