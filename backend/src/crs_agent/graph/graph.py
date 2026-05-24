import json
import logging
import operator
from typing import Annotated, Any, Dict, List, TypedDict

from crs_agent.graph.agents import ask_model, orchestrator_agent, recommend_model
from crs_agent.graph.schema import (
    AskClarification,
    CentralAgentOutput,
    Escalate,
    Recommend,
)
from crs_agent.prompts.orchestrator_prompt import (
    ASK_SYSTEM_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
    RECOMMEND_SYSTEM_PROMPT,
)
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    thread_id: str
    customer_id: str
    turn_count: int
    last_recommendations: Annotated[List[List[Dict[str, Any]]], operator.add]
    last_action: str
    orchestrator_decision: Any
    needs_human: bool


async def prepare_state(state: GraphState, config: RunnableConfig):
    turn_count = state.get("turn_count", 0) + 1

    return {
        "turn_count": turn_count,
    }


async def orchestrator(state: GraphState, config: RunnableConfig):
    logger.info(f"Orchestrator state: {state}")
    messages = [SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT)] + state["messages"]
    response = await orchestrator_agent.ainvoke({"messages": messages}, config)
    logger.info(f"Orchestrator agent response: {response}")

    decision = response.get("structured_response")
    if isinstance(decision, CentralAgentOutput):
        decision = decision.root
    else:
        logger.warning(
            f"Orchestrator returned no structured response or invalid type: {type(decision)}"
        )
        return {
            "orchestrator_decision": Escalate(
                reason="Non sono riuscito a trovare una risposta adatta."
            ),
            "last_action": "escalate",
        }

    action_type = "unknown"
    if isinstance(decision, Recommend) or (
        isinstance(decision, dict) and decision.get("action") == "recommend"
    ):
        action_type = "recommend"

    elif isinstance(decision, AskClarification) or (
        isinstance(decision, dict) and decision.get("action") == "ask"
    ):
        action_type = "ask"

    elif isinstance(decision, Escalate) or (
        isinstance(decision, dict) and decision.get("action") == "escalate"
    ):
        action_type = "escalate"

    logger.info(f"Orchestrator final decision: {decision}, action: {action_type}")
    return {"orchestrator_decision": decision, "last_action": action_type}


async def recommend_node(state: GraphState, config: RunnableConfig):
    decision: Recommend = state.get("orchestrator_decision")
    if not decision or not hasattr(decision, "items"):
        logger.error(f"recommend_node called with invalid decision: {decision}")
        return {
            "messages": [SystemMessage(content="Si è verificato un errore interno.")]
        }
    from crs_agent.vector_db.retriever import retrieve_by_product_ids

    product_ids = [item.product_id for item in decision.items]

    products = await retrieve_by_product_ids(product_ids)
    product_map = {p.product_id: p for p in products}

    enriched_items = []
    for rec_item in decision.items:
        pid = rec_item.product_id
        p_data = product_map.get(pid)

        item_dict = p_data.model_dump() if p_data else {"product_id": pid}
        item_dict.pop("score", None)
        item_dict.pop("schema_version", None)
        item_dict.update(
            {
                "type": "recommended_item",
                "reason": rec_item.reason,
                "affinity": rec_item.affinity,
                "price": p_data.min_price_eur if p_data else None,
                "in_stock": p_data.available if p_data else None,
                "link": None,
            }
        )
        enriched_items.append(item_dict)

    messages = [SystemMessage(content=RECOMMEND_SYSTEM_PROMPT)]
    items_text = json.dumps(enriched_items, ensure_ascii=False)
    messages.append(
        HumanMessage(
            content=f"Please present these recommended products to the user:\n{items_text}"
        )
    )

    reply = await recommend_model.ainvoke(messages, config)

    return {"messages": [reply], "last_recommendations": [enriched_items]}


async def ask_node(state: GraphState, config: RunnableConfig):
    decision = state.get("orchestrator_decision")
    logger.info(f"ask_node decision: {decision}")

    if not decision:
        logger.error("ask_node called with None decision")
        topic = "their preferences"
    else:
        topic = (
            decision.question_topic
            if hasattr(decision, "question_topic")
            else decision.get("question_topic", "their preferences")
        )

    messages = [SystemMessage(content=ASK_SYSTEM_PROMPT)]
    messages.append(
        HumanMessage(content=f"The user needs clarification regarding: {topic}")
    )

    reply = await ask_model.ainvoke(messages, config)

    return {"messages": [reply]}


async def escalate_node(state: GraphState, config: RunnableConfig):
    decision: Escalate = state.get("orchestrator_decision")
    if not decision:
        logger.error("escalate_node called with None decision")
        reason = "Mi dispiace, non sono in grado di procedere con la tua richiesta in questo momento."
    else:
        reason = (
            decision.reason
            if hasattr(decision, "reason")
            else decision.get("reason", "Unknown reason")
        )
    from langchain_core.messages import AIMessage

    return {"messages": [AIMessage(content=reason)], "needs_human": True}


def route_orchestrator(state: GraphState) -> str:
    action = state.get("last_action")
    if action == "recommend":
        return "recommend_node"
    elif action == "ask":
        return "ask_node"
    elif action == "escalate":
        return "escalate_node"
    # Fallback to escalate if unknown
    return "escalate_node"


agent_builder = StateGraph(GraphState)
agent_builder.add_node("prepare_state", prepare_state)
agent_builder.add_node("orchestrator", orchestrator)
agent_builder.add_node("recommend_node", recommend_node)
agent_builder.add_node("ask_node", ask_node)
agent_builder.add_node("escalate_node", escalate_node)

agent_builder.add_edge(START, "prepare_state")
agent_builder.add_edge("prepare_state", "orchestrator")
agent_builder.add_conditional_edges("orchestrator", route_orchestrator)
agent_builder.add_edge("recommend_node", END)
agent_builder.add_edge("ask_node", END)
agent_builder.add_edge("escalate_node", END)


def build_agent(checkpointer: AsyncPostgresSaver = None):
    if checkpointer:
        return agent_builder.compile(checkpointer=checkpointer)
    return agent_builder.compile()
