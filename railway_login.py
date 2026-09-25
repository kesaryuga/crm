import subprocess
import time
from pathlib import Path

RAILWAY = r"C:\Users\Yury\AppData\Roaming\npm\railway.cmd"
ROOT = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm")
OUT = ROOT / "railway-login-out.txt"
ERR = ROOT / "railway-login-err.txt"

for p in (OUT, ERR):
    if p.exists():
        p.unlink()

of = open(OUT, "w", encoding="utf-8", errors="replace")
ef = open(ERR, "w", encoding="utf-8", errors="replace")

proc = subprocess.Popen(
    [RAILWAY, "login", "--browserless"],
    stdout=of,
    stderr=ef,
    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
)
time.sleep(8)
of.flush()
ef.flush()
print("ALIVE", proc.poll() is None, flush=True)
print("PID", proc.pid, flush=True)
print("---OUT---", flush=True)
print(OUT.read_text(encoding="utf-8", errors="replace"), flush=True)
print("---ERR---", flush=True)
print(ERR.read_text(encoding="utf-8", errors="replace"), flush=True)
