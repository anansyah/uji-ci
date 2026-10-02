import json, urllib.request, time, subprocess, os

# --- 1) push ---
tok = open('/root/.hermes/github_token.txt').read().strip()
env = dict(os.environ); env["GH_TOKEN"] = tok
p = subprocess.run(
    "cd /root/tmp/uji-ci && git add -A && git -c user.name=anansyah -c user.email=noreply@github.com commit -qm 'rantai cadangan' && "
    "git -c credential.helper='!f() { echo username=x-access-token; echo password=\"$GH_TOKEN\"; }; f' push -q origin master",
    shell=True, env=env, capture_output=True, text=True)
print("push:", "OK" if p.returncode == 0 else p.stderr[:200])

# --- 2) tanam baris uji ---
akun = open('/root/.hermes/secrets/cf_account.txt').read().strip()
kunci = open('/root/.hermes/secrets/cf_token.txt').read().strip()
uuid = "1203827f-97a1-4602-bb73-bd9083926a45"
BASIS = "https://api.cloudflare.com/client/v4/accounts/" + akun + "/d1/database/" + uuid + "/query"

def d1(sql, params=None):
    badan = json.dumps({"sql": sql, "params": params or []}).encode()
    req = urllib.request.Request(BASIS, data=badan, headers={"Authorization": "Bearer " + kunci, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["result"][0]["results"]

r = d1("INSERT INTO agen_perintah (perintah, status) VALUES (?, 'menunggu') RETURNING id",
       ["Balas satu kata saja: lulus"])
print("baris baru:", r[0]["id"])

# --- 3) nyalakan pelaksana sekarang juga ---
p = subprocess.run("python3 /root/.hermes/scripts/agen_dispatch.py", capture_output=True, text=True)
print("penjemput:", (p.stdout + p.stderr).strip() or "(hening)")

# --- 4) pantau sampai selesai ---
for i in range(8):
    time.sleep(40)
    b = d1("SELECT id, status, substr(coalesce(hasil,''),1,150) AS h, selesai FROM agen_perintah WHERE id = %d" % r[0]["id"])[0]
    if b["status"] in ("selesai", "gagal"):
        print("HASIL:", json.dumps(b, ensure_ascii=False))
        break
    print("menunggu... (%d)" % (i + 1))
else:
    print("BELUM SELESAI:", json.dumps(b, ensure_ascii=False))
