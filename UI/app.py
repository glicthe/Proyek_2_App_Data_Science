import streamlit as st
import streamlit.components.v1 as components
import cv2
import numpy as np
from PIL import Image
# from ultralytics import YOLO  # Nanti di-uncomment saat best.pt sudah dimasukkan

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA
# ==========================================
st.set_page_config(page_title="Smart ADAS Dashboard", page_icon="🚗", layout="wide")

# ==========================================
# 2. SIDEBAR (NAVIGASI KIRI)
# ==========================================
st.sidebar.title("🚗 Smart ADAS Navigasi")
st.sidebar.markdown("Silakan pilih mode operasi dasbor:")

# Menu Utama dengan 5 Fitur yang diminta
menu_pilihan = st.sidebar.radio(
    "Menu Utama:",
    ("🏠 Dashboard Screen", 
     "🖼️ Deteksi Gambar", 
     "🎬 Deteksi Video", 
     "📹 Deteksi Realtime (Webcam)", 
     "⛈️ Stress Test (Kondisi Ekstrem)")
)

st.sidebar.markdown("---")
st.sidebar.caption("Proyek Tugas Akhir - Kelompok 6")

# ==========================================
# 3. MAIN SCREEN (TENGAH KE KANAN)
# ==========================================

# FITUR 5: DASHBOARD SCREEN (Pendahuluan)
if menu_pilihan == "🏠 Dashboard Screen":
    st.title("Selamat Datang di Smart ADAS Dashboard")
    
    # Membaca dan menampilkan file HTML eksternal
    try:
        with open("dashboard_anim.html", "r", encoding="utf-8") as f:
            html_data = f.read()
        # Render HTML ke dalam Streamlit dengan tinggi yang pas
        components.html(html_data, height=220)
    except FileNotFoundError:
        st.warning("File animasi tidak ditemukan.")

    st.markdown("""
    Sistem cerdas ini dirancang untuk mendeteksi rambu lalu lintas secara otomatis menggunakan arsitektur YOLOv8.
    
    **Fitur yang tersedia:**
    * **Deteksi Gambar:** Mengunggah gambar statis untuk analisis piksel.
    * **Deteksi Video:** Memutar rekaman perjalanan (Dashcam).
    * **Deteksi Realtime:** Menggunakan kamera langsung untuk simulasi langsung.
    * **Stress Test:** Pengujian model AI pada kondisi ekstrem (malam hari, hujan, kamera goyang).
    
    *Silakan pilih menu di sebelah kiri untuk memulai.*
    """)

# FITUR 1: DETEKSI GAMBAR
elif menu_pilihan == "🖼️ Deteksi Gambar":
    st.title("Deteksi Gambar Statis")
    file_gambar = st.file_uploader("Upload gambar rambu (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
    
    if file_gambar is not None:
        # Menampilkan gambar asli
        gambar_asli = Image.open(file_gambar)
        st.image(gambar_asli, caption="Gambar yang diunggah", use_container_width=True)
        
        if st.button("Mulai Deteksi AI"):
            with st.spinner("AI sedang menganalisis gambar..."):
                # NANTI KODE YOLO MASUK DI SINI
                # hasil = model.predict(gambar_asli)
                
                st.success("Deteksi Selesai! (Ini adalah tempat gambar hasil deteksi kotak merah nanti dimunculkan)")

# FITUR 2: DETEKSI VIDEO
elif menu_pilihan == "🎬 Deteksi Video":
    st.title("Deteksi Video (Dashcam)")
    file_video = st.file_uploader("Upload video perjalanan (MP4)", type=['mp4'])
    
    if file_video is not None:
        st.video(file_video) # Memutar video bawaan streamlit
        st.info("Catatan: Untuk memproses deteksi frame-by-frame, kita akan menggunakan OpenCV pada iterasi selanjutnya.")
        
        if st.button("Proses Video dengan AI"):
            st.warning("Fitur pemrosesan video sedang dalam tahap integrasi dengan model.")

# FITUR 3: DETEKSI REALTIME (WEBCAM)
elif menu_pilihan == "📹 Deteksi Realtime (Webcam)":
    st.title("Live Dashcam (Simulasi ADAS)")
    st.markdown("Pastikan webcam tidak sedang digunakan oleh aplikasi lain.")
    
    run_kamera = st.checkbox("Nyalakan Kamera")
    tempat_video = st.empty() # Placeholder (Layar kosong yang akan diisi frame video berulang-ulang)
    
    if run_kamera:
        kamera = cv2.VideoCapture(0)
        
        while run_kamera:
            sukses, frame = kamera.read()
            if not sukses:
                st.error("Gagal membaca kamera.")
                break
                
            # Konversi warna agar tidak biru di Streamlit
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # NANTI KODE YOLO PREDICT MASUK DI SINI
            
            # Menembakkan gambar ke layar secara real-time
            tempat_video.image(frame_rgb, channels="RGB", use_container_width=True)
            
        kamera.release()
    else:
        st.write("Kamera dimatikan.")

# FITUR 4: STRESS TEST
elif menu_pilihan == "⛈️ Stress Test (Kondisi Ekstrem)":
    st.title("Galeri Pengujian Kondisi Ekstrem")
    st.markdown("Pembuktian ketangguhan model AI pada kondisi yang tidak ideal.")
    
    # Dropdown untuk memilih skenario
    skenario = st.selectbox("Pilih Skenario Uji:", ("Malam Hari / Minim Cahaya", "Hujan Lebat", "Kamera Goyang (Blur)"))
    
    st.info(f"Anda memilih skenario: **{skenario}**. (Video demo dari tim QA/Rangga akan dimasukkan ke sini nantinya).")
    
    # Ruang untuk menampilkan video stress test
    st.image("https://via.placeholder.com/800x400.png?text=Video+Stress+Test+Akan+Tampil+Di+Sini", use_container_width=True)

