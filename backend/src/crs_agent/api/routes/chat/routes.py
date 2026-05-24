import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from crs_agent.api.routes.chat.models import (
    ChatRequest,
    ConversationStartEvent,
    DoneEvent,
    MessageChunkEvent,
    RecommendedItem,
)

router = APIRouter()
logger = logging.getLogger(__name__)


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
    agent = request.app.state.agent

    config = {"configurable": {"thread_id": conversation_id, "recursion_limit": 50}}
    new_message = body.message.model_dump()

    async def event_generator():
        start_event = ConversationStartEvent(conversation_id=conversation_id)
        yield f"data: {start_event.model_dump_json()}\n\n"

        try:
            async for event in agent.astream_events(
                {"messages": [new_message]},
                config=config,
                version="v2",
            ):
                if await request.is_disconnected():
                    break

                kind = event["event"]
                metadata = event["metadata"]
                checkpoint_ns = metadata.get("checkpoint_ns", "")

                event_model = None

                if kind == "on_chat_model_stream":
                    if (
                        "ask_node" in checkpoint_ns
                        or "escalate_node" in checkpoint_ns
                        or "recommend_node" in checkpoint_ns
                    ):
                        content = event["data"]["chunk"].content
                        if content:
                            event_model = MessageChunkEvent(content=content)

                if event_model:
                    yield f"data: {event_model.model_dump_json()}\n\n"

            final_state = await agent.aget_state(config)
            last_decision = final_state.values.get("last_action")
            if last_decision == "recommend":
                recommendations = final_state.values.get("last_recommendations")
                if recommendations:
                    last_recommendations = recommendations[-1]
                    for recommentation in last_recommendations:
                        item = RecommendedItem.model_validate(recommentation)
                        yield f"data: {item.model_dump_json()}\n\n"
            elif last_decision == "escalate":
                messages = final_state.values.get("messages")
                if messages:
                    last_msg = messages[-1]
                    content = (
                        last_msg.content
                        if hasattr(last_msg, "content")
                        else str(last_msg)
                    )
                    escalate_message = MessageChunkEvent(content=content)
                    yield f"data: {escalate_message.model_dump_json()}\n\n"

        except Exception as e:
            logger.error(str(e), exc_info=True)
            yield f"data: {MessageChunkEvent(content='Mi dispiace, si è verificato un errore. Riprova tra un momento.').model_dump_json()}\n\n"

        finally:
            yield f"data: {DoneEvent().model_dump_json()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
