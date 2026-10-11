def solve(payload):
    text = payload['text']
    result = []
    i = 0
    while i < len(text):
        if text[i] == '\x1b':  # ESC character
            if i + 1 < len(text) and text[i + 1] in '()#?':
                # Handle ANSI escape sequences
                i += 2
                while i < len(text) and text[i] in '0123456789;':
                    i += 1
                if i < len(text) and text[i] in 'ABCDEFGHJKSTf':
                    i += 1
                continue
            elif i + 1 < len(text) and text[i + 1] == '[':
                # Handle ANSI escape sequences
                i += 2
                while i < len(text) and text[i] in '0123456789;':
                    i += 1
                if i < len(text) and text[i] in '@ABCDEFGHIJKLMNOPQRSTUVWXYZ\\]^_`abcdefghijklmnopqrstuvwxyz':
                    i += 1
                    continue
        result.append(text[i])
        i += 1
    return ''.join(result)
