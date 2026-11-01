import sys, os, subprocess
from concurrent.futures import ThreadPoolExecutor
tsv, outdir, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.makedirs(outdir, exist_ok=True)
rows = [l.split("\t") for l in open(tsv).read().splitlines()][:n]
def get(r):
    name, fid = r
    p = os.path.join(outdir, name)
    if os.path.exists(p) and os.path.getsize(p) > 1000: return True
    url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    for _ in range(3):
        try:
            data = subprocess.run(["curl", "-sL", "--max-time", "60", "--max-filesize", "5000000", url],
                                  capture_output=True).stdout
            if data[:4] == b"RIFF": open(p, "wb").write(data); return True
        except Exception: pass
    return False
with ThreadPoolExecutor(6) as ex: ok = list(ex.map(get, rows))
print(outdir.rsplit("/", 1)[1], f"{sum(ok)}/{len(rows)} downloaded")
