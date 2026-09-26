from __future__ import annotations

import json
import socket

from urllib import (
    error,
    request,
)

from app.rca.ollama_adapter import (
    get_ollama_model,
    get_ollama_url,
)


class AgentOllamaError(
    RuntimeError
):
    pass


def _get_chat_url() -> str:
    configured = (
        get_ollama_url()
        .strip()
        .rstrip("/")
    )

    if configured.endswith(
        "/api/chat"
    ):
        return configured

    if configured.endswith(
        "/api/generate"
    ):
        return (
            configured[
                :-len(
                    "/api/generate"
                )
            ]
            + "/api/chat"
        )

    if configured.endswith(
        "/api"
    ):
        return (
            configured
            + "/chat"
        )

    return (
        configured
        + "/api/chat"
    )


def generate_agent_answer(
    *,
    system_prompt: str,
    user_prompt: str,
) -> dict:
    model = (
        get_ollama_model()
    )

    payload = {
        "model":
            model,

        "stream":
            False,

        "keep_alive":
            "10m",

        # Agent answers should be concise explanations,
        # not long hidden reasoning runs.
        "think":
            False,

        "messages": [
            {
                "role":
                    "system",

                "content":
                    system_prompt,
            },
            {
                "role":
                    "user",

                "content":
                    user_prompt,
            },
        ],

        "options": {
            "temperature":
                0.1,

            "num_predict":
                220,

            "num_ctx":
                4096,
        },
    }

    body = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    http_request = (
        request.Request(
            _get_chat_url(),

            data=body,

            method="POST",

            headers={
                "Content-Type":
                    "application/json",
            },
        )
    )

    try:
        with request.urlopen(
            http_request,
            timeout=180,
        ) as response:
            raw = (
                response
                .read()
                .decode(
                    "utf-8"
                )
            )

    except error.HTTPError as exc:
        detail = (
            exc.read()
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        raise AgentOllamaError(
            (
                "Ollama returned "
                f"HTTP {exc.code}: "
                f"{detail}"
            )
        ) from exc

    except (
        error.URLError,
        TimeoutError,
        socket.timeout,
    ) as exc:
        reason = getattr(
            exc,
            "reason",
            exc,
        )

        raise AgentOllamaError(
            (
                "Local Ollama request failed: "
                f"{reason}"
            )
        ) from exc

    try:
        data = json.loads(
            raw
        )

    except json.JSONDecodeError as exc:
        raise AgentOllamaError(
            (
                "Ollama returned "
                "invalid JSON"
            )
        ) from exc

    message = (
        data.get(
            "message"
        )
        or {}
    )

    answer = (
        message.get(
            "content"
        )
        or ""
    ).strip()

    if not answer:
        raise AgentOllamaError(
            (
                "Ollama returned "
                "an empty answer"
            )
        )

    return {
        "provider":
            "OLLAMA_LOCAL",

        "model":
            model,

        "answer":
            answer,

        "metadata": {
            "done":
                data.get(
                    "done"
                ),

            "done_reason":
                data.get(
                    "done_reason"
                ),

            "total_duration":
                data.get(
                    "total_duration"
                ),

            "load_duration":
                data.get(
                    "load_duration"
                ),

            "prompt_eval_count":
                data.get(
                    "prompt_eval_count"
                ),

            "eval_count":
                data.get(
                    "eval_count"
                ),
        },
    }
