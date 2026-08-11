# CHANGELOG — day13-k3-monitoring-llmops

> Mục mới nhất lên đầu. Mỗi entry ghi: Lỗi/Thay đổi | Nguyên nhân gốc | Giải pháp.

| Ngày | Thay đổi | Nguyên nhân | Giải pháp |
|------|----------|-------------|-----------|
| 2026-08-11 | Deploy toàn bộ hệ thống LLMOps Monitoring: gộp 4 module thành unified FastAPI app trên Render + Jaeger UI trên Railway | Cần môi trường production demo trực quan cho 4 kỹ thuật Monitoring/Observability (Langfuse, OpenTelemetry, PII Scrubbing, Structured Logging) | Tạo `app.py`, `render.yaml`, deploy Web Service lên Render; deploy Jaeger Docker container lên Railway với OTLP TCP Proxy trỏ dữ liệu từ Render sang Railway Jaeger |
| 2026-08-10 | Khởi tạo repo với 5 module demo: Trace theory, Structured Logging, PII Scrubbing, OpenTelemetry+Jaeger, Langfuse | Lab material cho Day 13 — K3 Monitoring & LLMOps | Tạo repo + commit đầu tiên `46ace67` |
| 2026-08-10 | Full repo upgrade: thêm docs/, LICENSE, community health files, docker-compose, restructure | Repo thiếu docs chuẩn theo AI Repo Rules | Tạo đầy đủ CHANGELOG, JOURNAL, ARCHITECTURE, LICENSE, CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, docker-compose.yml, upgrade README |
