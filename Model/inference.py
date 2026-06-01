"""
=============================================================
Model/inference.py
"Mata" AI Sistem ADAS — Inference YOLOv8 + Integrasi Logic
Kelompok 6 | Proyek Tugas Akhir
=============================================================

INSTRUKSI AKTIVASI DI UI/app.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LANGKAH 1 — Ganti blok impor dummy (baris 20-25) menjadi:

    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Model"))
    from inference import jalankan_deteksi, MODEL_YOLO

LANGKAH 2 — Hapus seluruh fungsi dummy_deteksi_frame() (baris 125-150).
            Tidak dibutuhkan lagi.

LANGKAH 3 — Deteksi Gambar (baris ~264-270):
    HAPUS baris:    time.sleep(0.8)
    HAPUS baris:    frame_out, deteksi, status, pesan = dummy_deteksi_frame(...)
    GANTI dengan:   frame_out, deteksi, status, pesan = jalankan_deteksi(
                        gambar_np, kecepatan_kmh=0
                    )
                    frame_out = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)

LANGKAH 4 — Proses Video (baris ~356-379), ganti seluruh isi
            if st.button("▶ Proses Video dengan AI") menjadi:

    tmp_path = "/tmp/adas_video.mp4"
    with open(tmp_path, "wb") as f:
        f.write(file_video.read())
    cap = cv2.VideoCapture(tmp_path)
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame_out, deteksi, status, pesan = jalankan_deteksi(frame, kecepatan_kmh)
        frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)
        placeholder_frame.image(frame_rgb, channels="RGB", use_container_width=True)
        with placeholder_notif_video.container():
            render_panel_notifikasi(status, pesan)
    cap.release()

LANGKAH 5 — Realtime Webcam (baris ~432):
    HAPUS:   frame_out, deteksi, status, pesan = dummy_deteksi_frame(frame_rgb, kecepatan_rt)
    GANTI:   frame_out, deteksi, status, pesan = jalankan_deteksi(frame, kecepatan_rt)
    CATATAN: Gunakan `frame` (BGR dari cv2.VideoCapture), bukan frame_rgb.
             Lalu tampilkan:
             frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)
             placeholder_cam.image(frame_rgb, channels="RGB", use_container_width=True)

=============================================================
"""

import os
import sys
import cv2
import numpy as np

# ── Tambahkan folder Logic/ ke sys.path agar bisa diimpor dari Model/ ──────
# Struktur yang diasumsikan:
#   project_root/
#     ├── Model/inference.py   ← file ini
#     ├── Logic/core_logic.py
#     └── UI/app.py
_ROOT_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGIC_DIR = os.path.join(_ROOT_DIR, "Logic")
sys.path.insert(0, _LOGIC_DIR)

from core_logic import evaluasi_batch, ambil_prioritas_tertinggi # type: ignore


# ==============================================================
# KONSTANTA VISUAL — Warna Bounding Box per Status
# Format warna: BGR (urutan OpenCV, bukan RGB)
# ==============================================================

WARNA_BBOX: dict = {
    "Pelanggaran": (0,   0,   255),   # Merah  — bahaya maksimal
    "Larangan"   : (0,   0,   220),   # Merah gelap — larangan
    "Peringatan" : (0,   255, 255),   # Kuning — waspadai
    "Info"       : (0,   255, 0  ),   # Hijau  — aman/informatif
    "Aman"       : (0,   255, 0  ),   # Hijau  — tidak ada masalah
}

# Tebal garis kotak bounding box (piksel)
TEBAL_BBOX    = 2

# Confidence minimum — deteksi di bawah nilai ini diabaikan
CONF_MIN      = 0.50

# Skala font teks label di atas bbox
SKALA_FONT    = 0.50

# Tebal teks label
TEBAL_FONT    = 1

# Padding dalam piksel antara teks dan tepi background label
PADDING_LABEL = 4


# ==============================================================
# INISIALISASI MODEL — Dimuat SEKALI saat modul pertama diimpor
# ── Pendekatan "module-level singleton" ──────────────────────
# Model tidak di-reload setiap frame — hanya sekali saat import.
# Di Streamlit, bungkus pemanggilan muat_model() dengan
# @st.cache_resource agar aman saat rerun.
# ==============================================================

MODEL_YOLO  = None   # objek YOLO aktif, None jika belum/gagal dimuat
_NAMA_MODEL = ""     # path model yang sedang dimuat (untuk logging)


def _inisialisasi_model(path_model=None):
    """
    Muat model YOLOv8 dari file .pt menggunakan ultralytics.

    Path dicari berurutan:
      1. Argumen path_model (jika eksplisit).
      2. Env var ADAS_MODEL_PATH.
      3. Default: <root>/Model/best.pt
      4. Fallback: best.pt di folder yang sama dengan inference.py
    """
    global MODEL_YOLO, _NAMA_MODEL

    kandidat = [
        path_model,
        os.environ.get("ADAS_MODEL_PATH"),
        os.path.join(_ROOT_DIR, "Model", "best.pt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "best.pt"),
    ]

    path_terpilih = None
    for p in kandidat:
        if p and os.path.isfile(p):
            path_terpilih = p
            break

    if path_terpilih is None:
        print("[inference.py] ⚠  best.pt tidak ditemukan. Letakkan di folder Model/ lalu restart.")
        return

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[inference.py] ⚠  ultralytics belum terinstal. Jalankan: pip install ultralytics")
        return

    try:
        MODEL_YOLO  = YOLO(path_terpilih)
        _NAMA_MODEL = path_terpilih
        n = len(MODEL_YOLO.names)
        print(f"[inference.py] ✅ Model dimuat  : {path_terpilih}")
        print(f"[inference.py]    Jumlah kelas  : {n}")
        print(f"[inference.py]    Kelas[0..2]   : {list(MODEL_YOLO.names.values())[:3]} …")
    except Exception as exc:
        print(f"[inference.py] ❌ Gagal memuat model: {exc}")
        MODEL_YOLO = None


# Panggil otomatis saat modul di-import
_inisialisasi_model()


# ==============================================================
# HELPER INTERNAL — Gambar satu bounding box + label ke frame
# ==============================================================

def _gambar_satu_bbox(frame, bbox, nama_kelas, confidence, jarak_meter, warna_bgr):
    """
    Gambar kotak pembatas + label nama kelas, confidence, dan jarak
    ke frame secara in-place (tidak ada return value).

    Susunan label (dari bawah ke atas kotak):
        - Baris 1: "NamaKelas  93%"
        - Baris 2: "~12.5 m"  (jika jarak tersedia)
    """
    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

    # 1. Kotak pembatas
    cv2.rectangle(frame, (x1, y1), (x2, y2), warna_bgr, TEBAL_BBOX)

    # 2. Tentukan warna teks — hitam di background kuning, putih lainnya
    r, g, b   = warna_bgr[2], warna_bgr[1], warna_bgr[0]  # BGR → RGB
    luminansi = 0.299 * r + 0.587 * g + 0.114 * b
    warna_teks = (0, 0, 0) if luminansi > 160 else (255, 255, 255)

    # 3. Label baris utama: "NamaKelas  93%"
    nama_pendek = nama_kelas if len(nama_kelas) <= 24 else nama_kelas[:22] + ".."
    teks_utama  = f"{nama_pendek}  {confidence * 100:.0f}%"

    (lebar_u, tinggi_u), baseline_u = cv2.getTextSize(
        teks_utama, cv2.FONT_HERSHEY_SIMPLEX, SKALA_FONT, TEBAL_FONT
    )

    # Posisi background: tepat di atas garis atas kotak
    bg_y2 = y1
    bg_y1 = bg_y2 - tinggi_u - PADDING_LABEL * 2

    # Jika melewati tepi atas frame, pindahkan ke bawah kotak
    if bg_y1 < 0:
        bg_y1 = y2
        bg_y2 = y2 + tinggi_u + PADDING_LABEL * 2

    cv2.rectangle(frame, (x1, bg_y1),
                  (x1 + lebar_u + PADDING_LABEL * 2, bg_y2), warna_bgr, cv2.FILLED)
    cv2.putText(frame, teks_utama, (x1 + PADDING_LABEL, bg_y2 - PADDING_LABEL),
                cv2.FONT_HERSHEY_SIMPLEX, SKALA_FONT, warna_teks, TEBAL_FONT, cv2.LINE_AA)

    # 4. Label baris jarak (opsional)
    if jarak_meter is not None:
        teks_jarak = f"~{jarak_meter:.1f} m"
        (lebar_j, tinggi_j), _ = cv2.getTextSize(
            teks_jarak, cv2.FONT_HERSHEY_SIMPLEX, SKALA_FONT - 0.07, TEBAL_FONT
        )
        jbg_y2 = bg_y1
        jbg_y1 = jbg_y2 - tinggi_j - PADDING_LABEL * 2

        if jbg_y1 >= 0:
            cv2.rectangle(frame, (x1, jbg_y1),
                          (x1 + lebar_j + PADDING_LABEL * 2, jbg_y2), warna_bgr, cv2.FILLED)
            cv2.putText(frame, teks_jarak, (x1 + PADDING_LABEL, jbg_y2 - PADDING_LABEL),
                        cv2.FONT_HERSHEY_SIMPLEX, SKALA_FONT - 0.07,
                        warna_teks, TEBAL_FONT, cv2.LINE_AA)


# ==============================================================
# HELPER INTERNAL — HUD overlay pojok kiri atas
# ==============================================================

def _gambar_hud(frame, status_global, jumlah_deteksi, kecepatan_kmh):
    """
    Overlay HUD semi-transparan: status | jumlah deteksi | kecepatan.
    Dimodifikasi in-place.
    """
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (230, 72), (13, 17, 23), cv2.FILLED)
    cv2.addWeighted(overlay, 0.60, frame, 0.40, 0, frame)

    warna = WARNA_BBOX.get(status_global, WARNA_BBOX["Aman"])
    cv2.putText(frame, f"STATUS : {status_global.upper()}",
                (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, warna, 1, cv2.LINE_AA)
    cv2.putText(frame, f"DETEKSI: {jumlah_deteksi} objek",
                (8, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (190, 190, 190), 1, cv2.LINE_AA)
    cv2.putText(frame, f"SPEED  : {kecepatan_kmh:.0f} km/h",
                (8, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (190, 190, 190), 1, cv2.LINE_AA)


# ==============================================================
# FUNGSI UTAMA — jalankan_deteksi()
# ==============================================================

def jalankan_deteksi(frame, kecepatan_kmh=0.0):
    """
    Proses satu frame melalui pipeline YOLO + rule engine ADAS.

    Pipeline:
        frame
          → YOLOv8 predict (conf ≥ 0.50)
          → ekstrak bbox, class_id, confidence
          → dynamic class mapping: model.names[class_id]   ← plug-and-play
          → evaluasi_batch()        → status & jarak per objek
          → ambil_prioritas_tertinggi() → status & pesan paling kritis
          → gambar bbox berwarna + label + HUD overlay
          → return tuple 4 elemen

    Args:
        frame (np.ndarray) : Frame BGR dari cv2.VideoCapture,
                             ATAU frame RGB dari PIL/Streamlit.
                             Konversi warna dideteksi otomatis.
        kecepatan_kmh (float): Kecepatan kendaraan dari st.slider.

    Returns:
        frame_hasil (np.ndarray BGR) : Frame + bounding box + HUD.
                                       Untuk Streamlit: konversi dulu
                                       cv2.cvtColor(..., COLOR_BGR2RGB)
        deteksi_list (list[dict])    : Raw deteksi YOLO.
        status_final (str)           : Status urgensi tertinggi.
        pesan_final  (str)           : Pesan notifikasi paling kritis.
    """
    STATUS_DEFAULT = "Aman"
    PESAN_DEFAULT  = "Tidak ada rambu terdeteksi dalam frame ini."

    deteksi_list = []
    status_final = STATUS_DEFAULT
    pesan_final  = PESAN_DEFAULT

    # Salin agar frame asli tidak termutasi
    frame_hasil  = frame.copy()
    tinggi_frame = frame_hasil.shape[0]

    # Guard: model belum dimuat
    if MODEL_YOLO is None:
        cv2.putText(frame_hasil,
                    "MODEL BELUM DIMUAT — periksa Model/best.pt",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2, cv2.LINE_AA)
        return frame_hasil, deteksi_list, "Aman", "Model YOLOv8 belum berhasil dimuat."

    # Normalisasi BGR: Streamlit memberikan RGB, cv2 butuh BGR untuk predict
    frame_bgr = cv2.cvtColor(frame_hasil, cv2.COLOR_RGB2BGR) \
                if _adalah_rgb(frame_hasil) else frame_hasil

    # Jalankan YOLO predict
    try:
        hasil_yolo = MODEL_YOLO.predict(source=frame_bgr, conf=CONF_MIN, verbose=False)
    except Exception as exc:
        print(f"[inference.py] ❌ Predict gagal: {exc}")
        return frame_hasil, deteksi_list, STATUS_DEFAULT, PESAN_DEFAULT

    if not hasil_yolo:
        return frame_hasil, deteksi_list, STATUS_DEFAULT, PESAN_DEFAULT

    result = hasil_yolo[0]

    if result.boxes is None or len(result.boxes) == 0:
        _gambar_hud(frame_hasil, STATUS_DEFAULT, 0, kecepatan_kmh)
        return frame_hasil, deteksi_list, STATUS_DEFAULT, PESAN_DEFAULT

    # ── Ekstrak setiap deteksi ───────────────────────────────────────────────
    for box in result.boxes:
        koordinat  = box.xyxy[0].tolist()
        class_id   = int(box.cls[0].item())
        confidence = float(box.conf[0].item())

        # DYNAMIC CLASS MAPPING — tidak ada hardcode nama kelas di sini
        nama_kelas = MODEL_YOLO.names.get(class_id, f"kelas_{class_id}")

        deteksi_list.append({
            "class_name" : nama_kelas,
            "bbox"       : [round(v, 1) for v in koordinat],
            "confidence" : round(confidence, 3),
        })

    # ── Kirim ke rule engine ─────────────────────────────────────────────────
    semua_hasil = evaluasi_batch(
        deteksi_list        = deteksi_list,
        frame_height        = float(tinggi_frame),
        kecepatan_kendaraan = kecepatan_kmh,
    )

    hasil_prioritas = ambil_prioritas_tertinggi(
        deteksi_list        = deteksi_list,
        frame_height        = float(tinggi_frame),
        kecepatan_kendaraan = kecepatan_kmh,
    )

    if hasil_prioritas:
        status_final = hasil_prioritas.status
        pesan_final  = hasil_prioritas.pesan

    # Peta nama → hasil evaluasi untuk lookup O(1)
    peta_hasil = {h.nama_kelas: h for h in reversed(semua_hasil)}

    # ── Gambar bounding box ──────────────────────────────────────────────────
    for det in deteksi_list:
        nama       = det["class_name"]
        bbox       = det["bbox"]
        conf       = det["confidence"]
        hasil_eval = peta_hasil.get(nama)
        status_obj = hasil_eval.status      if hasil_eval else "Info"
        jarak_m    = hasil_eval.jarak_meter if hasil_eval else None
        warna      = WARNA_BBOX.get(status_obj, WARNA_BBOX["Info"])

        _gambar_satu_bbox(frame_hasil, bbox, nama, conf, jarak_m, warna)

    # ── HUD overlay ──────────────────────────────────────────────────────────
    _gambar_hud(frame_hasil, status_final, len(deteksi_list), kecepatan_kmh)

    return frame_hasil, deteksi_list, status_final, pesan_final


# ==============================================================
# HELPER — Deteksi format RGB vs BGR (heuristik)
# ==============================================================

def _adalah_rgb(frame):
    """
    Heuristik: gambar alam nyata umumnya lebih merah dari biru.
    Jika channel-0 secara konsisten lebih terang dari channel-2,
    kemungkinan besar array ini adalah RGB (bukan BGR).
    """
    if frame.ndim != 3 or frame.shape[2] != 3:
        return False
    return float(frame[:, :, 0].mean()) > float(frame[:, :, 2].mean()) * 1.05


# ==============================================================
# BLOK PENGUJIAN MANDIRI
# Jalankan: python Model/inference.py
# Dengan gambar: python Model/inference.py --gambar foto.jpg --kecepatan 95
# ==============================================================

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Uji inference.py standalone")
    ap.add_argument("--gambar",    type=str,   default=None,
                    help="Path gambar uji. Kosong = frame dummy.")
    ap.add_argument("--kecepatan", type=float, default=85.0,
                    help="Kecepatan simulasi km/jam (default: 85).")
    ap.add_argument("--simpan",    type=str,   default="output_test.jpg",
                    help="Nama file output (default: output_test.jpg).")
    args = ap.parse_args()

    SEP = "=" * 65
    print(SEP)
    print("  SMART ADAS — Uji Mandiri inference.py")
    print(SEP)

    if MODEL_YOLO is not None:
        print(f"\n✅ Model aktif   : {_NAMA_MODEL}")
        print(f"   Jumlah kelas  : {len(MODEL_YOLO.names)}")
    else:
        print("\n⚠  Model TIDAK aktif — pastikan best.pt ada di Model/")

    if args.gambar and os.path.isfile(args.gambar):
        print(f"\n📷 Memuat gambar : {args.gambar}")
        frame_uji = cv2.imread(args.gambar)
    else:
        print("\n📷 Gambar tidak ditemukan — membuat frame dummy 720p …")
        frame_uji = np.full((720, 1280, 3), 25, dtype=np.uint8)
        cv2.putText(frame_uji, "FRAME DUMMY — Smart ADAS Kelompok 6",
                    (180, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 229, 255), 2, cv2.LINE_AA)

    print(f"\n🔍 Menjalankan deteksi | kecepatan = {args.kecepatan} km/jam …")
    frame_out, deteksi, status, pesan = jalankan_deteksi(frame_uji, args.kecepatan)

    print(f"\n   Jumlah deteksi   : {len(deteksi)}")
    print(f"   Status prioritas : {status}")
    print(f"   Pesan            : {pesan}")

    if deteksi:
        print("\n   Detail tiap objek:")
        for i, d in enumerate(deteksi, 1):
            print(f"     [{i}] {d['class_name']:<35s} "
                  f"conf={d['confidence']:.2f}  "
                  f"bbox={[round(v) for v in d['bbox']]}")

    cv2.imwrite(args.simpan, frame_out)
    print(f"\n💾 Frame hasil disimpan → {args.simpan}")
    print(f"   Buka file untuk melihat bounding box dan label.\n")
    print(SEP)
