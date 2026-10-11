import urllib.parse
import unicodedata

def solve(payload):
    query = payload['query']
    operations = payload['operations']
    
    # Parse the query string
    pairs = []
    for segment in query.split('&') + query.split(';'):
        if segment:
            key, value = segment.split('=', 1) if '=' in segment else (segment, None)
            key = urllib.parse.unquote(key.replace('+', ' '))
            value = urllib.parse.unquote(value.replace('+', ' ')) if value is not None else None
            pairs.append([key, value])
    
    # Apply operations
    for operation in operations:
        if operation['op'] == 'add':
            pairs.append([operation['key'], operation['value']])
        elif operation['op'] == 'set':
            pairs = [pair for pair in pairs if pair[0] != operation['key']]
            pairs.append([operation['key'], operation['value']])
        elif operation['op'] == 'delete':
            pairs = [pair for pair in pairs if pair[0] != operation['key']]
    
    # Encode the pairs
    encoded_pairs = []
    for key, value in pairs:
        encoded_key = urllib.parse.quote(key, safe='~-._!$\'()*,;/:?@')
        encoded_value = urllib.parse.quote(value, safe='~-._!$\'()*,;/:?@') if value is not None else ''
        encoded_pairs.append([encoded_key, encoded_value])
    
    # Format the query string
    encoded_query = '&'.join(f'{key}={value}' if value is not None else key for key, value in encoded_pairs)
    
    return {
        'pairs': pairs,
        'query': encoded_query
    }
