import contextlib, importlib.util, io, json, sys, traceback
from pathlib import Path
root = Path(sys.argv[1]).resolve()
evaluator, candidate, cases = map(Path, sys.argv[2:5])
output = io.StringIO()
error = None
try:
    spec = importlib.util.spec_from_file_location("portable_evaluator", evaluator)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.argv = [str(evaluator), "--candidate", str(candidate), "--cases", str(cases)]
    with contextlib.redirect_stdout(output): module.main()
    result = json.loads(output.getvalue())
except Exception:
    error = traceback.format_exc()
    result = None
loaded = {name: str(Path(m.__file__).resolve()) for name, m in list(sys.modules.items()) if getattr(m, "__file__", None)}
print(json.dumps({"evaluation": result, "error": error, "loaded_files": loaded, "sys_path": sys.path, "isolated": sys.flags.isolated, "no_site": sys.flags.no_site}, ensure_ascii=False))
