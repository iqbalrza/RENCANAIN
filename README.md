# Rencanain — AI-Powered Bandung Trip Planner

Rencanakan perjalanan wisata Bandung secara cerdas dengan kecerdasan buatan. Itinerary lengkap, rute optimal, dan budget smart dalam hitungan detik.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45.0-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Azure OpenAI](https://img.shields.io/badge/Azure%20OpenAI-GPT--4o-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Azure AI Search](https://img.shields.io/badge/Azure%20AI%20Search-RAG-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Azure Maps](https://img.shields.io/badge/Azure%20Maps-Routes-0078D4?style=flat&logo=microsoftazure&logoColor=white)
![Hackathon](https://img.shields.io/badge/Microsoft%20Elevate%20Hackathon-2025-5C2D91?style=flat&logo=microsoft&logoColor=white)

---

## Daftar Isi

- [Tentang Proyek](#tentang-proyek)
- [Fitur Utama](#fitur-utama)
- [Arsitektur Sistem](#arsitektur-sistem)
- [RAG Pipeline](#rag-pipeline)
- [Tech Stack](#tech-stack)
- [Struktur Proyek](#struktur-proyek)
- [Instalasi dan Setup](#instalasi-dan-setup)
- [Konfigurasi Azure](#konfigurasi-azure)
- [Menjalankan Aplikasi](#menjalankan-aplikasi)
- [Dataset](#dataset)
- [API Services](#api-services)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Tentang Proyek

**Rencanain** (sebelumnya *BandungTrip AI*) adalah aplikasi perencanaan wisata berbasis AI yang dikembangkan untuk **Microsoft Elevate Hackathon 2025** pada platform Dicoding. Aplikasi ini memungkinkan wisatawan merencanakan perjalanan ke Bandung secara otomatis — mulai dari rekomendasi hotel, itinerary per hari, kuliner, rute peta, hingga kalkulasi budget — hanya dengan mengisi satu form.

Sistem menggunakan pipeline **RAG (Retrieval-Augmented Generation)** dengan Azure AI Search sebagai knowledge base dan Azure OpenAI GPT-4o sebagai reasoning engine, sehingga rekomendasi yang dihasilkan akurat dan tidak berhalusinasi.

---

## Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **AI Itinerary Builder** | Susun jadwal perjalanan per hari otomatis berdasarkan preferensi dan budget |
| **Peta Rute Interaktif** | Visualisasi rute per hari dengan Folium dan Azure Maps Route API |
| **Budget Allocator** | Alokasi otomatis 40% hotel, 25% wisata, 25% kuliner, 10% transport |
| **Rekomendasi Transportasi** | Saran moda transport dari kota asal ke Bandung via LLM |
| **Optimasi Rute (TSP)** | Nearest Neighbor Algorithm untuk urutan kunjungan paling efisien |
| **RAG Search** | Azure AI Search pada 3 index: wisata, hotel, kuliner |
| **Narasi AI Grounded** | Generate ringkasan perjalanan berbasis context dari Azure Search |
| **Visualisasi Budget** | Progress bar dan breakdown biaya per kategori |
| **Anti-Halusinasi** | Grounding strategy: LLM hanya merespons dari context documents |
| **Fallback Lokal** | Semua Azure service memiliki fallback lokal agar app tetap berjalan |

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                   │
│  Form Input → Itinerary Card → Map View → Budget Card   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                     CORE LOGIC                          │
│                                                         │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ Itinerary Builder│    │   Budget Allocator       │   │
│  │  - RAG retrieval │    │   40% Hotel              │   │
│  │  - Filter & sort │    │   25% Wisata             │   │
│  │  - Plan kuliner  │    │   25% Kuliner            │   │
│  └────────┬─────────┘    │   10% Transport          │   │
│           │              └──────────────────────────┘   │
│  ┌────────▼─────────┐                                   │
│  │  Haversine +     │                                   │
│  │  Nearest         │                                   │
│  │  Neighbor (TSP)  │                                   │
│  └──────────────────┘                                   │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   AZURE SERVICES                        │
│                                                         │
│  ┌──────────────┐ ┌──────────────────┐ ┌─────────────┐  │
│  │ Azure OpenAI │ │ Azure AI Search  │ │ Azure Maps  │  │
│  │   GPT-4o     │ │  3 Index:        │ │ Route API   │  │
│  │              │ │  - wisata-alam   │ │             │  │
│  │ - Intent     │ │  - hotel-budget  │ │ - Rute jalan│  │
│  │   extraction │ │  - kuliner-lokal │ │ - Multi-WP  │  │
│  │ - Narrative  │ │                  │ │ - OSRM FB   │  │
│  │ - Transport  │ │  Fallback: JSON  │ │             │  │
│  └──────────────┘ └──────────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline

Rencanain mengimplementasikan **Retrieval-Augmented Generation** untuk memastikan rekomendasi LLM ter-grounded ke data nyata, bukan halusinasi dari training knowledge.

### Alur RAG

```
1. RETRIEVAL — itinerary_builder.py
   ├── retrieve_for_itinerary() query Azure AI Search dengan:
   │     • Full-text search: "Alam Kuliner Lembang"
   │     • OData filter: harga_tiket le 50000 and rating ge 4.0
   │     • Order by: rating desc
   └── Hasil: kandidat wisata, hotel, kuliner

2. AUGMENTATION — grounding.py
   ├── build_context_from_itinerary()
   ├── Format context documents dari hasil retrieval
   └── Inject ke system prompt GPT-4o

3. GENERATION — openai_service.py
   ├── GPT-4o terima prompt + grounded context
   └── Output narasi yang faktual, tanpa karangan
```

### Mengapa Tidak Pakai PostgreSQL atau Vector Database?

**Azure AI Search sudah cukup** untuk use case ini karena:

| Kebutuhan | Azure AI Search |
|-----------|-----------------|
| Filter numerik (harga, rating) | OData filter `le`, `ge`, `eq` |
| Sorting dan ranking | `order_by` parameter |
| Full-text search | Built-in dengan scoring profile |
| Faceting (distribusi kategori) | Built-in |
| Semantic search | Tersedia di tier Standard ke atas |

**PostgreSQL tidak diperlukan** karena dataset bersifat statis (wisata, hotel, kuliner tidak berubah real-time), tidak ada user yang menulis data baru, dan tidak ada relasi kompleks antar tabel.

**Vector database tidak diperlukan** karena preferensi user sudah dalam bentuk kategori terstruktur (Alam, Budaya, Hiburan, Kota, Kuliner) yang dipilih dari dropdown, bukan free-text ambigu yang membutuhkan semantic similarity.

---

## Tech Stack

**Frontend dan Framework**
- [Streamlit](https://streamlit.io/) 1.45.0 — UI web app
- [Folium](https://python-visualization.github.io/folium/) dan [streamlit-folium](https://github.com/randyzwitch/streamlit-folium) — Peta interaktif

**AI dan Cloud (Microsoft Azure)**
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

## Struktur Proyek

```
app/
├── main.py                        # Entry point Streamlit
├── config.py                      # Load env variables dan Azure credentials
├── requirements.txt
├── .gitignore
│
├── components/                    # UI Components
│   ├── form_input.py              # Form 5-field input
│   ├── itinerary_card.py          # Tampilan itinerary per hari
│   ├── budget_summary.py          # Progress bar dan breakdown budget
│   ├── map_view.py                # Peta rute Folium per hari
│   └── transport_card.py          # Card rekomendasi transportasi
│
├── core/                          # Business Logic
│   ├── itinerary_builder.py       # Algoritma susun itinerary + RAG retrieval
│   ├── budget_allocator.py        # Alokasi budget 40/25/25/10
│   └── haversine.py               # Haversine + Nearest Neighbor TSP
│
├── services/                      # Azure Service Wrappers
│   ├── openai_service.py          # Azure OpenAI dengan auto-grounding
│   ├── search_service.py          # Azure AI Search dengan OData filter
│   ├── maps_service.py            # Azure Maps dengan Haversine fallback
│   └── grounding.py               # RAG pipeline dan system prompt builder
│
├── data/                          # Dataset JSON (source of truth)
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
│   ├── seed_data.py               # Validasi dan statistik dataset
│   ├── create_index.py            # Buat schema index Azure AI Search
│   ├── upload_index.py            # Upload data ke Azure AI Search
│   └── precompute_jarak.py        # Pre-compute distance matrix
│
└── tests/                         # Unit tests
    ├── test_budget_allocator.py
    ├── test_search_service.py
    └── test_grounding.py
```

---

## Instalasi dan Setup

### Prasyarat

- Python 3.10 atau lebih baru
- pip / virtualenv

### 1. Clone Repository

```bash
git clone https://github.com/iqbalrza/rencanain.git
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

> **Catatan:** Aplikasi tetap berjalan tanpa Azure credentials menggunakan mode fallback lokal (data JSON dan algoritma lokal).

---

## Konfigurasi Azure

### Azure OpenAI

1. Buat resource **Azure OpenAI** di [Azure Portal](https://portal.azure.com)
2. Deploy model **GPT-4o** pada resource tersebut
3. Salin endpoint dan API key ke `.env`

### Azure AI Search (Setup RAG)

Setup ini wajib dilakukan dalam urutan yang benar. Tanpa schema yang tepat, OData filter (`harga_tiket le 50000`) akan gagal karena field dianggap sebagai string.

**Langkah 1 — Buat resource Azure AI Search**

Buat resource baru di Azure Portal (Free tier cukup untuk development).

**Langkah 2 — Buat schema index**

```bash
cd app
python scripts/create_index.py
```

Script ini akan membuat 3 index dengan schema lengkap:
- `wisata-alam` dengan field `harga_tiket` (Int32), `rating` (Double), `tags` (Collection)
- `hotel-budget` dengan field `harga_per_malam` (Int32), `fasilitas` (Collection)
- `kuliner-lokal` dengan field `harga_per_orang` (Int32)

**Langkah 3 — Upload data ke index**

```bash
python scripts/upload_index.py
```

Script ini akan meng-upload semua dokumen dari `data/*.json` ke Azure Search.

### Azure Maps

1. Buat resource **Azure Maps Account**
2. Salin subscription key ke `.env`
3. Digunakan untuk rute jalan sesungguhnya, fallback ke OSRM jika tidak tersedia

---

## Menjalankan Aplikasi

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

## Dataset

Dataset tersimpan dalam format JSON di folder `app/data/` sebagai **source of truth**, kemudian di-upload ke Azure AI Search untuk keperluan RAG retrieval.

| File | Jumlah | Keterangan |
|------|--------|------------|
| `wisata.json` | 50+ entri | Destinasi wisata Bandung dan sekitar (Alam, Budaya, Hiburan, Kota) |
| `hotel.json` | 20 entri | Hotel Budget (Rp 120rb-350rb), Mid-Range (Rp 480rb-650rb), Premium (Rp 1.1jt+) |
| `kuliner.json` | 50 entri | Rumah makan Sunda, kafe, jajanan, restoran viral 2025-2026 |

Setiap entri memiliki koordinat GPS (`lat`, `lng`) untuk keperluan peta dan kalkulasi rute.

### Validasi Dataset

```bash
cd app
python scripts/seed_data.py
```

---

## API Services

### `search_service.py` (RAG Entry Point)

| Fungsi | Deskripsi |
|--------|-----------|
| `search_wisata(query, top, max_harga_tiket, kategori, min_rating)` | Cari destinasi wisata dengan OData filter |
| `search_hotel(query, top, max_harga_malam, kategori, min_rating)` | Cari hotel dengan filter budget |
| `search_kuliner(query, top, max_harga_orang, kategori, min_rating)` | Cari kuliner dengan filter harga |
| `search_all(query, top_per_category)` | Cari di semua 3 index sekaligus |
| `retrieve_for_itinerary(...)` | Bridge function untuk itinerary builder, retrieve semua kandidat sekaligus |

### `openai_service.py`

| Fungsi | Deskripsi |
|--------|-----------|
| `extract_intent(form_data)` | Parse input form menjadi structured query untuk retrieval |
| `generate_narrative(itinerary_data)` | Generate narasi perjalanan dengan auto-grounding dari Azure Search |
| `generate_transport_recommendation(kota_asal, jumlah_orang, budget)` | Rekomendasi moda transportasi via LLM |

### `grounding.py`

| Fungsi | Deskripsi |
|--------|-----------|
| `build_context_from_itinerary(itinerary_data)` | Build context documents dari itinerary terpilih dengan retrieve detail dari Azure Search |
| `build_context_documents(intent, form_data)` | Build context dari intent + form data (pre-generation) |
| `build_system_prompt(context_docs)` | Build system prompt anti-halusinasi dengan grounding strategy |

### `maps_service.py`

| Fungsi | Deskripsi |
|--------|-----------|
| `optimize_route(destinations, start_lat, start_lng)` | Optimasi urutan kunjungan |
| `get_distance_between(lat1, lng1, lat2, lng2)` | Jarak antara dua titik |

---

## Testing

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

## Deployment

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

## Alur Kerja Aplikasi

```
User mengisi form (kota asal, durasi, jumlah orang, budget, preferensi)
        │
        ▼
build_itinerary() — Core algorithm
  ├── allocate_budget() → 40/25/25/10
  ├── retrieve_for_itinerary() → Azure AI Search (RAG)
  │     ├── search_wisata + filter budget
  │     ├── search_hotel + filter kategori
  │     └── search_kuliner + filter harga
  ├── nearest_neighbor_route() → optimasi TSP
  ├── select_hotel() → pilih hotel dari kandidat retrieval
  └── susun kuliner per waktu makan
        │
        ▼
generate_transport_recommendation() — Azure OpenAI
        │
        ▼
generate_narrative() — Azure OpenAI dengan grounding context
        │
        ▼
Render UI:
  ├── Tab 1: Itinerary card + transport card + narasi
  ├── Tab 2: Peta rute Folium (Azure Maps / OSRM / straight line)
  └── Tab 3: Budget summary + breakdown per kategori
```

---

## Lisensi

Proyek ini dibuat untuk keperluan **Microsoft Elevate Hackathon 2025** di Dicoding. Bebas digunakan untuk tujuan edukasi dan non-komersial.

---

## Author

Dibuat untuk Microsoft Elevate Hackathon 2025.

**Powered by:**
- Azure OpenAI (GPT-4o)
- Azure AI Search
- Azure Maps
- Streamlit