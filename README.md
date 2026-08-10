# LLMOps Monitoring & Observability

[![License](https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-informational?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-informational?style=flat-square)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-informational?style=flat-square)
![Langfuse](https://img.shields.io/badge/Langfuse-informational?style=flat-square)

Tài liệu và code demo các kỹ thuật **Monitoring, Observability** cho hệ thống AI Agent / LLM trong production. Lab material cho **Day 13 — K3**.

## Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────┐
│                   LLMOps Monitoring Lab                     │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  Trace   │Structured│   PII    │  OTEL +  │    Langfuse     │
│  Theory  │ Logging  │Scrubbing │  Jaeger  │  Integration    │
│ (docs)   │(structlog│(Regex +  │(FastAPI +│ (FastAPI +      │
│          │+context) │Presidio) │ OTLP)    │  @observe)      │
└──────────┴──────────┴──────────┴────┬─────┴───────┬─────────┘
                                      │             │
                                      ▼             ▼
                                 ┌─────────┐  ┌──────────┐
                                 │ Jaeger  │  │ Langfuse │
                                 │ (Docker)│  │ (Cloud)  │
                                 └─────────┘  └──────────┘
```

## Cấu trúc dự án

```
.
├── trace.md                    # Lý thuyết Trace, Span, Waterfall
├── structured-logs.py          # Structured Logging (structlog + contextvars)
├── pii-scrubbing.py            # PII Scrubbing (Regex + Microsoft Presidio)
├── opentelemetry/              # OpenTelemetry Tracing + Jaeger visualization
│   ├── otel_demo.py            #   FastAPI app + OTEL SDK + GenAI conventions
│   ├── requirements.txt
│   └── README.md
├── langfuse/                   # Langfuse LLM Observability platform
│   ├── langfuse-integration.py #   FastAPI app + @observe decorator
│   ├── requirements.txt
│   └── README.md
├── docker-compose.yml          # Jaeger infrastructure (Docker)
├── requirements.txt            # Dependencies gộp toàn repo
├── docs/
│   ├── CHANGELOG.md            # Log thay đổi
│   ├── JOURNAL.md              # Nhật ký bàn giao multi-agent
│   └── ARCHITECTURE.md         # Kiến trúc chi tiết
├── LICENSE                     # Apache-2.0
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
└── SECURITY.md
```

## Nội dung chính

### 1. Trace & Span (`trace.md`)

Giải thích khái niệm Trace, Span, Waterfall View trong ngữ cảnh AI Agent — cách một request đi qua các bước Guardrail → RAG → LLM → Tool Call → Answer và cách dùng trace để debug bottleneck, hallucination, cost.

### 2. Structured Logging (`structured-logs.py`)

Demo Python `structlog` với JSON output chuẩn:
- Cấu hình processors (log level, timestamp ISO 8601, exception formatting)
- `contextvars` để tự động gắn `correlation_id`, `user_id` xuyên suốt async call chain
- Mô phỏng multi-request đồng thời

```bash
pip install structlog
python structured-logs.py
```

### 3. PII Scrubbing (`pii-scrubbing.py`)

Hybrid pipeline lọc dữ liệu cá nhân (PII) trước khi log/trace:
- **Regex** — xử lý nhanh các mẫu cố định (SĐT, Email, CCCD, thẻ tín dụng)
- **Microsoft Presidio (NLP/NER)** — nhận diện ngữ cảnh sâu (tên người, địa chỉ)

```bash
pip install presidio-analyzer presidio-anonymizer spacy
python -m spacy download en_core_web_lg
python pii-scrubbing.py
```

### 4. OpenTelemetry + Jaeger (`opentelemetry/`)

Distributed tracing với OpenTelemetry SDK, FastAPI auto-instrumentation, và Jaeger UI để visualize trace waterfall.

```bash
# Khởi chạy Jaeger
docker compose up -d jaeger

# Chạy demo
cd opentelemetry
pip install -r requirements.txt
python otel_demo.py

# Mở Jaeger UI: http://localhost:16686
```

Xem chi tiết tại [opentelemetry/README.md](opentelemetry/README.md).

### 5. Langfuse Integration (`langfuse/`)

LLM Observability với Langfuse — decorator-based tracing (`@observe`), tự động track token usage, cost, và hiển thị trace trên Langfuse Cloud UI.

```bash
cd langfuse
cp .env.example .env   # Điền Langfuse API keys
pip install -r requirements.txt
python langfuse-integration.py

# Mở Langfuse UI: https://us.cloud.langfuse.com → Traces
```

Xem chi tiết tại [langfuse/README.md](langfuse/README.md).

## Cài đặt nhanh (toàn bộ)

```bash
# 1. Clone repo
git clone https://github.com/nhmanhDev/day13-k3-monitoring-llmops.git
cd day13-k3-monitoring-llmops

# 2. Tạo virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# 3. Cài tất cả dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_lg

# 4. (Tùy chọn) Khởi chạy Jaeger cho module OpenTelemetry
docker compose up -d jaeger
```

## Tài liệu

| File | Nội dung |
|------|----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Kiến trúc chi tiết 5 module |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Log thay đổi |
| [docs/JOURNAL.md](docs/JOURNAL.md) | Nhật ký bàn giao multi-agent |

## Đóng góp & bảo mật

- Đóng góp: [CONTRIBUTING.md](CONTRIBUTING.md)
- Báo lỗi bảo mật: [SECURITY.md](SECURITY.md)

## License

Phát hành theo [Apache-2.0](LICENSE).
