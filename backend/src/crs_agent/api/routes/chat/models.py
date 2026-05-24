from typing import Literal, Optional, Union

from pydantic import BaseModel, field_validator


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: ChatMessage
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str


class ConversationStartEvent(BaseModel):
    type: Literal["conversation_start"] = "conversation_start"
    conversation_id: str


class MessageChunkEvent(BaseModel):
    type: Literal["message_chunk"] = "message_chunk"
    content: str


class RecommendedItem(BaseModel):
    type: Literal["recommended_item"] = "recommended_item"
    product_id: str
    title: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None
    reason: Optional[str] = None
    affinity: Optional[float] = None
    link: Optional[str] = None

    @field_validator("title", mode="before")
    @classmethod
    def title_fallback(cls, v, info):
        if v is None:
            return info.data.get("product_id", "Unknown")
        return v


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"


StreamEvent = Union[
    ConversationStartEvent,
    MessageChunkEvent,
    RecommendedItem,
    DoneEvent,
]
