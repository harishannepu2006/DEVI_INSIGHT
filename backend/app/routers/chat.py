"""Chat router — bug-specific AI chatbot."""
from fastapi import APIRouter, HTTPException, Depends
from app.middleware.auth_middleware import get_current_user
from app.utils.supabase_client import get_db
from app.services.ai_engine import AIEngine
from app.models.schemas import ChatMessageRequest

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/bug/{bug_id}")
async def chat_with_bug(bug_id: str, data: ChatMessageRequest,
                        current_user: dict = Depends(get_current_user)):
    """Chat with AI about a specific bug."""
    db = get_db()
    ai_engine = AIEngine()

    # Get bug details
    bug_result = db.table("bugs").select("*").eq("id", bug_id).execute()
    if not bug_result.data:
        raise HTTPException(status_code=404, detail="Bug not found")

    bug = bug_result.data[0]

    # Get chat history
    history = db.table("chat_messages").select("*").eq(
        "bug_id", bug_id
    ).order("created_at").execute()

    # Store user message
    db.table("chat_messages").insert({
        "bug_id": bug_id,
        "user_id": current_user["id"],
        "role": "user",
        "content": data.message,
    }).execute()

    # Generate AI response
    response_text = ai_engine.generate_bug_chat_response(
        bug=bug,
        question=data.message,
        chat_history=history.data or [],
    )

    # Store assistant response
    assistant_msg = db.table("chat_messages").insert({
        "bug_id": bug_id,
        "user_id": current_user["id"],
        "role": "assistant",
        "content": response_text,
    }).execute()

    return {
        "response": response_text,
        "message_id": assistant_msg.data[0]["id"] if assistant_msg.data else None,
    }


@router.get("/bug/{bug_id}/history")
async def get_chat_history(bug_id: str, current_user: dict = Depends(get_current_user)):
    """Get chat history for a specific bug."""
    db = get_db()

    result = db.table("chat_messages").select("*").eq(
        "bug_id", bug_id
    ).order("created_at").execute()

    return {"messages": result.data, "total": len(result.data)}
