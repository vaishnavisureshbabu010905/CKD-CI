from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import get_current_user
from models.chat import ChatThread, ChatMessage
from schemas.chat import ChatThreadCreate, ChatThreadRead, ChatMessageCreate, ChatMessageRead
from services.chat_service import manager
from services.audit_service import log_audit

router = APIRouter(prefix="/chat", tags=["chat"])


def _assistant_reply(text: str) -> str:
    lower = text.lower()
    if "risk" in lower:
        return "Risk review: 1) verify eGFR trend over last 90 days, 2) check UACR and BP control, 3) if trajectory worsens, escalate to nephrology and repeat labs within 1-2 weeks."
    if "alert" in lower:
        return "Alert triage: prioritize unresolved high severity alerts, confirm latest creatinine/UACR values, and close only after documenting action taken."
    if "patient" in lower:
        return "Patient summary support ready: share identifier plus latest labs (eGFR, creatinine, UACR, BP), and I will return risk, likely drivers, and next-step checklist."
    if "predict" in lower or "prediction" in lower:
        return "Prediction interpretation: use probability + confidence together, then map to action: high-risk => urgent nephrology review; moderate => short-interval follow-up; low => routine monitoring."
    return "Real-time advice: check trend direction first (not single values), compare with prior 30-90 day labs, and set a concrete follow-up window with documented owner."


@router.post("/threads", response_model=ChatThreadRead)
def create_thread(payload: ChatThreadCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    thread = ChatThread(
        thread_type=payload.thread_type,
        patient_id=payload.patient_id,
        name=payload.name,
        participants=payload.participants,
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    log_audit(db, current_user, action="create_thread", resource_type="chat_thread", resource_id=str(thread.id))
    return thread


@router.get("/threads", response_model=list[ChatThreadRead])
def list_threads(patient_id: int | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(ChatThread).order_by(ChatThread.created_at.desc())
    if patient_id:
        q = q.filter(ChatThread.patient_id == patient_id)
    return q.limit(200).all()


@router.post("/messages", response_model=ChatMessageRead)
def post_message(payload: ChatMessageCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    thread = db.query(ChatThread).filter(ChatThread.id == payload.thread_id).first()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    msg = ChatMessage(
        thread_id=payload.thread_id,
        sender_id=current_user.id,
        content=payload.content,
        status="sent",
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    assistant = ChatMessage(
        thread_id=payload.thread_id,
        sender_id=None,
        content=_assistant_reply(payload.content),
        status="delivered",
    )
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    # best-effort push to live websocket clients
    try:
        import asyncio
        asyncio.create_task(
            manager.broadcast(msg.thread_id, {"type": "message", "thread_id": msg.thread_id, "message": ChatMessageRead.model_validate(msg).model_dump()})
        )
        asyncio.create_task(
            manager.broadcast(assistant.thread_id, {"type": "message", "thread_id": assistant.thread_id, "message": ChatMessageRead.model_validate(assistant).model_dump()})
        )
    except Exception:
        pass
    log_audit(db, current_user, action="post_message", resource_type="chat_message", resource_id=str(msg.id))
    return msg


@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: int):
    await manager.connect(thread_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(thread_id, data)
    except WebSocketDisconnect:
        manager.disconnect(thread_id, websocket)


@router.get("/messages", response_model=list[ChatMessageRead])
def list_messages(thread_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(200)
        .all()
    )
