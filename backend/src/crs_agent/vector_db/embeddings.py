from langchain_openai import OpenAIEmbeddings

from crs_agent.settings import settings

embeddings_model = OpenAIEmbeddings(
    model=settings.embedding_model.model_name,
    base_url=settings.embedding_model.base_url,
    api_key=settings.embedding_model.api_key,
    dimensions=settings.qdrant.vector_size,
    check_embedding_ctx_length=False,
)
