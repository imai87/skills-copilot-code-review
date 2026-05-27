"""
Announcement management endpoints for the High School Management System API
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    """Payload used to create or update an announcement."""

    message: str = Field(..., min_length=5, max_length=280)
    start_date: Optional[datetime] = None
    expires_at: datetime


def _to_api_model(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize MongoDB document to API response format."""
    return {
        "id": str(doc["_id"]),
        "message": doc["message"],
        "start_date": doc.get("start_date"),
        "expires_at": doc["expires_at"],
        "created_by": doc.get("created_by")
    }


def _normalize_datetime(value: datetime) -> datetime:
    """Convert datetimes to UTC naive format for consistent storage/comparison."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _to_lexical_datetime(value: datetime) -> str:
    """Format datetime as sortable string (YYYY-MM-DDTHH:MM:SS)."""
    normalized = _normalize_datetime(value)
    return normalized.strftime("%Y-%m-%dT%H:%M:%S")


def _validate_payload(payload: AnnouncementPayload) -> None:
    normalized_message = payload.message.strip()
    if len(normalized_message) < 5:
        raise HTTPException(
            status_code=400,
            detail="Message must contain at least 5 characters"
        )

    now = datetime.utcnow()
    expires_at = _normalize_datetime(payload.expires_at)
    if expires_at <= now:
        raise HTTPException(
            status_code=400,
            detail="Expiration date must be in the future"
        )

    if payload.start_date:
        start_date = _normalize_datetime(payload.start_date)
        if start_date.year < 1970:
            raise HTTPException(status_code=400, detail="Start date is invalid")
        if start_date >= expires_at:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before expiration date"
            )


def _require_authenticated_teacher(username: Optional[str]) -> Dict[str, Any]:
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Return currently active announcements for public display."""
    now = _to_lexical_datetime(datetime.utcnow())
    query = {
        "expires_at": {"$gt": now},
        "$or": [
            {"start_date": None},
            {"start_date": {"$lte": now}},
            {"start_date": {"$exists": False}}
        ]
    }

    docs = announcements_collection.find(query).sort("expires_at", 1)
    return [_to_api_model(doc) for doc in docs]


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def list_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List all announcements for management (authenticated users only)."""
    _require_authenticated_teacher(teacher_username)
    docs = announcements_collection.find({}).sort("expires_at", 1)
    return [_to_api_model(doc) for doc in docs]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Create a new announcement (authenticated users only)."""
    teacher = _require_authenticated_teacher(teacher_username)
    _validate_payload(payload)

    new_id = str(uuid4())
    doc = {
        "_id": new_id,
        "message": payload.message.strip(),
        "start_date": _to_lexical_datetime(payload.start_date) if payload.start_date else None,
        "expires_at": _to_lexical_datetime(payload.expires_at),
        "created_by": teacher["username"]
    }
    announcements_collection.insert_one(doc)
    return _to_api_model(doc)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement (authenticated users only)."""
    _require_authenticated_teacher(teacher_username)
    _validate_payload(payload)

    update_doc = {
        "message": payload.message.strip(),
        "start_date": _to_lexical_datetime(payload.start_date) if payload.start_date else None,
        "expires_at": _to_lexical_datetime(payload.expires_at)
    }

    result = announcements_collection.update_one(
        {"_id": announcement_id},
        {"$set": update_doc}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": announcement_id})
    return _to_api_model(updated)


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """Delete an announcement (authenticated users only)."""
    _require_authenticated_teacher(teacher_username)

    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted successfully"}
