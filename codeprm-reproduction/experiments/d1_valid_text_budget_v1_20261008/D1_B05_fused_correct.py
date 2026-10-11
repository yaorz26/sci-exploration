def solve(payload):
    def walk(node,path):
        if isinstance(node,dict):
            new={}; matches=[]
            for k,v in node.items():
                if v is None and payload.get('drop_null',False): continue
                child,found=walk(v,path+[k]);new[k]=child;matches.extend(found)
            return new,matches
        if isinstance(node,list):
            kept=[v for v in node if not (v is None and payload.get('drop_null',False))]
            new=[];matches=[]
            for i,v in enumerate(kept):
                child,found=walk(v,path+[i]);new.append(child);matches.extend(found)
            return new,matches
        value=node*payload.get('factor',1) if type(node) in (int,float) else node
        return value,([{'path':path,'value':value}] if type(value) in (int,float) and value>=payload['threshold'] else [])
    tree,matches=walk(payload['tree'],[])
    return {'tree':tree,'matches':matches}
