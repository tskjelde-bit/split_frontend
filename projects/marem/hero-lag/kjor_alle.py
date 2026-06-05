import subprocess, sys
JOBS = {
  "07-sofa": (0.300,0.56,0.725,0.87),
  "04-lampe-venstre": (0.115,0.46,0.245,0.88),
  "05-lampe-hoyre": (0.745,0.46,0.885,0.88),
  "06-lenestol": (0.885,0.64,1.000,0.95),
}
for name, bb in JOBS.items():
    args = [str(b) for b in bb]
    for model in ("birefnet-general", "isnet-general-use"):
        try:
            r = subprocess.run([sys.executable, "worker.py", name, model, *args],
                               timeout=180, capture_output=True, text=True)
            if "OK" in r.stdout:
                print(f"OK {name} ({model})", flush=True); break
            print(f"feil {name} ({model}): {r.stderr[-120:]}", flush=True)
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT {name} ({model})", flush=True)
print("done")
