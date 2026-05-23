import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .models import (
    ChatRequest,
    ConversationStartEvent,
    DoneEvent,
    MessageChunkEvent,
    RecommendedItem,
)

router = APIRouter()
logger = logging.getLogger(__name__)

MOCK_TEXT = "Ho trovato qualcosa che potrebbe fare al caso tuo. Ecco alcune proposte selezionate per te."

MOCK_PRODUCTS = [
    RecommendedItem(
        product_id="P005",
        title="Tom Ford — Black Orchid",
        price=165.0,
        in_stock=True,
        reason="Note di oud e spezie, perfetto per l'inverno.",
        affinity=0.97,
        link="https://lume.it/products/p005",
    ),
    RecommendedItem(
        product_id="P009",
        title="Xerjoff — Naxos",
        price=280.0,
        in_stock=True,
        reason="Orientale con miele e tabacco, lussuoso e avvolgente.",
        affinity=0.91,
        link="https://lume.it/products/p009",
    ),
    RecommendedItem(
        product_id="P001",
        title="Maison Margiela Replica — Jazz Club",
        price=145.0,
        in_stock=True,
        reason="Legnoso e speziato, ideale per le serate invernali.",
        affinity=0.85,
        link="https://lume.it/products/p001",
    ),
]


@router.post(
    "/chat/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Server-Sent Events stream",
        }
    },
)
async def chat_stream(body: ChatRequest, request: Request):
    if not body.message or not body.message.content.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    conversation_id = body.conversation_id or str(uuid.uuid4())

    async def event_generator():
        yield f"data: {ConversationStartEvent(conversation_id=conversation_id).model_dump_json()}\n\n"

        try:
            chunk_size = 4
            for i in range(0, len(MOCK_TEXT), chunk_size):
                if await request.is_disconnected():
                    return
                chunk = MessageChunkEvent(content=MOCK_TEXT[i : i + chunk_size])
                yield f"data: {chunk.model_dump_json()}\n\n"
                await asyncio.sleep(0.03)

            for product in MOCK_PRODUCTS:
                if await request.is_disconnected():
                    return
                yield f"data: {product.model_dump_json()}\n\n"
                await asyncio.sleep(0.05)

        except Exception as e:
            logger.error(str(e), exc_info=True)
            yield f"data: {MessageChunkEvent(content='Mi dispiace, si è verificato un errore. Riprova tra un momento.').model_dump_json()}\n\n"

        finally:
            yield f"data: {DoneEvent().model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
