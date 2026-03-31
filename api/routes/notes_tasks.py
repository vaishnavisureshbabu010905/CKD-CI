from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from core.deps import get_current_user
from models.note import Note, Task
from schemas.note import NoteCreate, NoteRead, TaskCreate, TaskUpdate, TaskRead
from services.audit_service import log_audit
from services.timeline_service import record_event

router = APIRouter(prefix="/collab", tags=["notes", "tasks"])


@router.post("/notes", response_model=NoteRead)
def create_note(payload: NoteCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    note = Note(
        patient_id=payload.patient_id,
        encounter_id=payload.encounter_id,
        author_id=current_user.id,
        note_type=payload.note_type,
        content=payload.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    record_event(
        db,
        patient_id=note.patient_id,
        source_type="note",
        source_id=note.id,
        summary=f"Note added ({note.note_type})",
    )
    log_audit(db, current_user, action="create_note", resource_type="note", resource_id=str(note.id))
    return note


@router.get("/notes", response_model=list[NoteRead])
def list_notes(patient_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return (
        db.query(Note)
        .filter(Note.patient_id == patient_id)
        .order_by(Note.created_at.desc())
        .limit(200)
        .all()
    )


@router.post("/tasks", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = Task(
        patient_id=payload.patient_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_at=payload.due_at,
        assignee_id=payload.assignee_id,
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    if task.patient_id:
        record_event(
            db,
            patient_id=task.patient_id,
            source_type="task",
            source_id=task.id,
            summary=f"Task created ({task.title})",
        )
    log_audit(db, current_user, action="create_task", resource_type="task", resource_id=str(task.id))
    return task


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    if payload.status == "done":
        from datetime import datetime
        task.completed_at = datetime.utcnow()
    db.add(task)
    db.commit()
    db.refresh(task)
    if task.patient_id:
        record_event(
            db,
            patient_id=task.patient_id,
            source_type="task",
            source_id=task.id,
            summary=f"Task updated ({task.status})",
        )
    log_audit(db, current_user, action="update_task", resource_type="task", resource_id=str(task.id))
    return task


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(patient_id: int | None = None, status_filter: str | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(Task).order_by(Task.created_at.desc())
    if patient_id:
        q = q.filter(Task.patient_id == patient_id)
    if status_filter:
        q = q.filter(Task.status == status_filter)
    return q.limit(200).all()
