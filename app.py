"""
LLMOps Monitoring & Observability — Unified Demo API
=====================================================
Gộp 4 module demo thành 1 FastAPI app duy nhất:
  1. POST /chat/langfuse   — LLM Observability với Langfuse (@observe decorator)
  2. POST /chat/otel       — Distributed Tracing với OpenTelemetry
  3. POST /scrub-pii       — PII Scrubbing (Regex + Microsoft Presidio)
  4. POST /structured-log  — Structured Logging (structlog + contextvars)

Deploy: Render Web Service (Free tier)
"""

import asyncio
import logging
import os
import re
import time
import uuid
from typing import Any, Dict

import structlog
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

load_dotenv()

# =============================================================================
# STRUCTLOG — Setup chuẩn JSON output
# =============================================================================
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    cache_logger_on_first_use=True,
)
struct_logger = structlog.get_logger()

# =============================================================================
# OPENTELEMETRY — Setup (export ra console vì không có Jaeger trên Render)
# =============================================================================
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode

resource = Resource.create({
    "service.name": "llmops-unified-demo",
    "service.version": "1.0.0",
    "deployment.environment": os.getenv("APP_ENV", "production"),
})

provider = TracerProvider(resource=resource)
# Console exporter — trace xuất ra Render Logs (thay vì Jaeger localhost)
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("ai.agent.tracer")

# =============================================================================
# LANGFUSE — Import (dùng env vars LANGFUSE_PUBLIC_KEY, SECRET_KEY, BASE_URL)
# =============================================================================
from langfuse import observe, get_client

# =============================================================================
# PII SCRUBBER — Hybrid Regex + Presidio
# =============================================================================
# Presidio cần download spaCy model lúc build → nặng.
# Trên Render free tier em dùng regex-only để tránh timeout build.
# Nếu cần Presidio, bật enable_presidio=True và thêm spacy vào build command.

PII_REGEX_PATTERNS: Dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    "phone_vn": r"(\+84|0)\d{9,10}",
    "cccd": r"\b\d{12}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
}


def scrub_pii_regex(text: str) -> str:
    """Lọc PII bằng Regex — nhanh, xử lý các mẫu cố định."""
    for pattern_name, pattern_regex in PII_REGEX_PATTERNS.items():
        replacement = f"[REDACTED_{pattern_name.upper()}]"
        text = re.sub(pattern_regex, replacement, text)
    return text


# =============================================================================
# FASTAPI APP
# =============================================================================
app = FastAPI(
    title="LLMOps Monitoring & Observability Demo",
    description=(
        "Unified API demo 4 kỹ thuật monitoring cho LLM/AI Agent: "
        "Langfuse, OpenTelemetry, PII Scrubbing, Structured Logging."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Health Check ----------
@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "llmops-unified-demo",
        "modules": [
            "POST /chat/langfuse — Langfuse LLM Observability",
            "POST /chat/otel — OpenTelemetry Distributed Tracing",
            "POST /scrub-pii — PII Scrubbing (Regex)",
            "POST /structured-log — Structured Logging (structlog)",
        ],
    }


# =============================================================================
# MODULE 1: LANGFUSE INTEGRATION
# =============================================================================
@observe(name="tool_execution")
def langfuse_tool_call(location: str):
    """Simulate tool call — auto-traced by @observe."""
    time.sleep(0.05)
    result = {"location": location, "temperature": "28C", "condition": "Sunny"}
    get_client().update_current_span(
        metadata={"tool_name": "get_weather", "input_location": location},
        output=result,
    )
    return result


@observe(as_type="generation", name="llm_generation")
def langfuse_llm_call(prompt: str, model_name: str = "claude-3-5-sonnet"):
    """Simulate LLM call — auto-traced as 'generation' by Langfuse."""
    time.sleep(0.1)
    response_text = "Thời tiết tại Hà Nội hôm nay rất đẹp, 28°C và có nắng."
    get_client().update_current_generation(
        model=model_name,
        input=prompt,
        output=response_text,
        usage_details={"input": 150, "output": 45, "total": 195},
        metadata={"temperature": 0.7, "provider": "anthropic"},
    )
    return response_text


@observe(name="chat_agent_endpoint")
async def langfuse_handle_chat(user_query: str, user_id: str):
    tool_data = langfuse_tool_call(location="Hanoi")
    final_prompt = f"User query: {user_query}. Context: {tool_data}"
    response = langfuse_llm_call(prompt=final_prompt)
    return response


@app.post("/chat/langfuse")
async def chat_langfuse(request: Request):
    """Demo Langfuse LLM Observability — trace hiện trên Langfuse Cloud UI."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    user_query = data.get("query", "Thời tiết Hà Nội thế nào?")
    user_id = data.get("user_id", "u_demo")

    response = await langfuse_handle_chat(user_query=user_query, user_id=user_id)
    return {"status": "success", "module": "langfuse", "response": response}


# =============================================================================
# MODULE 2: OPENTELEMETRY
# =============================================================================
def otel_tool_call(location: str):
    with tracer.start_as_current_span("tool.execute") as span:
        span.set_attribute("tool.name", "get_weather")
        span.set_attribute("tool.args.location", location)
        time.sleep(0.05)
        result = {"location": location, "temperature": "28C", "condition": "Sunny"}
        span.set_attribute("tool.result", str(result))
        return result


def otel_llm_call(prompt: str, model_name: str = "claude-3-5-sonnet"):
    with tracer.start_as_current_span("llm.generate") as span:
        span.set_attribute("gen_ai.system", "anthropic")
        span.set_attribute("gen_ai.request.model", model_name)
        span.set_attribute("gen_ai.request.temperature", 0.7)
        span.set_attribute("gen_ai.prompt", prompt)
        time.sleep(0.1)
        response_text = "Thời tiết tại Hà Nội hôm nay rất đẹp, 28°C và có nắng."
        span.set_attribute("gen_ai.completion", response_text)
        span.set_attribute("gen_ai.usage.input_tokens", 150)
        span.set_attribute("gen_ai.usage.output_tokens", 45)
        span.set_attribute("gen_ai.usage.total_tokens", 195)
        span.set_status(Status(StatusCode.OK))
        return response_text


@app.post("/chat/otel")
async def chat_otel(request: Request):
    """Demo OpenTelemetry Tracing — trace xuất ra Render Logs (console)."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    user_query = data.get("query", "Thời tiết Hà Nội thế nào?")

    current_span = trace.get_current_span()
    current_span.set_attribute("user.query", user_query)

    tool_data = otel_tool_call(location="Hanoi")
    final_prompt = f"User query: {user_query}. Context: {tool_data}"
    response = otel_llm_call(prompt=final_prompt)

    return {"status": "success", "module": "opentelemetry", "response": response}


# =============================================================================
# MODULE 3: PII SCRUBBING
# =============================================================================
@app.post("/scrub-pii")
async def scrub_pii(request: Request):
    """Demo PII Scrubbing — gửi text chứa thông tin nhạy cảm, trả về text đã che."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    raw_text = data.get(
        "text",
        "Xin chào, email tôi là johndoe@example.com, SĐT 0912345678, "
        "CCCD 001092001234, thẻ 4532-1111-2222-3333.",
    )

    scrubbed = scrub_pii_regex(raw_text)
    return {
        "status": "success",
        "module": "pii_scrubbing",
        "original": raw_text,
        "scrubbed": scrubbed,
    }


# =============================================================================
# MODULE 4: STRUCTURED LOGGING
# =============================================================================
@app.post("/structured-log")
async def structured_log(request: Request):
    """Demo Structured Logging — xem JSON log chuẩn trong Render Logs."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    user_id = data.get("user_id", "u_demo")
    query = data.get("query", "Tóm tắt tài liệu này")

    # Clear + bind context (giống production: correlation_id tự động)
    clear_contextvars()
    correlation_id = str(uuid.uuid4())[:8]
    bind_contextvars(
        correlation_id=correlation_id,
        user_id=user_id,
        feature="structured_log_demo",
    )

    struct_logger.info("request_received", query_len=len(query))

    start_time = time.time()
    # Simulate RAG pipeline
    struct_logger.info("retrieving_documents", vector_db="pinecone", top_k=3)
    await asyncio.sleep(0.05)
    struct_logger.info("llm_call_started", model="claude-sonnet-4-5")
    await asyncio.sleep(0.1)

    latency_ms = int((time.time() - start_time) * 1000)
    struct_logger.info("response_sent", latency_ms=latency_ms, status="success")

    return {
        "status": "success",
        "module": "structured_logging",
        "correlation_id": correlation_id,
        "message": f"Check Render Logs để xem JSON structured logs với correlation_id={correlation_id}",
        "latency_ms": latency_ms,
    }


# =============================================================================
# ENTRYPOINT
# =============================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
