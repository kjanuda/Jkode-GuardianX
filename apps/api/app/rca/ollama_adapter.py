from __future__ import annotations

import json
import os
from typing import Any

import requests


DEFAULT_OLLAMA_URL = (
    "http://localhost:11434"
)

DEFAULT_MODEL = (
    "qwen3.5:4b"
)


ALLOWED_DOMAINS = [
    "DEVICE_DOMAIN",
    "NETWORK_DOMAIN",
    "PROPAGATION_DOMAIN",
]


ALLOWED_CAUSES = [
    "DEVICE_MODEL_OR_FIRMWARE",
    "CELL_OR_NETWORK",
    "CONGESTION_OR_BACKHAUL",
    "COVERAGE_OR_PROPAGATION",
    "INTERFERENCE",
    "OUTAGE",
    "TERRAIN_PROPAGATION_LIKELY",
    "VEGETATION_PROPAGATION_POSSIBLE",
    "WEATHER_STRESS_POSSIBLE",
]


class OllamaRCAError(Exception):
    pass


def get_ollama_url() -> str:
    return (
        os.getenv(
            "OLLAMA_BASE_URL"
        )
        or DEFAULT_OLLAMA_URL
    ).rstrip("/")


def get_ollama_model() -> str:
    return (
        os.getenv(
            "OLLAMA_RCA_MODEL"
        )
        or DEFAULT_MODEL
    )


def build_proposal_schema() -> dict:
    return {
        "type": "object",

        "properties": {
            "proposed_domain": {
                "type": "string",
                "enum": ALLOWED_DOMAINS,
            },

            "primary_cause": {
                "type": "string",
                "enum": ALLOWED_CAUSES,
            },

            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },

            "evidence_ids": {
                "type": "array",

                "items": {
                    "type": "integer",
                },

                "minItems": 1,
            },

            "contributors": {
                "type": "array",

                "items": {
                    "type": "object",

                    "properties": {
                        "cause": {
                            "type": "string",
                            "enum": ALLOWED_CAUSES,
                        },

                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },

                        "evidence_ids": {
                            "type": "array",

                            "items": {
                                "type": "integer",
                            },

                            "minItems": 1,
                        },
                    },

                    "required": [
                        "cause",
                        "confidence",
                        "evidence_ids",
                    ],

                    "additionalProperties":
                        False,
                },
            },

            "reasoning_summary": {
                "type": "string",
            },
        },

        "required": [
            "proposed_domain",
            "primary_cause",
            "confidence",
            "evidence_ids",
            "contributors",
            "reasoning_summary",
        ],

        "additionalProperties":
            False,
    }


SYSTEM_PROMPT = """
You are the Guardian X telecom RCA proposal engine.

You are NOT the final decision maker.
Guardian X will independently verify every claim.

==================================================
AUTHORITATIVE DOMAIN / CAUSE CONTRACT
==================================================

DEVICE_DOMAIN:
- DEVICE_MODEL_OR_FIRMWARE

NETWORK_DOMAIN:
- CELL_OR_NETWORK
- CONGESTION_OR_BACKHAUL
- INTERFERENCE
- OUTAGE

PROPAGATION_DOMAIN:
- COVERAGE_OR_PROPAGATION
- TERRAIN_PROPAGATION_LIKELY
- VEGETATION_PROPAGATION_POSSIBLE
- WEATHER_STRESS_POSSIBLE

You MUST use the domain associated with the
selected primary cause exactly as defined above.

==================================================
EVIDENCE RULES
==================================================

1. Use only evidence in the supplied packet.

2. Never invent evidence IDs, measurements,
   timestamps, locations, or network conditions.

3. Every evidence ID in primary evidence_ids
   MUST directly support primary_cause.

   This means primary_cause must literally appear
   in that evidence record's supports_causes list.

4. Do NOT cite related or corroborating evidence
   under primary evidence_ids if it supports a
   different cause.

Example:

If:
- evidence 101 supports COVERAGE_OR_PROPAGATION
- evidence 104 supports TERRAIN_PROPAGATION_LIKELY
- evidence 105 supports VEGETATION_PROPAGATION_POSSIBLE

Then this is INVALID:

primary_cause = COVERAGE_OR_PROPAGATION
evidence_ids = [101, 104, 105]

because 104 and 105 do not directly support
COVERAGE_OR_PROPAGATION.

5. Contributor evidence IDs must directly support
   that contributor's cause.

6. Evidence with gate_passed=false MUST NOT be
   used as supporting causal evidence.

7. If a broad cause such as
   COVERAGE_OR_PROPAGATION is supported, and a
   more specific physical root cause such as
   TERRAIN_PROPAGATION_LIKELY is also directly
   supported, prefer the more specific supported
   physical cause as primary.

Example:

primary:
TERRAIN_PROPAGATION_LIKELY
evidence_ids:
[terrain evidence]

contributor:
VEGETATION_PROPAGATION_POSSIBLE
evidence_ids:
[vegetation evidence]

8. Do not claim WEATHER_STRESS_POSSIBLE unless
   weather evidence both supports that cause and
   has gate_passed=true.

9. Do not claim DEVICE_MODEL_OR_FIRMWARE when
   population evidence contradicts a device-model
   specific incident.

10. Confidence is an evidence-strength proposal,
    not a calibrated probability.

11. reasoning_summary is explanation only.
    It is NEVER evidence.

12. Do not treat a high support_score,
    reliability_score, freshness_score, or
    specificity_score as permission to ignore
    the actual evidence content.

13. Do not use an evidence record merely because
    its category appears related to a cause.
    The cause must be directly present in
    supports_causes.

14. Do not use contradicts_causes as supporting
    evidence.

15. If no supplied evidence directly supports a
    specific cause, do not invent support for it.
    Select only a cause that is directly supported
    by valid gated evidence.

16. Keep reasoning_summary concise and grounded
    entirely in the supplied evidence.

17. The final proposal must contain at least one
    valid primary evidence ID.

18. Every contributor must contain at least one
    evidence ID that directly supports that
    contributor cause.

==================================================
PHYSICAL PROPAGATION GUIDANCE
==================================================

When terrain evidence is supplied, consider the
provided physical propagation summaries such as:

- mean_los_blocked_pct
- mean_geo_vulnerability
- propagation_high_ratio
- coverage_signature_ratio
- fresnel_v2_available_ratio
- mean_fresnel_occupancy_pct
- mean_max_fresnel_intrusion_m
- mean_minimum_clearance_ratio

Do NOT invent physical interpretation beyond the
values actually supplied.

When Fresnel evidence is unavailable or gated out,
do not claim that Fresnel obstruction proves the
cause.

When terrain evidence directly supports
TERRAIN_PROPAGATION_LIKELY, it may be selected as
a specific primary cause instead of the broader
COVERAGE_OR_PROPAGATION cause.

==================================================
OUTPUT CONTRACT
==================================================

Return exactly one structured RCA proposal.

The output must contain:

- proposed_domain
- primary_cause
- confidence
- evidence_ids
- contributors
- reasoning_summary

Return only valid JSON matching the supplied schema.

Do not return Markdown.

Do not return explanations outside the JSON object.
""".strip()


def generate_ollama_rca_proposal(
    *,
    evidence_packet: dict[str, Any],
) -> dict[str, Any]:

    base_url = (
        get_ollama_url()
    )

    model = (
        get_ollama_model()
    )

    # ========================================================
    # OLLAMA CHAT PAYLOAD
    # ========================================================

    payload = {
        "model":
            model,

        "stream":
            False,

        # ----------------------------------------------------
        # Qwen structured RCA mode
        #
        # IMPORTANT:
        # `think` is TOP-LEVEL.
        # It must NOT be placed inside `options`.
        # ----------------------------------------------------

        "think":
            False,

        "messages": [
            {
                "role":
                    "system",

                "content":
                    SYSTEM_PROMPT,
            },

            {
                "role":
                    "user",

                "content": (
                    "Analyze the following "
                    "Guardian X RCA evidence "
                    "packet.\n\n"
                    "Produce exactly one "
                    "evidence-based RCA proposal.\n\n"
                    f"{json.dumps(
                        evidence_packet,
                        ensure_ascii=False
                    )}"
                ),
            },
        ],

        # ----------------------------------------------------
        # Structured output schema
        # ----------------------------------------------------

        "format":
            build_proposal_schema(),

        # ----------------------------------------------------
        # Performance settings
        # ----------------------------------------------------

        "options": {
            "temperature":
                0,

            "num_predict":
                350,

            "num_ctx":
                4096,
        },
    }

    # ========================================================
    # OLLAMA REQUEST
    # ========================================================

    try:
        response = requests.post(
            f"{base_url}/api/chat",

            json=payload,

            # Connection timeout:
            #     10 seconds
            #
            # Read / generation timeout:
            #     600 seconds
            timeout=(
                10,
                600,
            ),
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise OllamaRCAError(
            f"Ollama request failed: {exc}"
        ) from exc

    # ========================================================
    # PARSE HTTP RESPONSE
    # ========================================================

    try:
        data = (
            response.json()
        )

    except ValueError as exc:
        raise OllamaRCAError(
            "Ollama returned invalid JSON "
            "at the HTTP response level"
        ) from exc

    # ========================================================
    # EXTRACT MESSAGE
    # ========================================================

    message = (
        data.get(
            "message"
        )
        or {}
    )

    raw_content = (
        message.get(
            "content"
        )
        or ""
    ).strip()

    # ========================================================
    # EMPTY OUTPUT DIAGNOSTICS
    # ========================================================

    if not raw_content:

        thinking = (
            message.get(
                "thinking"
            )
            or ""
        )

        done_reason = (
            data.get(
                "done_reason"
            )
        )

        raise OllamaRCAError(
            "Ollama returned no proposal. "
            f"done_reason={done_reason}, "
            f"thinking_chars={len(thinking)}"
        )

    # ========================================================
    # PARSE STRUCTURED PROPOSAL
    # ========================================================

    try:
        proposal = json.loads(
            raw_content
        )

    except json.JSONDecodeError as exc:
        raise OllamaRCAError(
            "Ollama output was not valid JSON"
        ) from exc

    # ========================================================
    # RETURN PROPOSAL + METADATA
    # ========================================================

    return {
        "model":
            model,

        "proposal":
            proposal,

        "ollama_metadata": {
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

            "prompt_eval_count":
                data.get(
                    "prompt_eval_count"
                ),

            "eval_count":
                data.get(
                    "eval_count"
                ),

            "thinking_chars":
                len(
                    message.get(
                        "thinking"
                    )
                    or ""
                ),
        },
    }