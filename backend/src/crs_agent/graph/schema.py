from typing import List, Literal, Union

from pydantic import BaseModel, Field, RootModel


class RecommendedItem(BaseModel):
    product_id: str = Field(
        description="ID of the recommended product. Must be an ID returned by retrieve_products in this turn."
    )
    reason: str = Field(
        description=(
            "One sentence explaining why this product fits the customer's need. "
            "Ground it in the ProductCard data — scent profile, price, occasion. "
            "Never invent facts not present in the card."
        )
    )
    affinity: float = Field(
        description=(
            "Confidence that this product matches the customer's need, from 0.0 to 1.0. "
            "Use the retrieval score as a starting point, adjust based on how well the product "
            "matches filters, occasion, and expressed preferences."
        )
    )


class AskClarification(BaseModel):
    action: Literal["ask"] = "ask"
    question_topic: str = Field(
        description="The topic or aspect you need clarification on."
    )


class Recommend(BaseModel):
    action: Literal["recommend"] = "recommend"
    items: List[RecommendedItem] = Field(description="List of products to recommend.")


class Escalate(BaseModel):
    action: Literal["escalate"] = "escalate"
    reason: str = Field(description="Reason for escalating to human agent.")


class CentralAgentOutput(RootModel[Union[AskClarification, Recommend, Escalate]]):
    pass


OrchestratorOutput = CentralAgentOutput
