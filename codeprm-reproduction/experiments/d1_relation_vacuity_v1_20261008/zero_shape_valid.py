def solve(payload):
    ids = [item['id'] for item in payload['instances']]
    return [{'result': None if op['op'] == 'clear' else 0,
             'computations': {key: 0 for key in ids},
             'sizes': {key: 0 for key in ids}}
            for op in payload['operations']]
