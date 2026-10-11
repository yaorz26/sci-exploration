"""WP2 补充：WSL 可用性与网络实测（决定 EvoCodeBench 那条 Ubuntu+conda 路线是否可行）。

只做只读探测：列发行版、看 python/conda、看磁盘、测网络（直连 + 走 Windows 主机代理）。
不安装任何东西、不改配置。
"""
import subprocess

DISTRO = "Ubuntu-22.04"


def run(cmd, timeout=90):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", ""
    except Exception as e:
        return "ERR", "", f"{type(e).__name__}: {e}"


print("=== wsl -l -v ===")
rc, out, err = run(["wsl.exe", "-l", "-v"], timeout=60)
print("rc:", rc)
print(out.replace("\x00", ""))
if err:
    print("stderr:", err.replace("\x00", "")[:300])

probe = r"""
echo "--- python ---"; python3 -V 2>&1
echo "--- conda ---"; which conda || echo "no conda"
echo "--- pip ---"; python3 -m pip -V 2>&1 | head -1
echo "--- disk ---"; df -h / | tail -1; echo "--- home ---"; echo $HOME
echo "--- direct net (pypi) ---"; timeout 15 python3 - <<'EOF'
import urllib.request
try:
    print('pypi', urllib.request.urlopen('https://pypi.org/simple/', timeout=10).status)
except Exception as e:
    print('pypi FAIL', type(e).__name__, str(e)[:60])
try:
    print('hf', urllib.request.urlopen('https://huggingface.co', timeout=10).status)
except Exception as e:
    print('hf FAIL', type(e).__name__, str(e)[:60])
EOF
echo "--- proxied net (via Windows host 127.0.0.1:7890) ---"
timeout 15 env https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 python3 - <<'EOF'
import urllib.request
for u in ['https://huggingface.co', 'https://github.com']:
    try:
        print(u, urllib.request.urlopen(u, timeout=10).status)
    except Exception as e:
        print(u, 'FAIL', type(e).__name__, str(e)[:60])
EOF
"""

print("\n=== WSL 内部探测 ===")
rc, out, err = run(["wsl.exe", "-d", DISTRO, "--", "bash", "-lc", probe], timeout=180)
print("rc:", rc)
print(out.replace("\x00", ""))
if err:
    print("stderr:", err.replace("\x00", "")[:500])
