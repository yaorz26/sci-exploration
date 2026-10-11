from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
CASE_SCRIPT = ROOT / "_run_one_real_feature_case.py"
CASE_SCRIPT.write_text(r'''from pathlib import Path
import json
import os
import sys
import tempfile

label = sys.argv[1]
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / label))
import confuse

app = Path(tempfile.mkdtemp(prefix="d1_confuse_app_")).resolve()
srcdir = app / "project" / "conf"
srcdir.mkdir(parents=True)
src = (srcdir / "local.yaml").resolve()
src.write_text("path: assets/a.txt\n", encoding="utf-8")
os.environ["D1APPDIR"] = str(app)
cases = []

def run(name, source_kwargs, template_kwargs):
    c = confuse.Configuration("d1app", read=False)
    try:
        source = confuse.ConfigSource({"path": "assets/a.txt"}, filename=str(src), **source_kwargs)
        c.add(source)
        out = c["path"].get(confuse.Filename(**template_kwargs))
        cases.append({"name":name,"status":"ok","resolved":out,"expected_source":str(srcdir / "assets" / "a.txt"),"expected_app":str(app / "assets" / "a.txt")})
    except Exception as exc:
        cases.append({"name":name,"status":"error","type":type(exc).__name__,"message":str(exc)})

run("default_source", {}, {})
run("source_flag", {"base_for_paths": True}, {})
run("template_source", {}, {"in_source_dir": True})
run("source_flag_app_override", {"base_for_paths": True}, {"in_app_dir": True})

c = confuse.Configuration("d1app", read=False)
kwargs = {"base_for_paths": True} if label == "merge" else {}
c.add(confuse.ConfigSource({"path": str(app / "abs" / "x")}, filename=str(src), **kwargs))
cases.append({"name":"absolute_path","status":"ok","resolved":c["path"].get(confuse.Filename())})

c = confuse.Configuration("d1app", read=False)
try:
    c.set_file(str(src), base_for_paths=True)
    cases.append({"name":"set_file_flag","status":"ok","resolved":c["path"].get(confuse.Filename())})
except Exception as exc:
    cases.append({"name":"set_file_flag","status":"error","type":type(exc).__name__,"message":str(exc)})

print(json.dumps({"label":label,"app_dir":str(app),"source_file":str(src),"cases":cases},ensure_ascii=False))
''', encoding='utf-8')
results = []
for label in ("parent", "merge"):
    proc = subprocess.run([sys.executable, "-B", str(CASE_SCRIPT), label], cwd=str(ROOT.parents[4]), capture_output=True, text=True, encoding="utf-8", timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"{label} failed: {proc.stderr}")
    results.append(json.loads(proc.stdout))
(ROOT / "real_feature_diagnostics.json").write_text(json.dumps({"results":results,"test_scope":"public source API only; no upstream tests; no hidden D1 data"},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(results,ensure_ascii=False,indent=2))
