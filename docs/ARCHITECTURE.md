# Kiến trúc — LLMOps Monitoring & Observability

> Ảnh chụp HIỆN TẠI. Sửa đè tại chỗ khi đổi, KHÔNG append theo ngày.

## Tổng quan

Repo gồm **5 module độc lập**, mỗi module demo 1 kỹ thuật Monitoring/Observability cho hệ thống AI Agent/LLM trong production. Không có shared state hay dependency chéo giữa các module.

```
┌─────────────────────────────────────────────────────────────┐
│                   LLMOps Monitoring Lab                     │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│  Trace   │Structured│   PII    │  OTEL +  │    Langfuse     │
│  Theory  │ Logging  │Scrubbing │  Jaeger  │  Integration    │
│ (docs)   │(structlog│(Regex +  │(FastAPI +│ (FastAPI +      │
│          │+context) │Presidio) │ OTLP)    │  @observe)      │
├──────────┼──────────┼──────────┼──────────┼─────────────────┤
│ trace.md │structured│   pii-   │opentel-  │   langfuse/     │
│          │-logs.py  │scrubbing │emetry/   │                 │
│          │          │  .py     │          │                 │
└──────────┴──────────┴──────────┴──────────┴─────────────────┘
                                      │              │
                                      ▼              ▼
                                 ┌─────────┐   ┌──────────┐
                                 │ Jaeger  │   │ Langfuse │
                                 │ (Docker)│   │ (Cloud)  │
                                 └─────────┘   └──────────┘
```

## Module chi tiết

### 1. Trace & Span Theory (`trace.md`)
- **Loại**: Tài liệu thuần (Markdown + Mermaid diagrams)
- **Nội dung**: Kịch bản AI Agent CSKH → trace hierarchy → waterfall → payload → giá trị thực tế (bottleneck, hallucination debug, cost tracking)
- **Không có code chạy**

### 2. Structured Logging (`structured-logs.py`)
- **Stack**: Python `structlog` + `contextvars`
- **Luồng**: Cấu hình processors (log level, ISO 8601 timestamp, JSON renderer) → bind `correlation_id` + `user_id` qua `contextvars` → log tự động kế thừa context xuyên suốt async call chain
- **Demo**: 2 mock requests chạy đồng thời, mỗi request có correlation_id riêng

### 3. PII Scrubbing (`pii-scrubbing.py`)
- **Stack**: Python `re` (Regex) + Microsoft `presidio-analyzer` + `presidio-anonymizer` + `spacy`
- **Luồng (Hybrid Pipeline)**:
  1. **Regex pass** — lọc nhanh SĐT VN, Email, CCCD 12 số, thẻ tín dụng
  2. **Presidio NER pass** — nhận diện ngữ cảnh sâu: tên người, địa chỉ, email bị sót
- **Output**: Text đã anonymize (`[REDACTED_*]`, `<PERSON>`)

### 4. OpenTelemetry + Jaeger (`opentelemetry/`)
- **Stack**: `opentelemetry-sdk` + `opentelemetry-exporter-otlp` + `FastAPIInstrumentor` + Jaeger (Docker)
- **Luồng**:
  1. Cấu hình `TracerProvider` + `Resource` (service name/version/env)
  2. Export span qua OTLP gRPC → Jaeger collector (port 4317)
  3. FastAPI auto-instrumentation tạo root span cho mỗi HTTP request
  4. Manual span: `tool.execute` (weather API) + `llm.generate` (GenAI semantic conventions)
- **Visualization**: Jaeger UI tại `localhost:16686`

### 5. Langfuse Integration (`langfuse/`)
- **Stack**: `langfuse` SDK + FastAPI + `python-dotenv`
- **Luồng**:
  1. `@observe` decorator tự động tạo span/trace
  2. `@observe(as_type="generation")` đánh dấu LLM call → Langfuse auto-track token/cost
  3. `get_client().update_current_span/generation()` bổ sung metadata
- **Visualization**: Langfuse Cloud UI

## Thư mục quan trọng

| Thư mục/File | Vai trò |
|---|---|
| `docs/` | Tài liệu dự án: CHANGELOG, JOURNAL, ARCHITECTURE |
| `opentelemetry/` | Module OTEL + Jaeger demo |
| `langfuse/` | Module Langfuse demo |
| `docker-compose.yml` | Jaeger infrastructure |
| `requirements.txt` | Dependencies gộp toàn repo |

## Dependency ngoài

| Service | Cách chạy | Dùng bởi |
|---------|-----------|----------|
| **Jaeger** | `docker compose up -d jaeger` | Module OpenTelemetry |
| **Langfuse Cloud** | Đăng ký tại cloud.langfuse.com, lấy API key | Module Langfuse |
| **spaCy model `en_core_web_lg`** | `python -m spacy download en_core_web_lg` | Module PII Scrubbing |
