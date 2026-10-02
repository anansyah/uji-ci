import json, urllib.request, time

akun = open('/root/.hermes/secrets/cf_account.txt').read().strip()
kunci = open('/root/.hermes/secrets/cf_token.txt').read().strip()
uuid = "1203827f-97a1-4602-bb73-bd9083926a45"
BASIS = "https://api.cloudflare.com/client/v4/accounts/" + akun + "/d1/database/" + uuid + "/query"

def d1(sql, params=None):
    badan = json.dumps({"sql": sql, "params": params or []}).encode()
    req = urllib.request.Request(BASIS, data=badan, headers={
        "Authorization": "Bearer " + kunci, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["result"][0]["results"]

for i in range(4):
    baris = d1("SELECT id, status, coba, substr(coalesce(hasil,''),1,120) AS h, selesai FROM agen_perintah WHERE id = 6")
    if baris and baris[0]["status"] in ("selesai", "gagal"):
        print(json.dumps(baris[0], ensure_ascii=False))
        break
    print("menunggu... (cek ke-%d)" % (i + 1))
    time.sleep(45)
else:
    print("BELUM SELESAI: " + json.dumps(baris, ensure_ascii=False))
