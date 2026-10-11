def solve(payload) -> object:
    tree=_transform(payload['tree'],payload.get('factor',1),payload.get('drop_null',False))
    matches=_select(tree,payload['threshold'])
    return {'tree':tree,'matches':matches}
