from pathlib import Path
import hashlib
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from agents.bedrock_model import BedrockAnswerModel
from agents.budget import CloudBudget
from agents.cache import TTLCache
from agents.groq_model import GroqAnswerModel
from agents.orchestrator import CoachAIOrchestrator
from language.messages import message as localized_message
from language.registry import get_language
from knowledge.chunker import semantic_chunks
from knowledge.document_registry import ManagedDocument, documents
from knowledge.parsers import parse_document
from monitoring.metrics import metrics
from monitoring.alerts import evaluate_alerts
from ops.runtime import ops
from rag.models import DocumentChunk, DocumentMetadata, DocumentStatus
from rag.retrieval import HybridRetriever
from rag.store import InMemoryKnowledgeStore
from security.rate_limit import SlidingWindowLimiter
from translation.service import TranslationService
from voice.language_voices import available_polly_voice, language_capabilities
from voice.providers import VOICES, AmazonPollyProvider
from storage.aws_ingestion import AWSIngestionPublisher
from storage.postgres import PostgresRuntime

load_dotenv()

app=FastAPI(title="CoachAI API",version="1.6.0")
DATABASE_URL=os.getenv("DATABASE_URL","").strip()
RUNTIME_BACKEND="postgres" if DATABASE_URL else "memory"
postgres_runtime=PostgresRuntime(
    DATABASE_URL,
    auto_init_schema=os.getenv("POSTGRES_AUTO_INIT_SCHEMA","false").lower()=="true",
) if DATABASE_URL else None
if postgres_runtime:
    store=postgres_runtime.knowledge_store()
    documents=postgres_runtime.document_registry()
    ops=postgres_runtime.ops()
else:
    store=InMemoryKnowledgeStore()
    from knowledge.document_registry import documents
    from ops.runtime import ops
retriever:HybridRetriever|None=None
retriever_generation=-1
INGESTION_MODE=os.getenv("INGESTION_MODE","inline").lower()

def build_cloud_model():
    if os.getenv("LLM_ENABLED","true").lower()!="true":return None
    provider=os.getenv("LLM_PROVIDER","auto").lower()
    try:
        if provider=="bedrock":return BedrockAnswerModel()
        if provider=="groq":return GroqAnswerModel()
        if provider=="auto" and os.getenv("GROQ_API_KEY") and os.getenv("GROQ_MODEL"):return GroqAnswerModel()
        if provider=="auto" and os.getenv("BEDROCK_MODEL_ID"):return BedrockAnswerModel()
    except Exception:return None
    return None

orchestrator=CoachAIOrchestrator(
    answer_model=build_cloud_model(),
    translator=TranslationService(),
    cloud_budget=CloudBudget(max_llm_calls_per_day=int(os.getenv("MAX_LLM_CALLS_PER_DAY","1000"))),
)
rate_limiter=SlidingWindowLimiter(int(os.getenv("MAX_REQUESTS_PER_MINUTE","30")),60)
UPLOAD_DIR=Path(os.getenv("DOCUMENT_STORAGE_PATH","data/documents"));UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
MAX_UPLOAD_BYTES=int(os.getenv("MAX_UPLOAD_MB","25"))*1024*1024
tts_cache=TTLCache(ttl_seconds=int(os.getenv("TTS_CACHE_TTL_SECONDS","3600")),max_items=256)

class ChatRequest(BaseModel):
    message:str=Field(min_length=1,max_length=1400)
    conversation_id:str|None=None
    voice_id:str="Brian"
    conversation_style:str="friendly"
    language:str="auto"

class TTSRequest(BaseModel):
    text:str=Field(min_length=1,max_length=3000)
    voice_id:str="Brian"
    language:str="en-GB"

class ReviewResolution(BaseModel):
    reviewer:str=Field(min_length=1,max_length=120)
    resolution:str=Field(min_length=1,max_length=1000)

def require_admin(x_admin_key:str|None=Header(default=None))->None:
    expected=os.getenv("ADMIN_API_KEY","")
    if not expected:raise HTTPException(503,"Admin API is not configured.")
    if x_admin_key!=expected:raise HTTPException(401,"Invalid admin credentials.")

@app.get("/")
async def home():return FileResponse("web/index.html")

@app.get("/dashboard")
async def dashboard():return FileResponse("web/dashboard.html")

@app.get("/config")
async def config():
    return {"tts_mode":os.getenv("TTS_MODE","browser"),"llm_provider":os.getenv("LLM_PROVIDER","auto"),"translation_provider":os.getenv("TRANSLATION_PROVIDER","none"),"fast_path_default":True,"governed_ingestion":True,"runtime_backend":RUNTIME_BACKEND,"ingestion_mode":INGESTION_MODE}

@app.get("/languages")
async def languages():
    items=[{"code":"auto","name":"Auto-detect","native_name":"Auto-detect"}]+language_capabilities()
    for item in items:
        item["greeting"]=localized_message("greeting", item["code"] if item["code"]!="auto" else "en-GB")
    return items

@app.get("/health")
async def health():
    return {"status":"ok","service":"coachai-api","generation":store.generation,"retriever_ready":retriever is not None and retriever_generation==store.generation,"open_reviews":len(ops.list_reviews("OPEN")),"runtime_backend":RUNTIME_BACKEND,"ingestion_mode":INGESTION_MODE}

@app.get("/kpis",dependencies=[Depends(require_admin)])
async def kpis():
    snapshot=metrics.snapshot()
    doc_counts=documents.counts()
    return {"kpis":snapshot,"alerts":[a.__dict__ for a in evaluate_alerts(snapshot)],"documents":{"total":sum(doc_counts.values()),"pending_review":doc_counts.get("PENDING_REVIEW",0),"active":doc_counts.get("ACTIVE",0),"by_status":doc_counts},"human_review_queue":{"open":len(ops.list_reviews("OPEN"))}}

@app.get("/voices")
async def voices():return [v.__dict__ for v in VOICES]

@app.get("/voice-capabilities")
async def voice_capabilities():return language_capabilities()

@app.get("/documents",dependencies=[Depends(require_admin)])
async def list_documents():return [d.__dict__ for d in documents.list()]

@app.post("/admin/documents/{document_id}/approve",dependencies=[Depends(require_admin)])
async def approve_document(document_id:str,reviewer:str="admin"):
    try:
        archived=documents.activate(document_id,reviewer);store.set_document_status(document_id,DocumentStatus.ACTIVE)
        for archived_id in archived:store.set_document_status(archived_id,DocumentStatus.ARCHIVED)
        event=ops.audit("DOCUMENT_ACTIVATED",reviewer,document_id,{"archived_versions":archived})
        return {"status":"ACTIVE","document_id":document_id,"archived_versions":archived,"audit_event_id":event.event_id}
    except KeyError:raise HTTPException(404,"Document not found") from None
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc

@app.post("/admin/documents/{document_id}/reject",dependencies=[Depends(require_admin)])
async def reject_document(document_id:str,reviewer:str="admin"):
    try:
        documents.reject(document_id,reviewer);store.set_document_status(document_id,DocumentStatus.REJECTED)
        event=ops.audit("DOCUMENT_REJECTED",reviewer,document_id,{})
        return {"status":"REJECTED","document_id":document_id,"audit_event_id":event.event_id}
    except KeyError:raise HTTPException(404,"Document not found") from None
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc

@app.get("/reviews",dependencies=[Depends(require_admin)])
async def list_reviews(status:str|None=None):return [r.__dict__ for r in ops.list_reviews(status)]

@app.post("/reviews/{review_id}/resolve",dependencies=[Depends(require_admin)])
async def resolve_review(review_id:str,request:ReviewResolution):
    try:
        item=ops.resolve_review(review_id,request.reviewer,request.resolution)
        ops.audit("HUMAN_REVIEW_RESOLVED",request.reviewer,review_id,{"resolution":request.resolution})
        return item.__dict__
    except KeyError:raise HTTPException(404,"Review not found") from None

@app.get("/audit",dependencies=[Depends(require_admin)])
async def audit():
    if hasattr(ops,"list_audit"):
        return [e.__dict__ for e in ops.list_audit(200)]
    return [e.__dict__ for e in reversed(ops.audit_events[-200:])]

def get_retriever()->HybridRetriever:
    global retriever,retriever_generation
    if retriever is None or retriever_generation!=store.generation:
        retriever=HybridRetriever(store.all());retriever_generation=store.generation
    return retriever

@app.post("/chat")
async def chat(request:Request,payload:ChatRequest):
    started=time.perf_counter()
    client_key=request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client_key):
        metrics.record("rate_limit_block");raise HTTPException(429,"Too many requests. Please try again shortly.",headers={"Retry-After":"60"})
    if payload.language!="auto":
        try:get_language(payload.language)
        except ValueError:raise HTTPException(400,"Unsupported language") from None
    if payload.voice_id not in {v.voice_id for v in VOICES}:raise HTTPException(400,"Unknown voice")
    if payload.conversation_style not in {"friendly","professional","concise"}:raise HTTPException(400,"Unsupported conversation style")

    conversation_id=payload.conversation_id or uuid4().hex
    orchestrator.retriever=get_retriever();orchestrator.knowledge_generation=store.generation
    result=await orchestrator.run(payload.message,conversation_id,payload.conversation_style,payload.voice_id,payload.language)
    elapsed=(time.perf_counter()-started)*1000
    perf=result.get("performance",{})
    if perf.get("cache_hit"):metrics.record("cache_hit")
    elif perf.get("llm_called"):metrics.record("llm_call",input_tokens=len(payload.message)//4,output_tokens=len(result.get("answer",""))//4)
    else:metrics.record("fast_path")
    translation_calls=int(perf.get("query_translated",False))+int(perf.get("answer_translated",False))
    if translation_calls:metrics.record("translation_call",translation_characters=len(payload.message)+len(result.get("answer","")))
    if perf.get("budget_blocked"):metrics.record("budget_block")
    metrics.record("abstention" if result.get("abstained") else "answer",elapsed)
    if result.get("security_blocked"):metrics.record("security_block")
    review_id=None
    if result.get("next_action")=="human_review":
        item=ops.enqueue_review(result.get("reason",result.get("intent","human_review")),payload.message,conversation_id);review_id=item.review_id
        metrics.record("human_escalation");ops.audit("HUMAN_REVIEW_CREATED","system",review_id,{"intent":result.get("intent")})
    result["conversation_id"]=conversation_id
    if review_id:result["review_id"]=review_id
    return result

@app.post("/documents/upload")
async def upload_document(file:UploadFile=File(...)):
    suffix=Path(file.filename or "").suffix.lower();allowed={".pdf",".docx",".pptx",".xlsx",".xls",".csv",".txt",".md",".html",".htm",".json"}
    if suffix not in allowed:raise HTTPException(415,f"Unsupported file type: {suffix or 'unknown'}")
    original_name=file.filename or f"document{suffix}";document_id=uuid4().hex;destination=UPLOAD_DIR/f"{document_id}{suffix}"
    content_hash=hashlib.sha256();total_bytes=0
    with destination.open("wb") as output:
        while chunk:=file.file.read(1024*1024):
            total_bytes+=len(chunk)
            if total_bytes>MAX_UPLOAD_BYTES:
                destination.unlink(missing_ok=True);raise HTTPException(413,f"File exceeds MAX_UPLOAD_MB={MAX_UPLOAD_BYTES//(1024*1024)}.")
            content_hash.update(chunk);output.write(chunk)
    digest=content_hash.hexdigest()
    if any(d.content_hash==digest for d in documents.list()):
        destination.unlink(missing_ok=True);raise HTTPException(409,"This document content already exists.")
    version=documents.next_version(original_name)
    try:
        if INGESTION_MODE=="aws_async":
            if not postgres_runtime:
                destination.unlink(missing_ok=True)
                raise HTTPException(503,"AWS async ingestion requires DATABASE_URL.")
            publisher=AWSIngestionPublisher()
            source_uri=publisher.upload_file(destination,document_id=document_id,filename=original_name,version=version,content_hash=digest)
            documents.add(ManagedDocument(document_id,original_name,version,digest,"general","PROCESSING",datetime.now(timezone.utc),source_uri=source_uri))
            publisher.enqueue(document_id=document_id,filename=original_name,version=version,content_hash=digest,source_uri=source_uri)
            event=ops.audit("DOCUMENT_INGESTION_QUEUED","system",document_id,{"filename":original_name,"version":version,"content_hash":digest,"source_uri":source_uri})
            destination.unlink(missing_ok=True)
            return {"document_id":document_id,"filename":original_name,"version":version,"status":"PROCESSING","ingestion":"queued","message":"Document stored in S3 and queued for background processing. It will require admin approval after processing.","audit_event_id":event.event_id}

        normalized=parse_document(destination);chunks=semantic_chunks(normalized)
        metadata=DocumentMetadata(document_id,original_name,version,"general",DocumentStatus.PENDING_REVIEW)
        converted=[DocumentChunk(f"{document_id}-{i}",metadata,c.location.page,c.location.section,c.text) for i,c in enumerate(chunks)]
        documents.add(ManagedDocument(document_id,original_name,version,digest,"general","PENDING_REVIEW",datetime.now(timezone.utc)))
        store.add(converted)
        event=ops.audit("DOCUMENT_UPLOADED","system",document_id,{"filename":original_name,"version":version,"content_hash":digest,"chunks":len(converted)})
        return {"document_id":document_id,"filename":original_name,"format":normalized.document_type.value,"version":version,"chunks_indexed":len(converted),"status":"PENDING_REVIEW","message":"Document processed. An admin must approve it before students can use it.","audit_event_id":event.event_id}
    except HTTPException:
        raise
    except Exception as exc:
        destination.unlink(missing_ok=True);raise HTTPException(422,f"Document extraction failed: {exc}") from exc

@app.post("/tts")
async def tts(request:TTSRequest):
    try:lang=get_language(request.language)
    except ValueError:raise HTTPException(400,"Unsupported language") from None
    matching=[v for v in VOICES if v.voice_id==request.voice_id]
    if not matching:raise HTTPException(400,"Unknown voice")
    voice=matching[0];selected_voice=voice.voice_id
    if voice.language!=lang.code:
        replacement=available_polly_voice(lang.code,voice.gender)
        if replacement:selected_voice=replacement
        elif not lang.polly_code:raise HTTPException(503,"Cloud voice is not available for this language. Use browser voice output instead.")
    engine=os.getenv("POLLY_ENGINE","neural")
    cache_key=AmazonPollyProvider.cache_key(request.text,selected_voice,engine,lang.polly_code or lang.code)
    cached=tts_cache.get(cache_key)
    if cached is not None:return Response(content=cached,media_type="audio/mpeg",headers={"X-TTS-Cache":"HIT"})
    try:audio=AmazonPollyProvider().synthesize(request.text,selected_voice,lang.polly_code or lang.code)
    except Exception as exc:raise HTTPException(503,f"Voice service unavailable: {exc}") from exc
    tts_cache.set(cache_key,audio);metrics.record("tts",tts_characters=len(request.text))
    return Response(content=audio,media_type="audio/mpeg",headers={"X-TTS-Cache":"MISS"})
