import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from crs_agent.graph.graph import build_agent
from crs_agent.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def postgres_lifespan(app: FastAPI):
    async with AsyncPostgresSaver.from_conn_string(
        settings.postgres.url
    ) as checkpointer:
        await checkpointer.setup()
        logger.info("Postgres checkpointer initialized.")
        app.state.agent = build_agent(checkpointer)
        yield


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.postgres.enabled:
        async with postgres_lifespan(app):
            yield
    else:
        logger.info("Postgres disabled. Using in-memory checkpointer (no persistence).")
        app.state.agent = build_agent(MemorySaver())
        yield
