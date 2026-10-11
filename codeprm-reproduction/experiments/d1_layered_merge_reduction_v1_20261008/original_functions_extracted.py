def layers_reference(p):
    import confuse
    import copy
    view = confuse.RootView([confuse.ConfigSource(source) for source in p['sources']])
    return copy.deepcopy(dict(view.flatten()))

def layers_alternate(p):
    import copy

    def combine(values):
        if not all((isinstance(value, dict) for value in values)):
            return copy.deepcopy(values[0])
        keys = dict.fromkeys((key for value in values for key in value))
        return {key: combine([value[key] for value in values if key in value]) for key in keys}
    return combine(p['sources'])
