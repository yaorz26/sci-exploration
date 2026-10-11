def solve(payload):
    def parse_range(range_str, range_separator):
        start, end = range_str.split(range_separator)
        start, end = int(start), int(end)
        if start <= end:
            return list(range(start, end + 1))
        else:
            return list(range(start, end - 1, -1))

    def parse_segment(segment, range_separator):
        if range_separator in segment:
            return parse_range(segment, range_separator)
        else:
            return [int(segment)]

    def parse_text(text, separator, range_separator):
        segments = text.strip().split(separator)
        result = []
        for segment in segments:
            if segment:
                result.extend(parse_segment(segment, range_separator))
        return result

    text = payload.get('text')
    separator = payload.get('separator', ',')
    range_separator = payload.get('range_separator', '-')

    return parse_text(text, separator, range_separator)
