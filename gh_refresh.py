import subprocess
import time
from pathlib import Path

GH = r"C:\Program Files\GitHub CLI\gh.exe"
ROOT = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm")
OUT = ROOT / "gh-out.txt"
ERR = ROOT / "gh-err.txt"

for p in (OUT, ERR):
    if p.exists():
        p.unlink()

out_f = open(OUT, "w", encoding="utf-8", errors="replace")
err_f = open(ERR, "w", encoding="utf-8", errors="replace")

proc = subprocess.Popen(
    [GH, "auth", "refresh", "-h", "github.com", "-s", "workflow"],
    stdout=out_f,
    stderr=err_f,
    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
)
time.sleep(6)
out_f.flush()
err_f.flush()
print("ALIVE", proc.poll() is None, flush=True)
print("PID", proc.pid, flush=True)
print("---OUT---", flush=True)
print(OUT.read_text(encoding="utf-8", errors="replace"), flush=True)
print("---ERR---", flush=True)
print(ERR.read_text(encoding="utf-8", errors="replace"), flush=True)
