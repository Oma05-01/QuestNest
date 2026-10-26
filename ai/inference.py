# ai/inference.py
import time
from typing import Type, TypeVar
from pydantic import BaseModel as PydanticBaseModel

from langchain_groq import ChatGroq
from django.conf import settings
from ai.models import AIRun

T = TypeVar("T", bound=PydanticBaseModel)

def _resolve_cfg(task: str) -> dict:
    return settings.AI_MODELS.get(task, settings.AI_MODELS["default"])

def get_model(task: str = "default"):
    cfg = _resolve_cfg(task)
    return ChatGroq(
        model=cfg["model"],
        temperature=cfg.get("temperature", 0.0),
        groq_api_key=settings.GROQ_API_KEY,
        timeout=30,
        max_retries=2,
    )


def run_structured(
        task: str,
        schema: Type[T],
        messages: list,
        *,
        workspace,
        user=None
) -> T:
    """
    Executes a structured output invocation while enforcing workspace context
    logging and performance metric persistence.
    """
    model = get_model(task).with_structured_output(schema, include_raw=True)
    start_time = time.time()

    cfg = _resolve_cfg(task)

    ai_run = AIRun(
        workspace=workspace,
        user=user,
        task=task,
        model_name=cfg["model"],
    )

    try:
        result = model.invoke(messages)
        latency = int((time.time() - start_time) * 1000)

        ai_run.latency_ms = latency
        ai_run.status = "success"
        ai_run.save()
        return result

    except Exception as e:
        ai_run.latency_ms = int((time.time() - start_time) * 1000)
        ai_run.status = "failed"
        ai_run.error_message = str(e)
        ai_run.save()
        raise e