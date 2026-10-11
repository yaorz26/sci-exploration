def _transform(node, factor, drop_null):
    if isinstance(node, dict):
        return {k: _transform(v, factor, drop_null) for k,v in node.items() if not (drop_null and v is None)}
    if isinstance(node, list):
        return [_transform(v, factor, drop_null) for v in node if not (drop_null and v is None)]
    return node*factor if type(node) in (int,float) else node

def _select(tree, threshold):
    result=[]
    def visit(node, path):
        if type(node) in (int,float) and node>=threshold: result.append({'path':path,'value':node})
        elif isinstance(node,dict):
            for key,value in node.items(): visit(value,path+[key])
        elif isinstance(node,list):
            for i,value in enumerate(node): visit(value,path+[i])
    visit(tree,[])
    return result
def solve(p):
    tree=_transform(p['tree'],p.get('factor',1),p.get('drop_null',False))
    matches=_select(tree,p['threshold'])
    return {'tree':tree,'matches':matches}
