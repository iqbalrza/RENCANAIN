# 🗺️ Rencanain — AI-Powered Bandung Trip Planner

> Rencanakan perjalanan wisata Bandung secara cerdas dengan kecerdasan buatan. Itinerary lengkap, rute optimal, dan budget smart — dalam hitungan detik.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45.0-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Azure OpenAI](https://img.shields.io/badge/Azure%20OpenAI-GPT--4o-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Azure AI Search](https://img.shields.io/badge/Azure%20AI%20Search-RAG-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Azure Maps](https://img.shields.io/badge/Azure%20Maps-Routes-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Hackathon](https://img.shields.io/badge/Microsoft%20Elevate%20Hackathon-2025-5C2D91?style=flat&logo=microsoft&logoColor=white)

---

## 📋 Daftar Isi

- [Tentang Proyek](#-tentang-proyek)
- [Fitur Utama](#-fitur-utama)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Tech Stack](#-tech-stack)
- [Struktur Proyek](#-struktur-proyek)
- [Instalasi & Setup](#-instalasi--setup)
- [Konfigurasi Azure](#-konfigurasi-azure)
- [Menjalankan Aplikasi](#-menjalankan-aplikasi)
- [Dataset](#-dataset)
- [API Services](#-api-services)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Kontribusi](#-kontribusi)

---

## 🌟 Tentang Proyek

**Rencanain** adalah aplikasi perencanaan wisata berbasis AI yang dikembangkan untuk **Microsoft Elevate Hackathon 2025** pada platform Dicoding. Aplikasi ini memungkinkan wisatawan merencanakan perjalanan ke Bandung secara otomatis — mulai dari rekomendasi hotel, itinerary per hari, kuliner, rute peta, hingga kalkulasi budget — hanya dengan mengisi satu form.

Sistem menggunakan pipeline **RAG (Retrieval-Augmented Generation)** dengan Azure AI Search sebagai knowledge base dan Azure OpenAI GPT-4o sebagai reasoning engine, sehingga rekomendasi yang dihasilkan akurat dan tidak berhalusinasi.

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🤖 **AI Itinerary Builder** | Susun jadwal perjalanan per hari otomatis berdasarkan preferensi dan budget |
| 🗺️ **Peta Rute Interaktif** | Visualisasi rute per hari dengan Folium + Azure Maps Route API |
| 💰 **Budget Allocator** | Alokasi otomatis 40% hotel / 25% wisata / 25% kuliner / 10% transport |
| 🚆 **Rekomendasi Transportasi** | Saran moda transport dari kota asal ke Bandung via LLM |
| 📍 **Optimasi Rute (TSP)** | Nearest Neighbor Algorithm untuk urutan kunjungan paling efisien |
| 🔍 **RAG Search** | Azure AI Search pada 3 index: wisata, hotel, kuliner |
| 📝 **Narasi AI** | Generate ringkasan perjalanan gaya pemandu wisata |
| 📊 **Visualisasi Budget** | Progress bar dan breakdown biaya per kategori |
| 🛡️ **Anti-Halusinasi** | Grounding strategy: LLM hanya merespons dari context documents |
| ⚡ **Fallback Lokal** | Semua Azure service memiliki fallback lokal agar app tetap berjalan |

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                   │
│  Form Input → Itinerary Card → Map View → Budget Card   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                     CORE LOGIC                          │
│                                                         │
│  ┌─────────────────┐    ┌──────────────────────────┐    │
│  │ Itinerary Builder│    │   Budget Allocator        │    │
│  │  - Filter wisata │    │   40% Hotel               │    │
│  │  - Select hotel  │    │   25% Wisata              │    │
│  │  - Plan kuliner  │    │   25% Kuliner             │    │
│  └────────┬────────┘    │   10% Transport           │    │
│           │              └──────────────────────────┘    │
│  ┌────────▼────────┐                                     │
│  │  Haversine +    │                                     │
│  │  Nearest        │                                     │
│  │  Neighbor (TSP) │                                     │
│  └─────────────────┘                                     │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   AZURE SERVICES                        │
│                                                         │
│  ┌──────────────┐ ┌─────────────────┐ ┌─────────────┐  │
│  │ Azure OpenAI │ │ Azure AI Search  │ │ Azure Maps  │  │
│  │   GPT-4o     │ │  3 Index:        │ │ Route API   │  │
│  │              │ │  - wisata-alam   │ │             │  │
│  │ - Intent     │ │  - hotel-budget  │ │ - Rute jalan│  │
│  │   Extraction │ │  - kuliner-lokal │ │ - Multi-WP  │  │
│  │ - Narrative  │ │                  │ │ - OSRM FB   │  │
│  │ - Transport  │ │  Fallback: JSON  │ │             │  │
│  └──────────────┘ └─────────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

**Frontend & Framework**
- [Streamlit](https://streamlit.io/) 1.45.0 — UI web app
- [Folium](https://python-visualization.github.io/folium/) + [streamlit-folium](https://github.com/randyzwitch/streamlit-folium) — Peta interaktif

**AI & Cloud (Microsoft Azure)**
- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) (GPT-4o) — LLM untuk narasi, intent extraction, rekomendasi transport
- [Azure AI Search](https://azure.microsoft.com/en-us/products/ai-services/cognitive-search) — RAG full-text search pada 3 index
- [Azure Maps](https://azure.microsoft.com/en-us/products/azure-maps) — Route directions API untuk rute jalan sesungguhnya

**Libraries**
- `openai` 1.78.1 — Azure OpenAI client
- `azure-search-documents` 11.6.0 — Azure AI Search client
- `requests` 2.32.3 — HTTP client (Azure Maps, OSRM)
- `python-dotenv` 1.1.0 — Environment variable management

**Algoritma**
- Haversine Formula — Kalkulasi jarak koordinat
- Nearest Neighbor Algorithm — Optimasi urutan kunjungan (TSP approximation)
- RAG (Retrieval-Augmented Generation) — Grounding LLM dengan data lokal

---

## 📁 Struktur Proyek

```
app/
├── main.py                        # Entry point Streamlit
├── config.py                      # Load env variables & Azure credentials
├── requirements.txt
├── .gitignore
│
├── components/                    # UI Components
│   ├── form_input.py              # Form 5-field input
│   ├── itinerary_card.py          # Tampilan itinerary per hari
│   ├── budget_summary.py          # Progress bar & breakdown budget
│   ├── map_view.py                # Peta rute Folium per hari
│   └── transport_card.py         # Card rekomendasi transportasi
│
├── core/                          # Business Logic
│   ├── itinerary_builder.py       # Algoritma susun itinerary
│   ├── budget_allocator.py        # Alokasi budget 40/25/25/10
│   └── haversine.py               # Haversine + Nearest Neighbor TSP
│
├── services/                      # Azure Service Wrappers
│   ├── openai_service.py          # Azure OpenAI (+ local fallback)
│   ├── search_service.py          # Azure AI Search (+ local fallback)
│   ├── maps_service.py            # Azure Maps (+ Haversine fallback)
│   └── grounding.py               # RAG pipeline & system prompt builder
│
├── data/                          # Dataset JSON
│   ├── wisata.json                # 50+ destinasi wisata Bandung
│   ├── hotel.json                 # 20 hotel (Budget/Mid-Range/Premium)
│   ├── kuliner.json               # 50 kuliner (lokal, kafe, jajanan)
│   └── jarak_matrix.json          # Pre-computed distance matrix
│
├── utils/                         # Utilities
│   ├── formatter.py               # Format Rupiah, durasi, jarak
│   ├── validator.py               # Validasi form input
│   └── logger.py                  # Logging handler
│
├── scripts/                       # Scripts operasional
│   ├── seed_data.py               # Validasi & statistik dataset
│   ├── upload_index.py            # Upload data ke Azure AI Search
│   └── precompute_jarak.py        # Pre-compute distance matrix
│
└── tests/                         # Unit tests
    ├── test_budget_allocator.py
    ├── test_search_service.py
    └── test_grounding.py
```

---

## 🚀 Instalasi & Setup

### Prasyarat

- Python 3.10 atau lebih baru
- pip / virtualenv

### 1. Clone Repository

```bash
git clone https://github.com/username/rencanain.git
cd rencanain
```

### 2. Buat Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r app/requirements.txt
```

### 4. Buat File `.env`

Buat file `.env` di dalam folder `app/`:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-search-key-here
AZURE_SEARCH_INDEX_WISATA=wisata-alam
AZURE_SEARCH_INDEX_HOTEL=hotel-budget
AZURE_SEARCH_INDEX_KULINER=kuliner-lokal

# Azure Maps
AZURE_MAPS_API_KEY=your-maps-key-here
```

> **Catatan:** Aplikasi tetap berjalan tanpa Azure credentials menggunakan mode fallback lokal (data JSON + algoritma lokal).

---

## ☁️ Konfigurasi Azure

### Azure OpenAI

1. Buat resource **Azure OpenAI** di [Azure Portal](https://portal.azure.com)
2. Deploy model **GPT-4o** pada resource tersebut
3. Salin endpoint dan API key ke `.env`

### Azure AI Search

1. Buat resource **Azure AI Search** (Free tier cukup untuk development)
2. Upload dataset menggunakan script:
   ```bash
   cd app
   python scripts/upload_index.py
   ```
3. Script akan membuat 3 index: `wisata-alam`, `hotel-budget`, `kuliner-lokal`

### Azure Maps

1. Buat resource **Azure Maps Account**
2. Salin subscription key ke `.env`
3. Digunakan untuk rute jalan sesungguhnya; fallback ke OSRM jika tidak tersedia

---

## ▶️ Menjalankan Aplikasi

```bash
cd app
streamlit run main.py
```

Aplikasi akan berjalan di `http://localhost:8501`

### Pre-compute Distance Matrix (Opsional)

Untuk mempercepat kalkulasi jarak saat runtime:

```bash
cd app
python scripts/precompute_jarak.py
```

---

## 📊 Dataset

Dataset tersimpan dalam format JSON di folder `app/data/`:

| File | Jumlah | Keterangan |
|------|--------|------------|
| `wisata.json` | 50+ entri | Destinasi wisata Bandung & sekitar (Alam, Budaya, Hiburan, Kota) |
| `hotel.json` | 20 entri | Hotel Budget (Rp 120rb-350rb), Mid-Range (Rp 480rb-650rb), Premium (Rp 1.1jt+) |
| `kuliner.json` | 50 entri | Rumah makan Sunda, kafe, jajanan, restoran viral 2025-2026 |

Setiap entri memiliki koordinat GPS (`lat`, `lng`) untuk keperluan peta dan kalkulasi rute.

### Validasi Dataset

```bash
cd app
python scripts/seed_data.py
```

---

## 🔌 API Services

### `openai_service.py`

| Fungsi | Deskripsi |
|--------|-----------|
| `extract_intent(form_data)` | Parse input form → structured query untuk retrieval |
| `generate_narrative(itinerary_data)` | Generate narasi perjalanan bergaya pemandu wisata |
| `generate_transport_recommendation(kota_asal, jumlah_orang, budget)` | Rekomendasi moda transportasi |

### `search_service.py`

| Fungsi | Deskripsi |
|--------|-----------|
| `search_wisata(query, top, filters)` | Cari destinasi wisata |
| `search_hotel(query, top, filters)` | Cari hotel |
| `search_kuliner(query, top, filters)` | Cari kuliner |
| `search_all(query, top_per_category)` | Cari di semua 3 index |

### `maps_service.py`

| Fungsi | Deskripsi |
|--------|-----------|
| `optimize_route(destinations, start_lat, start_lng)` | Optimasi urutan kunjungan |
| `get_distance_between(lat1, lng1, lat2, lng2)` | Jarak antara dua titik |

---

## 🧪 Testing

Jalankan semua unit test:

```bash
cd app

# Test budget allocator
python tests/test_budget_allocator.py

# Test search service
python tests/test_search_service.py

# Test grounding / RAG pipeline
python tests/test_grounding.py
```

Semua test berjalan dengan fallback lokal tanpa memerlukan koneksi Azure.

---

## 🚢 Deployment

### Streamlit Community Cloud

1. Push ke GitHub
2. Buka [share.streamlit.io](https://share.streamlit.io)
3. Set `app/main.py` sebagai entry point
4. Tambahkan secrets (`.env`) pada **Settings → Secrets**

### Azure Static Web Apps (Rekomendasi Hackathon)

Untuk deployment ke Azure menggunakan Azure Static Web Apps + Azure Functions:

1. Build Streamlit app sebagai static export atau gunakan Azure Container Apps
2. Pastikan semua environment variable dikonfigurasi di **Application Settings**
3. Hubungkan dengan Azure AI Search, OpenAI, dan Maps yang sudah di-provision

---

## 🧩 Alur Kerja Aplikasi

```
User mengisi form (kota asal, durasi, jumlah orang, budget, preferensi)
        │
        ▼
build_itinerary() — Core algorithm
  ├── allocate_budget() → 40/25/25/10
  ├── filter wisata by preferensi
  ├── nearest_neighbor_route() → optimasi TSP
  ├── filter_hotel_by_budget() → pilih hotel terbaik
  └── susun kuliner per waktu makan
        │
        ▼
generate_transport_recommendation() — Azure OpenAI / fallback
        │
        ▼
generate_narrative() — Azure OpenAI / fallback
        │
        ▼
Render UI:
  ├── Tab 1: Itinerary card + transport card + narasi
  ├── Tab 2: Peta rute Folium (Azure Maps / OSRM / straight line)
  └── Tab 3: Budget summary + breakdown per kategori
```

---

## 📄 Lisensi

Proyek ini dibuat untuk keperluan **Microsoft Elevate Hackathon 2025** di Dicoding. Bebas digunakan untuk tujuan edukasi dan non-komersial.

---

## 👤 Author

Dibuat dengan ❤️ untuk Microsoft Elevate Hackathon 2025

**Powered by:**
- 🔵 Azure OpenAI (GPT-4o)
- 🔵 Azure AI Search
- 🔵 Azure Maps
- 🔴 Streamlit
