# 🤖 Tbot - Telegram Task Routing Bot

Tbot adalah bot Telegram pintar yang membantu pengguna menemukan tugas terdekat berdasarkan lokasi mereka. Bot ini mengakses Google Sheets sebagai backend data tugas dan menggambar rute dari lokasi pengguna ke lokasi tugas menggunakan peta statis.

## 🛠 Fitur

- 📍 Mendeteksi lokasi pengguna melalui Telegram
- 📄 Mengambil data tugas dari Google Sheets
- 🚦 Memprioritaskan tugas berdasarkan estimasi waktu tempuh
- 🗺 Menampilkan peta statis dengan rute dari lokasi pengguna ke tugas
- ✅ Menyimpan status dan progres tugas

## 📦 Instalasi

1. Clone repositori ini:
    ```bash
    git clone https://github.com/nurqoneah/Tele_Bot_Teknisi_Tsel
    cd Tele_Bot_Teknisi_Tsel
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Siapkan file `credentials.json` untuk akses Google Sheets menggunakan Google Service Account.

4. Jalankan bot:
    ```bash
    python bot.py
    ```

## 📄 Contoh Penggunaan

1. Kirim lokasi ke bot
2. Bot akan membalas dengan tugas terdekat dan estimasi waktu tempuh
3. Bot menampilkan gambar peta dengan rute
4. Pengguna dapat menerima tugas langsung dari chat

## 🧾 Requirements

File `requirements.txt`:

