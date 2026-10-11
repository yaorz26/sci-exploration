def solve(payload):
    capacity = payload['capacity']
    instances = payload['instances']
    operations = payload['operations']
    
    instance_map = {instance['id']: {'bias': instance['bias'], 'cache': [], 'hits': 0, 'misses': 0} for instance in instances}
    computations = {instance['id']: 0 for instance in instances}
    sizes = {instance['id']: 0 for instance in instances}
    
    results = []
    
    for operation in operations:
        if operation['op'] == 'call':
            instance_id = operation['instance']
            x = operation['x']
            instance = instance_map[instance_id]
            
            if any(item['x'] == x for item in instance['cache']):
                # Hit
                instance['hits'] += 1
                result = instance['bias'] + x
            else:
                # Miss
                instance['misses'] += 1
                result = instance['bias'] + x
                computations[instance_id] += 1
                
                if len(instance['cache']) >= capacity:
                    # Evict the least recently used item
                    instance['cache'].pop(0)
                
                # Add the new item to the cache
                instance['cache'].append({'x': x, 'timestamp': len(instance['cache'])})
            
            sizes[instance_id] = len(instance['cache'])
            results.append({'result': result, 'computations': computations, 'sizes': sizes})
        
        elif operation['op'] == 'clear':
            instance_id = operation['instance']
            instance_map[instance_id]['cache'] = []
            sizes[instance_id] = 0
            results.append({'result': None, 'computations': computations, 'sizes': sizes})
    
    return results
