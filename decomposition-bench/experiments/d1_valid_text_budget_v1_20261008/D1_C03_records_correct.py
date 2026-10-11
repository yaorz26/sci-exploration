def solve(payload):
    records=[];count=0;output=[]
    for op in payload['operations']:
        if op['op']=='clear':records=[];value=None
        else:
            key=(tuple(op.get('args',[])),tuple(sorted(op.get('kwargs',{}).items())))
            matches=[i for i,r in enumerate(records) if r[0]==key]
            if matches:
                pair=records.pop(matches[0]);value=pair[1];records.append(pair)
            else:
                count+=1;value=sum(op.get('args',[]))+sum(op.get('kwargs',{}).values())
                if payload['capacity']>0:
                    records.append((key,value));records=records[-payload['capacity']:]
        output.append({'result':value,'computations':count,'size':len(records)})
    return output
