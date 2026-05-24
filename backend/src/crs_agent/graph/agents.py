from crs_agent.graph.schema import CentralAgentOutput
from crs_agent.settings import settings
from crs_agent.tools.retriever import retrieve_products
from crs_agent.utils.models_factory import build_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware

orchestrator_model = build_chat_model(settings.orchestrator_model, timeout=30)

orchestrator_agent = create_agent(
    orchestrator_model,
    tools=[retrieve_products],
    response_format=CentralAgentOutput,
    middleware=[
        ModelCallLimitMiddleware(run_limit=5, exit_behavior="end"),
    ],
    checkpointer=False,
)

ask_model = build_chat_model(settings.ask_model, timeout=30, streaming=True)

recommend_model = build_chat_model(settings.recommend_model, timeout=30, streaming=True)
