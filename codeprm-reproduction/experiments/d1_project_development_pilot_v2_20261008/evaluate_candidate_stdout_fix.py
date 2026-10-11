"""Evaluate one saved entry point against explicit JSON behavioral cases."""
import argparse
import contextlib
import copy
import importlib.util
import json
import sys
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--cases',type=Path,required=True)
    args=parser.parse_args()
    specification=importlib.util.spec_from_file_location('candidate',args.candidate)
    module=importlib.util.module_from_spec(specification)
    # Candidate prints are diagnostic data, not part of solve's return value.
    # Keep them in the bounded stderr stream, away from the JSON score channel.
    with contextlib.redirect_stdout(sys.stderr):
        specification.loader.exec_module(module)
    cases=json.loads(args.cases.read_text(encoding='utf-8'))
    results=[]
    for case in cases:
        payload=copy.deepcopy(case['input'])
        before=copy.deepcopy(payload)
        try:
            with contextlib.redirect_stdout(sys.stderr):
                actual={'value':module.solve(payload)}
            # Normalize tuples and ensure the result is serializable.
            actual=json.loads(json.dumps(actual,ensure_ascii=False,allow_nan=False))
        except Exception as exc:
            actual={'error':type(exc).__name__}
        passed=actual==case['expected'] and payload==before
        results.append({'case_id':case['case_id'],'pass':passed,'input_unchanged':payload==before,
                        'error':None if passed else {'expected':case['expected'],'actual':actual}})
    print(json.dumps({'cases':len(results),'passed':sum(row['pass'] for row in results),
                      'all_pass':all(row['pass'] for row in results),'results':results},ensure_ascii=False))

if __name__=='__main__':
    main()
