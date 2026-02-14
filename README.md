# ⚡ FastAPI Expert Assistant

> **Multi-agent RAG sistemi** — FastAPI sorularını resmi dokümantasyon, web araması ve LLM ile yanıtlayan, Streamlit tabanlı interaktif asistan.

---

## 📋 İçindekiler

- [Proje Hakkında](#proje-hakkında)
- [Mimari](#mimari)
- [Teknoloji Yığını](#teknoloji-yığını)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Proje Yapısı](#proje-yapısı)
- [Agent'lar](#agentlar)
- [Servisler ve Araçlar](#servisler-ve-araçlar)
- [Konfigürasyon](#konfigürasyon)
- [API Referansı](#api-referansı)


---

## Proje Hakkında

FastAPI Expert Assistant, kullanıcıların FastAPI framework'ü hakkındaki sorularını yanıtlamak için tasarlanmış **çok ajanlı bir RAG (Retrieval-Augmented Generation) sistemidir**. Sistem; yerel dokümantasyon tabanından bilgi çeker, web üzerinde güncel örnek arar ve LLM aracılığıyla açıklama + kod üretir.

### Desteklenen Konular

| Konu | Açıklama |
|------|----------|
| **REST API** | Route tanımlama, path/query parametreler, Pydantic modelleri |
| **WebSocket** | Gerçek zamanlı çift yönlü iletişim |
| **Auth (OAuth2/JWT)** | Token tabanlı kimlik doğrulama akışları |
| **Dependencies** | `Depends()` ile dependency injection |
| **Middleware** | İstek/yanıt pipeline yönetimi |
| **Background Tasks** | Asenkron arka plan işlemleri |
| **Testing** | pytest ile FastAPI test stratejileri |
| **Deployment** | Docker, Gunicorn, Kubernetes |

---

## Mimari

```
Kullanıcı Sorusu (Streamlit UI)
         │
         ▼
    FastAPI Backend (/api/v1/ask)
         │
         ▼
  AgentOrchestrator (workflow.py)
         │
    ┌────┴─────────────────────────┐
    │                              │
    ▼                              │
Agent 1: QueryAnalyzer         (seri)
    │ → language, framework,       │
    │   topic, keywords            │
    │                              │
    ▼                              │
    ┌──────────┬──────────┐        │
    │          │          │        │
    ▼          ▼       (paralel)   │
Agent 2:   Agent 3:               │
DocReader  ExampleFinder          │
(RAG/FAISS) (DuckDuckGo)         │
    │          │                   │
    └────┬─────┘                   │
         │                         │
         ▼                         │
  Tools: CodeValidator +           │
         ComplexityAnalyzer        │
         │                         │
         ▼                         │
Agent 4: CodeExplainer            │
(explanation + code + line-by-line │
 + best practices + sources)       │
         │                         │
         ▼                         │
   Streamlit UI (Yanıt Gösterimi) ◄┘
```

### Akış Özeti

1. **QueryAnalyzer** — Soruyu parse eder; dil, framework, konu ve anahtar kelimeleri çıkarır.
2. **DocumentationReader** (paralel) — FAISS index üzerinden yerel FastAPI dokümanlarından ilgili chunk'ları getirir.
3. **ExampleFinderAgent** (paralel) — DuckDuckGo ile GitHub örnekleri arar.
4. **CodeValidator + ComplexityAnalyzer** — Bulunan kod örneklerini doğrular ve karmaşıklık analizi yapar.
5. **CodeExplainer** — Tüm bağlamı birleştirerek açıklama, çalışan kod, satır satır yorum ve best practice üretir.

---

## Kullanılan Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI + Uvicorn |
| **LLM** | Ollama (yerel, multi-model) |
| **Embedding** | SentenceTransformers |
| **Vektör DB** | FAISS (IndexFlatL2) |
| **Web Arama** | DuckDuckGo Search (`duckduckgo-search`) |
| **Kod Analiz** | AST (stdlib) + Radon (cyclomatic complexity) |
| **Data Validation** | Pydantic v2 |
| **Async** | Python asyncio |

---

## Kurulum

### Gereksinimler

- Python 3.10+
- [Ollama](https://ollama.ai) kurulu ve çalışıyor olmalı
- `pip` veya `uv`

### 1. Repoyu Klonla

```bash
git clone https://github.com/kullanici/fastapi-expert-assistant.git
cd fastapi-expert-assistant
```

### 2. Sanal Ortam ve Bağımlılıklar

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Ollama Modelleri İndir

```bash
# Hızlı görevler için (QueryAnalyzer, ExampleFinder)
ollama pull llama3.2:1b

# Derin akıl yürütme için (CodeExplainer, DocumentationReader)
ollama pull llama3.1:8b
```

### 4. Ortam Değişkenlerini Ayarla

`.env` dosyası oluştur (veya `app/config.py`'yi düzenle):

```env
APP_NAME=FastAPI Expert Assistant
APP_VERSION=1.0.0
API_PREFIX=/api/v1

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
FAST_MODEL=llama3.2:1b
POWERFUL_MODEL=llama3.1:8b
TEMPERATURE=0.1
MAX_TOKENS=2048
OLLAMA_TIMEOUT=480

# RAG
DOCUMENTS_PATH=data/documents
VECTOR_DB_PATH=data/vector_db
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=3
```

### 5. Dokümanları Ekle

`data/documents/` dizinine FastAPI resmi dokümanlarının `.md` veya `.txt` versiyonlarını koy. İlk başlatmada FAISS index otomatik oluşturulur.

### 6. Servisleri Başlat

```bash
# Terminal 1: Backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
streamlit run app.py
```

Tarayıcıda `http://localhost:8501` adresini aç.

---

## Kullanım

Streamlit arayüzünde soru yaz ve **🚀 Ask** butonuna bas:

```
"How do Dependencies work in FastAPI?"
"OAuth2 JWT authentication flow in FastAPI?"
"How to implement WebSocket with connection manager?"
"FastAPI middleware examples"
```

### Yanıt Bileşenleri

| Bölüm | İçerik |
|-------|--------|
| **📖 Explanation** | Kavramın 2-3 cümlelik açıklaması |
| **💻 Code Example** | Çalıştırılabilir, kopyalanabilir Python kodu |
| **🔍 Line by Line** | Kodun satır satır açıklaması |
| **✅ Best Practices** | Konuyla ilgili en iyi pratikler |
| **🔗 Sources** | Kullanılan web kaynakları |

---

## Proje Yapısı

```
fastapi-expert-assistant/
│
├── app.py                      # Streamlit frontend
│
├── app/
│   ├── main.py                 # FastAPI uygulama fabrikası
│   ├── config.py               # Ayarlar (Settings)
│   ├── deps.py                 # Orchestrator bağımlılık kurulumu
│   │
│   ├── api/
│   │   └── routes.py           # /ask ve /health endpoint'leri
│   │
│   ├── models/
│   │   └── schemas.py          # Pydantic modelleri (tüm agent kontratları)
│   │
│   ├── agents/
│   │   ├── base_agent.py       # Soyut temel agent sınıfı
│   │   ├── query_analyzer.py   # Agent 1: Soru analizi
│   │   ├── documentation_reader.py  # Agent 2: RAG / yerel doküman
│   │   ├── example_finder.py   # Agent 3: Web arama
│   │   └── code_explainer.py   # Agent 4: Kod açıklama ve sentez
│   │
│   ├── services/
│   │   ├── llm_service.py      # Ollama LLM sarmalayıcı
│   │   ├── rag_service.py      # FAISS tabanlı RAG servisi
│   │   ├── document_service.py # Doküman okuma ve chunk'lama
│   │   └── model_selector.py   # Görev bazlı model yönlendirme
│   │
│   ├── tools/
│   │   ├── code_validator.py   # AST tabanlı Python sözdizim doğrulama
│   │   ├── complexity_analyzer.py  # Radon cyclomatic complexity
│   │   └── web_search.py       # DuckDuckGo arama sarmalayıcı
│   │
│   └── orchestrator/
│       └── workflow.py         # AgentOrchestrator (tam iş akışı)
│
├── data/
│   ├── documents/              # FastAPI .md / .txt dokümanları (RAG için)
│   └── vector_db/              # FAISS index (otomatik oluşturulur)
│       ├── faiss.index
│       └── chunks.npy
│
├── assets/
│   └── company_logo.jpg        # Opsiyonel logo
│
├── requirements.txt
└── README.md
```

---

## Agent'lar

### Agent 1 — QueryAnalyzer

**Dosya:** `app/agents/query_analyzer.py`

Kullanıcı sorusunu LLM ile parse eder ve yapılandırılmış metadata çıkarır.

**Çıktı (QueryAnalysis):**

```json
{
  "language": "python",
  "framework": "fastapi",
  "topic": "dependency_injection",
  "subtopic": null,
  "keywords": ["fastapi", "depends", "dependency", "injection"]
}
```

**Özellikler:**
- LLM başarısız olursa regex/heuristic fallback devreye girer
- `_TOPIC_ALIASES` ile normalize edilmiş topic isimleri
- `framework|topic|...` gibi multi-value çıktılar güvenli şekilde temizlenir

---

### Agent 2 — DocumentationReader

**Dosya:** `app/agents/documentation_reader.py`

FAISS vektör veritabanı üzerinden yerel FastAPI dokümanlarında semantic arama yapar.

**Çıktı (DocumentationResult):**

```json
{
  "snippets": [
    {"source": "dependencies.md", "text": "...", "relevance": 0.87}
  ],
  "meta": {"query": "fastapi depends", "top_k": 3, "source": "faiss"}
}
```

---

### Agent 3 — ExampleFinder

**Dosya:** `app/agents/example_finder.py`

DuckDuckGo ile GitHub kod örnekleri arar. Kod sinyali (`def`, `import`, `@app.` vb.) içeren snippet'leri önceliklendirir.

**Çıktı (ExampleFinderResult):**

```json
{
  "results": [{"title": "...", "url": "https://...", "snippet": "..."}],
  "code_example": "from fastapi import ...",
  "meta": {"query": "fastapi dependency injection github example", "provider": "duckduckgo"}
}
```

---

### Agent 4 — CodeExplainer

**Dosya:** `app/agents/code_explainer.py`

Tüm bağlamı (doc snippets + web results + validation + complexity) alıp final yanıtı üretir. Üç aşamalı JSON onarım mekanizması içerir.

**Çıktı (FinalAnswer):**

```json
{
  "explanation": "Dependency Injection ...",
  "code_example": "from fastapi import FastAPI, Depends\n...",
  "line_by_line": ["Line 1 creates the app instance ...", "..."],
  "best_practices": ["Always use type hints ...", "..."],
  "sources": ["https://fastapi.tiangolo.com/tutorial/dependencies/"],
  "meta": {"framework": "fastapi", "topic": "dependency_injection"}
}
```

---

## Servisler ve Araçlar

### LLMService

Ollama HTTP API'sine istek gönderen sarmalayıcı. `ModelSelector` ile entegre çalışır.

```python
llm.generate(prompt, model="llama3.1:8b", temperature=0.1)
```

### ModelSelector

Görev tipine ve girdi uzunluğuna göre hızlı/güçlü model seçer:

| Durum | Model |
|-------|-------|
| `reasoning_depth == "deep"` | `POWERFUL_MODEL` |
| `task_type in {explain, synthesize, write}` | `POWERFUL_MODEL` |
| `input_length >= 1200` | `POWERFUL_MODEL` |
| Diğer | `FAST_MODEL` |

### RAGService

FAISS `IndexFlatL2` ile embedding tabanlı chunk arama. Index disk'e kaydedilir, sonraki başlatmalarda yeniden yüklenir.

### DocumentService

`.md` ve `.txt` dosyalarını okur, Markdown syntax'ını temizler ve configurable overlap'li chunk'lara böler.

### CodeValidatorTool

Python AST ile sözdizim doğrulama. Hata varsa satır ve offset numarasını döndürür.

### ComplexityAnalyzerTool

Radon ile cyclomatic complexity hesaplama. Radon kurulu değilse `available: false` döndürür ve sistem çalışmaya devam eder.

### WebSearchTool

DuckDuckGo `lite` backend ile arama, exponential backoff ile rate-limit koruması (3 deneme: 1s, 2s, 4s).

---

## Konfigürasyon

Tüm ayarlar `app/config.py` içindeki `Settings` sınıfındadır. Ortam değişkenleri veya `.env` dosyası ile override edilebilir.

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama sunucu adresi |
| `OLLAMA_MODEL` | `llama3.1:8b` | Varsayılan model |
| `FAST_MODEL` | `llama3.2:1b` | Sınıflandırma/hızlı görevler |
| `POWERFUL_MODEL` | `llama3.1:8b` | Açıklama/derin akıl yürütme |
| `TEMPERATURE` | `0.1` | LLM sıcaklığı |
| `MAX_TOKENS` | `2048` | Maksimum token sayısı |
| `OLLAMA_TIMEOUT` | `480` | İstek zaman aşımı (saniye) |
| `DOCUMENTS_PATH` | `data/documents` | Doküman dizini |
| `VECTOR_DB_PATH` | `data/vector_db` | FAISS index dizini |
| `CHUNK_SIZE` | `500` | Chunk boyutu (karakter) |
| `CHUNK_OVERLAP` | `50` | Chunk overlap (karakter) |
| `TOP_K_RESULTS` | `3` | RAG'dan dönecek chunk sayısı |

---

## API Referansı

### `POST /api/v1/ask`

Kullanıcı sorusunu işler ve yanıt döndürür.

**Request:**
```json
{
  "query": "How do WebSockets work in FastAPI?"
}
```

**Response:**
```json
{
  "explanation": "WebSocket...",
  "code_example": "from fastapi import FastAPI, WebSocket...",
  "line_by_line": ["Creates the app instance...", "..."],
  "best_practices": ["Handle disconnects gracefully...", "..."],
  "sources": ["https://fastapi.tiangolo.com/advanced/websockets/"],
  "meta": {
    "framework": "fastapi",
    "topic": "websocket"
  }
}
```

### `GET /api/v1/health`

Servis sağlık kontrolü.

```json
{"status": "ok"}
```

---

