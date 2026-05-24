from crs_agent.settings import AIModelConfig, ModelRoleConfig, settings
from langchain_core.runnables import Runnable
from langchain_litellm import ChatLiteLLM


def resolve_model(name: str) -> AIModelConfig:
    config = settings.models.get(name)
    if config is None:
        raise ValueError(f"Model '{name}' is not defined in settings.models")
    return config


def build_chat_model(role: ModelRoleConfig, **overrides) -> Runnable:
    primary = resolve_model(role.model)

    kwargs = dict(
        model=primary.model_name,
        base_url=primary.base_url,
        api_key=primary.api_key,
        temperature=role.temperature,
        max_tokens=role.max_tokens,
        top_p=role.top_p,
    )

    if role.reasoning_effort is not None and primary.reasoning_model:
        kwargs["extra_body"] = {"reasoning_effort": role.reasoning_effort}

    kwargs.update(overrides)
    model = ChatLiteLLM(**kwargs)

    if role.fallback is not None:
        fallback = resolve_model(role.fallback)
        fallback_kwargs = dict(
            model=fallback.model_name,
            base_url=fallback.base_url,
            api_key=fallback.api_key,
            temperature=role.temperature,
            max_tokens=role.max_tokens,
            top_p=role.top_p,
        )

        if role.reasoning_effort is not None and fallback.reasoning_model:
            fallback_kwargs["extra_body"] = {"reasoning_effort": role.reasoning_effort}

        for key in ("timeout", "streaming"):
            if key in overrides:
                fallback_kwargs[key] = overrides[key]

        fallback_model = ChatLiteLLM(**fallback_kwargs)
        return model.with_fallbacks(
            [fallback_model],
            exceptions_to_handle=(Exception,),
        )

    return model
