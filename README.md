# MonitoringBoiler_TTI

Sistem monitoring boiler berbasis Python untuk mengintegrasikan data dari PLC melalui protokol OPC DA dan menyimpannya ke database time-series InfluxDB. Proyek ini dirancang untuk keperluan monitoring industri, data logging, dan analisis sistem boiler secara real-time.

## 📋 Deskripsi

Proyek ini menyediakan solusi lengkap untuk:
- Membaca data dari OPC DA server (Kepware/MX OPC)
- Monitoring parameter boiler secara real-time
- Logging otomatis ke InfluxDB untuk analisis time-series
- GUI sederhana untuk memudahkan operasional
- Manajemen whitelist tag dan auto-discovery dari channel OPC

## ✨ Fitur Utama

- **Koneksi OPC DA**: Support untuk Kepware dan Mitsubishi MX OPC Server
- **Auto Logging**: Penyimpanan data otomatis ke InfluxDB dengan timestamp
- **Tag Management**: Whitelist tag dan batch read untuk efisiensi
- **GUI Application**: Interface Tkinter untuk start/stop logger dengan mudah
- **Flexible Configuration**: Konfigurasi melalui environment variables (.env)
- **CSV Tag List**: Daftar lengkap tag PLC dalam format CSV

## 🗂️ Struktur Proyek

```
MonitoringBoiler_TTI/
├── boiler_opcDA.py              # Script utama monitoring OPC → InfluxDB
├── boiler_opcDA_KepServer.py    # Khusus untuk Kepware (dengan whitelist)
├── boiler_opcDA_MX.py           # Khusus untuk Mitsubishi MX OPC
├── boilder_cek.py               # Utility untuk cek tag OPC yang tersedia
├── gui_app_boiler.py            # Aplikasi GUI runner (Start/Stop)
├── FX3U.csv                     # Daftar tag PLC (nama, address, tipe data)
├── requirements.txt             # Dependencies Python
├── openopc120-master/           # Library OpenOPC untuk Python 3
└── .gitignore                   # Git ignore file
```

## 🚀 Instalasi

### Prasyarat

- Python 3.7 (harus 3.7)
- OPC DA Server (Kepware/MX OPC) sudah terinstall dan running
- InfluxDB server (local atau cloud)
- Windows OS (untuk OpenOPC dengan pywin32)

### Langkah Instalasi

1. **Clone repository**
   ```bash
   git clone https://github.com/aryasjsr/MonitoringBoiler_TTI.git
   cd MonitoringBoiler_TTI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup OpenOPC** (jika diperlukan)
   ```bash
   cd openopc120-master
   python setup.py install
   ```

4. **Buat file .env**
   
   Buat file `.env` di root directory dengan konfigurasi berikut:
   ```env
   # OPC Server Configuration
   OPC_SERVER=NamaOPCServer
   OPC_HOST=localhost
   KEP_CHANNEL=BOILER
   KEP_ITEMS=tag1,tag2,tag3
   
   # InfluxDB Configuration
   INFLUX_URL=http://localhost:8086
   INFLUX_TOKEN=your-influxdb-token
   INFLUX_ORG=your-organization
   INFLUX_BUCKET=boiler-monitoring
   
   # Monitoring Settings
   CHANGE_TOLERANCE=0.0
   POLL_SEC=1
   ```

## 📖 Penggunaan

### 1. Monitoring Otomatis (Command Line)

Untuk menjalankan monitoring dengan logging otomatis ke InfluxDB:

```bash
python boiler_opcDA.py
```

### 2. GUI Application

Menjalankan aplikasi dengan interface grafis:

```bash
python gui_app_boiler.py
```

### 3. Cek Tag OPC yang Tersedia

Untuk melihat daftar tag yang tersedia di OPC server:

```bash
python boilder_cek.py
```

### 4. Script Spesifik Server

**Untuk Kepware:**
```bash
python boiler_opcDA_KepServer.py
```

**Untuk MX OPC:**
```bash
python boiler_opcDA_MX.py
```

## 📊 Daftar Tag PLC

Daftar tag yang dimonitor terdapat dalam file `FX3U.csv`. Contoh tag:

| Tag Name | Address | Data Type | Keterangan |
|----------|---------|-----------|------------|
| BUZZER | Y0007 | Boolean | Alarm buzzer |
| Flow Steam | D0000128 | Float | Sensor flow steam |
| Flow Water | D0000130 | Float | Sensor flow water |
| Furnace Temp | D0000108 | Short | Temperatur furnace |
| Pressure Water | D0000104 | Float | Sensor pressure water |
| Quantity Steam | D0000132 | Float | Quantity steam |
| RUN FDF | Y0001 | Boolean | Status FDF running |
| RUN IDF | Y0000 | Boolean | Status IDF running |

Untuk daftar lengkap, lihat file [FX3U.csv](FX3U.csv).

## 🔧 Dependencies

Proyek ini menggunakan library berikut:

```
certifi==2025.8.3
influxdb-client==1.36.1
OpenOPC-DA==1.5.1
Pyro5==5.15
python-dateutil==2.9.0.post0
python-dotenv==0.21.1
pywin32==225
reactivex==4.0.4
serpent==1.41
six==1.17.0
typing_extensions==4.5.0
urllib3==1.26.16
```

Install semua dependencies dengan:
```bash
pip install -r requirements.txt
```

## ⚙️ Konfigurasi

### Environment Variables (.env)

| Variable | Deskripsi | Contoh |
|----------|-----------|--------|
| `OPC_SERVER` | Nama OPC server | `Kepware.KEPServerEX.V6` |
| `OPC_HOST` | Host OPC server | `localhost` atau `192.168.1.100` |
| `KEP_CHANNEL` | Channel Kepware | `BOILER` |
| `KEP_ITEMS` | Item tags (comma-separated) | `tag1,tag2,tag3` |
| `INFLUX_URL` | URL InfluxDB | `http://localhost:8086` |
| `INFLUX_TOKEN` | Token autentikasi InfluxDB | `your-token-here` |
| `INFLUX_ORG` | Organisasi InfluxDB | `your-org` |
| `INFLUX_BUCKET` | Bucket untuk data | `boiler-monitoring` |
| `CHANGE_TOLERANCE` | Toleransi perubahan nilai | `0.0` |
| `POLL_SEC` | Interval polling (detik) | `1` |

## 🛠️ Troubleshooting

### Error: "Failed to connect to OPC Server"

- Pastikan OPC Server sudah running
- Cek nama OPC Server di environment variable
- Pastikan OPC Gateway Service aktif

### Error: "InfluxDB connection failed"

- Verifikasi URL dan token InfluxDB
- Pastikan bucket sudah dibuat
- Cek koneksi network ke InfluxDB server

### Tag tidak terbaca

- Jalankan `boilder_cek.py` untuk verifikasi tag yang tersedia
- Cek format nama tag di file FX3U.csv
- Pastikan PLC terhubung dengan OPC server

## 📝 Lisensi

Proyek ini menggunakan [OpenOPC for Python](https://github.com/joseamaita/openopc120) yang dilisensikan di bawah GNU GPL v2.

## 👤 Author

**aryasjsr**
- GitHub: [@aryasjsr](https://github.com/aryasjsr)

## 🤝 Kontribusi

Kontribusi, issues, dan feature requests sangat diterima!

## 📌 Catatan

- Proyek ini dikembangkan untuk keperluan monitoring industri
- Disarankan untuk testing di environment development terlebih dahulu
- Pastikan konfigurasi security InfluxDB sesuai standar production

---


