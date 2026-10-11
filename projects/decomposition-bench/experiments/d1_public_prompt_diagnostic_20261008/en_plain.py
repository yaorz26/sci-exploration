def solve(payload):
    text = payload["text"]
    separator = payload.get("separator", ",")
    range_separator = payload.get("range_separator", "-")
    
    def parse_segment(segment):
        if range_separator in segment:
            start, end = segment.split(range_separator)
            start = int(start.strip())
            end = int(end.strip())
            if start <= end:
                return list(range(start, end + 1))
            else:
                return list(range(start, end - 1, -1))
        else:
            return [int(segment.strip())]
    
    segments = text.split(separator)
    numbers = []
    
    for segment in segments:
        segment = segment.strip()
        if segment:
            numbers.extend(parse_segment(segment))
    
    return sorted(numbers)

# Example usage:
payload = {"text": "1,3-5,3"}
print(solve(payload))  # Output: [1, 3, 3, 4, 5]

payload = {"text": "9:7;2", "separator": ";", "range_separator": ":"}
print(solve(payload))  # Output: [2, 7, 8, 9]
