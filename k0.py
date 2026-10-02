#!/usr/bin/env python3
"""Jembatan antrean perintah: baca D1 -> jalankan satu-kali -> tulis balik.
Hanya pustaka bawaan Python. Exit 0 = semua rapi (termasuk antrean kosong).
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

AKUN = os.environ.get("CF_ACCOUNT", "").strip()
TOKEN = os.environ.get("CF_TOKEN", "").strip()
DBID = os.environ.get("CF_DB_UUID", "").strip()
BASIS = "https://api.cloudflare.com/client/v4/accounts/%s/d1/database/%s/query" % (AKUN, DBID)
MAKS_PERINTAH = 2000
MAKS_HASIL = 8000
BATCH = 3
DETIK = 300

# --- bersihkan sisipan iklan hulu (tiruan persis buangSisipan panel) ---
import re
_TAK_NAMPAK = "[​‌‍⁠﻿­]"
_PETA = {"А": "A", "а": "a", "В": "B", "в": "b", "С": "C", "с": "c",
         "Е": "E", "е": "e", "Н": "H", "н": "h", "І": "I", "і": "i",
         "Ј": "J", "ј": "j", "К": "K", "к": "k", "М": "M", "м": "m",
         "О": "O", "о": "o", "Р": "P", "р": "p", "Ѕ": "S", "ѕ": "s",
         "Т": "T", "т": "t", "Х": "X", "х": "x", "ſ": "s"}
_KUAT = ["BANSOS", "BARISKA", "APIKEY", "SELLERNYA", "KONTOL2IN", "100%"]


def bersihkan(teks):
    """Buang sisipan iklan dari penyedia; kembalikan isi sah saja."""
    if not teks or not isinstance(teks, str):
        return teks
    t = re.sub(_TAK_NAMPAK, "", teks)
    u = "".join(_PETA.get(ch, ch) for ch in t.upper())
    kandidat = [m.start() for m in re.finditer(r"100\s*%[^\n]{0,70}?(?:BANSOS|APIKEY)", u)]
    kandidat += [m.start() for m in re.finditer(r"JUAL\s*APIKEY", u)]
    for pos in sorted(kandidat):
        dekat = u[pos:pos + 500]
        kuat = [k for k in _KUAT if k in dekat]
        if len(kuat) < 2:
            continue
        akhir = pos
        for k in kuat:
            i = dekat.rfind(k)
            if i >= 0:
                akhir = max(akhir, pos + i + len(k))
        awal = t.rfind("\n", 0, pos)
        awal = 0 if awal < 0 else awal + 1
        nl = t.find("\n", akhir)
        akhir = len(t) if nl < 0 else nl
        kiri = re.sub(r"^[=\s]{3,}", "", t[:awal].strip())
        kanan = re.sub(r"[=\s]{3,}$", "", t[akhir:].strip())
        kanan = kanan.lstrip("!. \t").strip()
        t = (kiri + "\n\n" + kanan) if (kiri and kanan) else (kiri or kanan)
        if not t.strip():
            return "(sisipan iklan dari penyedia dibuang; tidak ada isi lain)"
        return t
    return t
# -------------------------------------------------------------------


def q(sql, params=None):
    badan = json.dumps({"sql": sql, "params": params or []}).encode()
    permintaan = urllib.request.Request(
        BASIS, data=badan,
        headers={"Authorization": "Bearer " + TOKEN,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(permintaan, timeout=60) as r:
        balasan = json.loads(r.read())
    if not balasan.get("success"):
        raise RuntimeError("galat D1")
    return balasan["result"][0]["results"]


def cap_stempel():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def cari_hermes():
    lokasi = os.path.expanduser("~/.local/bin/hermes")
    if os.path.exists(lokasi):
        return lokasi
    return "hermes"


def kerjakan(perintah):
    if len(perintah) > MAKS_PERINTAH:
        return "DITOLAK: perintah terlalu panjang (maks %d karakter)" % MAKS_PERINTAH, "gagal"
    jalur = os.environ.get("PATH", "")
    if os.path.dirname(os.path.expanduser("~/.local/bin")) not in jalur:
        os.environ["PATH"] = jalur + ":" + os.path.expanduser("~/.local/bin")
    try:
        proses = subprocess.run(
            [cari_hermes(), "chat", "-q", perintah, "-Q"],
            capture_output=True, text=True, timeout=DETIK)
    except subprocess.TimeoutExpired:
        return "GAGAL: waktu habis %d detik" % DETIK, "gagal"
    keluar = bersihkan(((proses.stdout or "") + (proses.stderr or "")).strip())
    if proses.returncode == 0 and keluar:
        return keluar[:MAKS_HASIL], "selesai"
    return (("GAGAL exit %d: " % proses.returncode) + keluar)[:MAKS_HASIL], "gagal"


def main():
    if not (AKUN and TOKEN and DBID):
        print("KONFIG KURANG: CF_ACCOUNT/CF_TOKEN/CF_DB_UUID")
        return 2
    try:
        antri = q("SELECT id, perintah FROM agen_perintah "
                  "WHERE status='menunggu' ORDER BY id LIMIT %d" % BATCH)
    except Exception as e:
        print("GAGAL BACA ANTREAN: %s" % e)
        return 1
    if not antri:
        return 0  # antrean kosong: hening, tanpa suara
    for baris in antri:
        # klaim anti-bentrok: hanya baris 'menunggu' yang boleh berpindah
        klaim = q("UPDATE agen_perintah SET status='dikerjakan' "
                  "WHERE id=? AND status='menunggu' RETURNING id", [baris["id"]])
        if not klaim:
            continue
        hasil, status = kerjakan((baris.get("perintah") or "").strip())
        q("UPDATE agen_perintah SET status=?, hasil=?, selesai=? WHERE id=?",
          [status, hasil, cap_stempel(), baris["id"]])
        print("baris %s -> %s" % (baris["id"], status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
