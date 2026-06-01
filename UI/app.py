"""
=============================================================
Smart ADAS Dashboard — UI/app.py
Kelompok 4 | Proyek Tugas Akhir
=============================================================
Jalankan dengan:
    cd UI
    streamlit run app.py
=============================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import cv2
import numpy as np
from PIL import Image
import os

# -------------------------------------------------------------------
# Impor dari Model/inference.py — aktif setelah best.pt tersedia
# -------------------------------------------------------------------
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Model"))
from inference import jalankan_deteksi, MODEL_YOLO # type: ignore

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Utils"))
from audio_manager import putar_audio_gtts # type: ignore

from ui_components import render_speedometer

# ===========================================================================
# 0. KONFIGURASI HALAMAN GLOBAL
# ===========================================================================
st.set_page_config(
    page_title="Smart ADAS Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeksi CSS kustom agar tampilan lebih tajam dan berwarna
st.markdown("""
<style>
/* ---- Palet warna tema gelap ala HUD kendaraan ---- */
:root {
    --bg-dark:     #0d1117;
    --panel-bg:    #161b22;
    --accent:      #00e5ff;
    --accent-warn: #ffd600;
    --accent-err:  #ff1744;
    --accent-ok:   #00e676;
    --text-main:   #e6edf3;
    --text-muted:  #8b949e;
}

/* ---- Latar belakang utama ---- */
.stApp {
    background-color: var(--bg-dark);
    color: var(--text-main);
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background-color: var(--panel-bg);
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] * {
    color: var(--text-main) !important;
}

/* ---- Metrik (KPI card) ---- */
[data-testid="stMetric"] {
    background: var(--panel-bg);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--accent) !important;
}

/* ---- Tombol ---- */
.stButton > button {
    background: linear-gradient(135deg, #00b4d8, #0077b6);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; }

/* ---- Alert / Info box kustom ---- */
.notif-ok    { background:#003322; border-left:4px solid var(--accent-ok);   color:var(--accent-ok);   padding:12px 16px; border-radius:8px; font-weight:600; }
.notif-warn  { background:#332b00; border-left:4px solid var(--accent-warn); color:var(--accent-warn); padding:12px 16px; border-radius:8px; font-weight:600; }
.notif-error { background:#330011; border-left:4px solid var(--accent-err);  color:var(--accent-err);  padding:12px 16px; border-radius:8px; font-weight:600; }

/* ---- Divider ---- */
hr { border-color: #30363d; }

/* ---- Judul section ---- */
h1, h2, h3 { color: var(--accent) !important; letter-spacing: 0.02em; }
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# 1. FUNGSI UTILITAS (PLACEHOLDER — akan dihubungkan ke core_logic.py nanti)
# ===========================================================================

def muat_animasi_html(path_html: str, tinggi: int = 200) -> None:
    """
    Render file HTML eksternal (animasi/banner) ke dalam Streamlit.
    Letakkan 'dashboard_anim.html' di folder UI/ yang sama dengan app.py.
    """
    if os.path.exists(path_html):
        with open(path_html, "r", encoding="utf-8") as f:
            html_konten = f.read()
        components.html(html_konten, height=tinggi, scrolling=False)
    else:
        st.caption(f"ℹ️ File animasi `{path_html}` belum ditemukan — lewati.")


# dummy_deteksi_frame() sudah dihapus.
# Seluruh deteksi sekarang ditangani oleh jalankan_deteksi() dari Model/inference.py.


def render_panel_notifikasi(status: str, pesan: str) -> None:
    """
    Tampilkan kotak notifikasi berwarna sesuai status dari core_logic.
    status: 'Aman' | 'Info' | 'Peringatan' | 'Larangan' | 'Pelanggaran'
    """
    # Normalisasi huruf besar/kecil agar robust terhadap variasi input
    status_lower = status.lower()

    ikon_map = {
        "aman"       : "✅",
        "info"       : "ℹ️",
        "peringatan" : "⚠️",
        "larangan"   : "🚫",
        "pelanggaran": "🚨",
    }
    css_map = {
        "aman"       : "notif-ok",
        "info"       : "notif-ok",
        "peringatan" : "notif-warn",
        "larangan"   : "notif-error",
        "pelanggaran": "notif-error",
    }

    ikon     = ikon_map.get(status_lower, "ℹ️")
    kelas_css = css_map.get(status_lower, "notif-ok")

    st.markdown(
        f"<div class='{kelas_css}'>"
        f"{ikon} &nbsp;<strong>{status.upper()}</strong> — {pesan}"
        f"</div>",
        unsafe_allow_html=True,
    )


# ===========================================================================
# 2. SIDEBAR — Navigasi + Animasi HTML
# ===========================================================================
with st.sidebar:
    st.markdown("## 🚗 Smart ADAS")
    st.markdown("---")

    menu_pilihan = st.radio(
        "Pilih Mode:",
        (
            "🏠 Dashboard",
            "🖼️ Deteksi Gambar",
            "🎬 Deteksi Video",
            "📹 Realtime (Webcam)",
            "⛈️ Stress Test",
        ),
        label_visibility="collapsed",
    )

    st.markdown("---")

    # # ── Animasi HTML di bagian bawah sidebar ──────────────────────────────
    # st.caption("Preview Dashboard Animation")
    # # Path relatif dari folder UI/ tempat app.py berada
    # muat_animasi_html("dashboard_anim.html", tinggi=180)

    st.markdown("---")
    st.caption("Kelompok 4 · Tugas Akhir · 2025")


# ===========================================================================
# 3. HALAMAN: DASHBOARD (Landing)
# ===========================================================================
if menu_pilihan == "🏠 Dashboard":

    # ── Header ──────────────────────────────────────────────────────────────
    col_judul, col_logo = st.columns([4, 1])
    with col_judul:
        st.title("Smart ADAS Dashboard")
        st.markdown("Sistem deteksi rambu lalu lintas Indonesia berbasis **YOLOv8** — 48 kelas.")
    with col_logo:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("# 🚦", unsafe_allow_html=False)   # ganti dengan st.image() jika ada logo
        
    # ── ANIMASI HTML PINDAH KE SINI ───────────────────────────────
    muat_animasi_html("dashboard_anim.html", tinggi=220)

    st.markdown("---")

    # ── KPI Cards ───────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    
    # Deteksi status mesin YOLO secara dinamis
    if MODEL_YOLO is not None:
        status_model = "Aktif (Dimuat)"
        mode_aktif = "AI Inference"
        jumlah_kelas = str(len(MODEL_YOLO.names)) # Otomatis baca jumlah kelas dari best.pt
    else:
        status_model = "Belum Dimuat"
        mode_aktif = "Demo / Dummy"
        jumlah_kelas = "-"

    k1.metric("Total Kelas Rambu", jumlah_kelas, delta=None)
    k2.metric("Model", "YOLOv8", delta=None)
    k3.metric("Status Model", status_model, delta=None)
    k4.metric("Mode Aktif", mode_aktif, delta=None)
    st.markdown("---")

    # ── Ringkasan Fitur ─────────────────────────────────────────────────────
    st.subheader("Panduan Cepat")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown("#### 🖼️ Gambar\nUnggah foto rambu untuk analisis satu frame.")
    with f2:
        st.markdown("#### 🎬 Video\nPutar rekaman dashcam & atur kecepatan simulator.")
    with f3:
        st.markdown("#### 📹 Realtime\nHubungkan webcam untuk ADAS langsung.")
    with f4:
        st.markdown("#### ⛈️ Stress Test\nUji model pada kondisi ekstrem (malam, hujan, blur).")


# ===========================================================================
# 4. HALAMAN: DETEKSI GAMBAR
# ===========================================================================
elif menu_pilihan == "🖼️ Deteksi Gambar":

    st.title("🖼️ Deteksi Gambar Statis")
    st.markdown("Unggah gambar rambu lalu lintas untuk dianalisis oleh model AI.")

    # ── Upload ───────────────────────────────────────────────────────────────
    file_gambar = st.file_uploader("Pilih file gambar (JPG / PNG)", type=["jpg", "jpeg", "png"])

    if file_gambar:
        gambar_pil = Image.open(file_gambar).convert("RGB")
        gambar_np = np.array(gambar_pil)

        kol_ori, kol_hasil = st.columns(2, gap="large")

        with kol_ori:
            st.subheader("Gambar Asli")
            st.image(gambar_pil, use_container_width=True)

        with kol_hasil:
            st.subheader("Hasil Deteksi")
            placeholder_hasil = st.empty()
            placeholder_notif = st.empty()

            if st.button("🔍 Mulai Deteksi AI", use_container_width=True):
                with st.spinner("Model sedang memproses gambar…"):
                    # Panggil inference nyata dari Model/inference.py
                    frame_out, deteksi, status, pesan = jalankan_deteksi(
                        gambar_np, kecepatan_kmh=0
                    )
                    # Konversi BGR → RGB untuk ditampilkan di Streamlit
                    frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)
                    placeholder_hasil.image(frame_rgb, channels="RGB", use_container_width=True)

                with placeholder_notif.container():
                    render_panel_notifikasi(status, pesan)
                    if deteksi:
                        st.json(deteksi)   # tampilkan raw JSON deteksi saat tersedia

    else:
        st.info("Belum ada gambar yang diunggah.")


# ===========================================================================
# 5. HALAMAN: DETEKSI VIDEO
# ===========================================================================
elif menu_pilihan == "🎬 Deteksi Video":

    st.title("🎬 Deteksi Video — Simulasi Dashcam")

    # ── Upload Video ─────────────────────────────────────────────────────────
    file_video = st.file_uploader("Upload rekaman dashcam (MP4)", type=["mp4", "avi", "mov"])

    if file_video:

        st.markdown("---")

        # ── Layout Utama: Player | Panel Kontrol ─────────────────────────────
        kol_player, kol_panel = st.columns([3, 2], gap="large")

        # ---- Kolom Kiri: Player Video + Placeholder Frame Deteksi ----
        with kol_player:
            st.subheader("Preview Video Asli")
            st.video(file_video)

            st.subheader("Output Frame Deteksi (Real-time)")
            placeholder_frame = st.empty()   # ← tempat frame hasil YOLO di-render nanti
            placeholder_frame.markdown(
                "<div style='background:#161b22;border:1px dashed #30363d;"
                "border-radius:10px;height:220px;display:flex;"
                "align-items:center;justify-content:center;color:#8b949e;'>"
                "Frame hasil deteksi akan muncul di sini saat model aktif."
                "</div>",
                unsafe_allow_html=True,
            )

        # ---- Kolom Kanan: Kontrol & Notifikasi ----
        with kol_panel:
            st.subheader("⚙️ Panel Kontrol ADAS")

            # ── Speed Simulator Slider ─────────────────────────────────────
            kecepatan_kmh = st.slider(
                "🚀 Kecepatan Kendaraan (km/h)",
                min_value=0,
                max_value=150,
                value=60,
                step=5,
                help="Manipulasi kecepatan simulasi untuk memicu rule engine ADAS.",
            )

            # Indikator visual kecepatan
            if kecepatan_kmh <= 40:
                warna_spd, label_spd = "#00e676", "PELAN"
            elif kecepatan_kmh <= 80:
                warna_spd, label_spd = "#ffd600", "SEDANG"
            else:
                warna_spd, label_spd = "#ff1744", "CEPAT"

            st.markdown(
                f"<div style='font-size:2.2rem;font-weight:800;color:{warna_spd};"
                f"text-align:center;letter-spacing:0.06em;padding:8px 0'>"
                f"{kecepatan_kmh} km/h &nbsp;<span style='font-size:1rem'>{label_spd}</span></div>",
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # ── Panel Notifikasi Status Rambu ──────────────────────────────
            st.subheader("🔔 Status Deteksi Rambu")
            placeholder_notif_video = st.empty()

            with placeholder_notif_video.container():
                # Nilai default sebelum model jalan
                render_panel_notifikasi("aman", "Menunggu proses deteksi dimulai…")

            st.markdown("---")

            # ── Tombol Proses ──────────────────────────────────────────────
            if st.button("▶ Proses Video dengan AI", use_container_width=True):
                # 1. Simpan raw video sementara agar bisa dibaca OpenCV
                tmp_path = "adas_video.mp4"
                with open(tmp_path, "wb") as f:
                    f.write(file_video.read())

                cap = cv2.VideoCapture(tmp_path)
                if not cap.isOpened():
                    st.error("❌ Gagal membuka file video. Pastikan format MP4/AVI valid.")
                else:
                    # 2. Persiapkan VideoWriter untuk membuat video baru
                    output_path = "hasil_deteksi_adas.mp4"
                    lebar = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    tinggi = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
                    
                    # Gunakan codec mp4v (standar kompresi MP4 di OpenCV)
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(output_path, fourcc, fps, (lebar, tinggi))

                    progress_bar = st.progress(0, text="Memproses video…")
                    frame_ke = 0

                    while cap.isOpened():
                        ok, frame = cap.read()
                        if not ok:
                            break

                        # Jalankan deteksi YOLO + rule engine
                        frame_out, deteksi, status, pesan = jalankan_deteksi(
                            frame, kecepatan_kmh
                        )

                        # --- TAMBAHKAN TRIGGER AUDIO DI SINI ---
                        if status in ["Peringatan", "Pelanggaran"]:
                            putar_audio_gtts(pesan)

                        # --- BAGIAN BARU: Tulis frame yang sudah ada bounding box ke video baru ---
                        out.write(frame_out)

                        # Konversi BGR → RGB untuk ditampilkan di Streamlit
                        frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)
                        placeholder_frame.image(frame_rgb, channels="RGB", use_container_width=True)

                        with placeholder_notif_video.container():
                            render_panel_notifikasi(status, pesan)

                        # Update progress bar
                        frame_ke += 1
                        pct = min(int(frame_ke / total_frame * 100), 100)
                        progress_bar.progress(pct, text=f"Frame {frame_ke}/{total_frame}")

                    # 3. Tutup dan bersihkan memory (Sangat Penting!)
                    cap.release()
                    out.release() 
                    progress_bar.empty()
                    st.success(f"✅ Selesai memproses {frame_ke} frame!")

                    # 4. Tampilkan tombol unduh untuk video yang baru dibuat
                    with open(output_path, "rb") as file_hasil:
                        st.download_button(
                            label="⬇️ Unduh Video Hasil Deteksi",
                            data=file_hasil,
                            file_name="ADAS_Result.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )

    else:
        st.info("Belum ada video yang diunggah. Silakan unggah file MP4 dashcam.")


# ===========================================================================
# 6. HALAMAN: REALTIME WEBCAM
# ===========================================================================
elif menu_pilihan == "📹 Realtime (Webcam)":

    st.title("📹 Live Webcam — Simulasi ADAS Real-time")
    st.markdown("Pastikan browser sudah memberi izin akses kamera.")

    kol_cam, kol_ctrl = st.columns([3, 2], gap="large")

    with kol_ctrl:
        st.subheader("⚙️ Kontrol Kamera")

        # ── Pilihan Mode Kontrol Kecepatan ─────────────────────────────
        mode_kontrol = st.radio(
            "Metode Input Kecepatan:",
            ("🎚️ Slider Standar", "🏎️ Pedal Balap"),
            horizontal=True,
        )

        st.markdown("<br>", unsafe_allow_html=True) # Sedikit jarak (spacing)

        # ── Logika Saklar Kontrol ──────────────────────────────────────
        if mode_kontrol == "🎚️ Slider Standar":
            kecepatan_rt = st.slider(
                "🚀 Kecepatan Simulasi (km/h)",
                min_value=0, max_value=150, value=50, step=5,
            )
        else:
            kecepatan_rt = render_speedometer()

        st.markdown("---")

        # ── Saklar Kamera ──────────────────────────────────────────────
        nyalakan = st.checkbox("🟢 Nyalakan Kamera", value=False)

        st.markdown("---")
        st.subheader("🔔 Status Deteksi")
        placeholder_notif_rt = st.empty()
        with placeholder_notif_rt.container():
            render_panel_notifikasi("aman", "Kamera belum aktif.")

    with kol_cam:
        st.subheader("Feed Kamera")
        placeholder_cam = st.empty()

        if nyalakan:
            kamera = cv2.VideoCapture(0)

            if not kamera.isOpened():
                st.error("❌ Tidak dapat membuka kamera. Periksa koneksi atau izin browser.")
            else:
                # stop_btn = st.button("⏹ Hentikan Kamera")

                while nyalakan:
                    sukses, frame = kamera.read()
                    if not sukses:
                        st.error("Gagal membaca frame dari kamera.")
                        break

                    # Jalankan deteksi YOLO + rule engine (input BGR dari cv2)
                    frame_out, deteksi, status, pesan = jalankan_deteksi(frame, kecepatan_rt)

                    # --- TAMBAHKAN TRIGGER AUDIO DI SINI ---
                    if status in ["Peringatan", "Pelanggaran"]:
                        putar_audio_gtts(pesan)

                    # Konversi BGR → RGB untuk Streamlit
                    frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)

                    # Update frame & notifikasi
                    placeholder_cam.image(frame_rgb, channels="RGB", use_container_width=True)
                    with placeholder_notif_rt.container():
                        render_panel_notifikasi(status, pesan)

                kamera.release()
                placeholder_cam.markdown("_Kamera dimatikan._")
        else:
            placeholder_cam.markdown(
                "<div style='background:#161b22;border:1px dashed #30363d;"
                "border-radius:10px;height:340px;display:flex;"
                "align-items:center;justify-content:center;color:#8b949e;'>"
                "Feed kamera akan muncul di sini."
                "</div>",
                unsafe_allow_html=True,
            )


# ===========================================================================
# 7. HALAMAN: STRESS TEST
# ===========================================================================
elif menu_pilihan == "⛈️ Stress Test":

    st.title("⛈️ Stress Test — Kondisi Ekstrem")
    st.markdown("Uji ketangguhan model AI pada skenario lingkungan yang tidak ideal.")

    # ── Pilihan Skenario ─────────────────────────────────────────────────────
    SKENARIO = {
        "🌑 Malam Hari / Minim Cahaya": {
            "keterangan": "Simulasi kondisi visibilitas rendah — pencahayaan < 5 lux.",
            "filter_cv": "gelap",
        },
        "🌧️ Hujan Lebat": {
            "keterangan": "Simulasi noise rain-drop dan lens-fogging pada kamera dashcam.",
            "filter_cv": "hujan",
        },
        "📷 Kamera Goyang (Motion Blur)": {
            "keterangan": "Simulasi jalan berlubang atau getaran mesin yang menyebabkan blur.",
            "filter_cv": "blur",
        },
        "☀️ Silau Matahari (Overexposed)": {
            "keterangan": "Kondisi backlight ekstrem saat berkendara ke arah matahari.",
            "filter_cv": "silau",
        },
    }

    skenario_dipilih = st.selectbox("Pilih Skenario Uji:", list(SKENARIO.keys()))
    info_skenario = SKENARIO[skenario_dipilih]
    st.info(f"**Deskripsi:** {info_skenario['keterangan']}")

    st.markdown("---")

    kol_up, kol_preview = st.columns(2, gap="large")

    with kol_up:
        st.subheader("Unggah Media Uji")
        file_uji = st.file_uploader(
            "Upload gambar atau video untuk diuji di skenario ini",
            type=["jpg", "jpeg", "png", "mp4"],
            key="stress_uploader",
        )

    with kol_preview:
        st.subheader("Hasil Deteksi AI")
        placeholder_stress = st.empty()

        if file_uji:
            if file_uji.type.startswith("image"):
                img_uji = Image.open(file_uji).convert("RGB")
                img_np = np.array(img_uji)

                # Aplikasikan filter simulasi kondisi ekstrem
                if info_skenario["filter_cv"] == "gelap":
                    img_filter = (img_np * 0.25).astype(np.uint8)
                elif info_skenario["filter_cv"] == "hujan":
                    noise = np.random.randint(0, 60, img_np.shape, dtype=np.uint8)
                    img_filter = cv2.add(img_np, noise)
                elif info_skenario["filter_cv"] == "blur":
                    img_filter = cv2.GaussianBlur(img_np, (21, 21), 0)
                elif info_skenario["filter_cv"] == "silau":
                    img_filter = np.clip(img_np.astype(np.int32) + 110, 0, 255).astype(np.uint8)
                else:
                    img_filter = img_np

                # Kirim gambar yang sudah difilter ke YOLO
                # kecepatan_kmh=0 karena ini gambar statis, bukan skenario berkendara
                # img_filter adalah RGB (dari PIL) — inference.py menangani konversi BGR otomatis
                frame_out, deteksi, status, pesan = jalankan_deteksi(img_filter, kecepatan_kmh=0)

                # Konversi BGR → RGB hasil inference untuk ditampilkan di Streamlit
                frame_rgb = cv2.cvtColor(frame_out, cv2.COLOR_BGR2RGB)

                # Tampilkan frame hasil deteksi AI (bukan lagi img_filter mentah)
                placeholder_stress.image(frame_rgb, caption=f"Hasil AI: {skenario_dipilih}", use_container_width=True)

                # Tampilkan panel status notifikasi di bawah gambar
                render_panel_notifikasi(status, pesan)

            elif file_uji.type == "video/mp4":
                placeholder_stress.video(file_uji)
                st.caption("Proses filter video tersedia setelah integrasi OpenCV penuh.")
        else:
            placeholder_stress.markdown(
                "<div style='background:#161b22;border:1px dashed #30363d;"
                "border-radius:10px;height:260px;display:flex;"
                "align-items:center;justify-content:center;color:#8b949e;'>"
                "Preview skenario akan tampil di sini."
                "</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown(
        "📌 **Catatan Tim QA:** Hasil pengujian video dari tiap skenario akan "
        "didokumentasikan di folder `docs/stress_test/` setelah sesi recording selesai."
    )
