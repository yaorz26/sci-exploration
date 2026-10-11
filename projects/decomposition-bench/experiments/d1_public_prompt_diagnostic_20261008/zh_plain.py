def solve(payload):
    text = payload['text']
    separator = payload.get('separator', ',')
    range_separator = payload.get('range_separator', '-')
    
    def parse_segment(segment):
        if range_separator in segment:
            start, end = segment.split(range_separator)
            start, end = int(start), int(end)
            if start <= end:
                return list(range(start, end + 1))
            else:
                return list(range(start, end - 1, -1))
        else:
            return [int(segment)]
    
    segments = text.strip().split(separator)
    result = []
    
    for segment in segments:
        if segment:
            try:
                result.extend(parse_segment(segment))
            except ValueError:
                raise ValueError(f"Invalid value in segment: {segment}")
    
    return result
