"use client";

import {
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import {
  Bot,
  BrainCircuit,
  LoaderCircle,
  RotateCcw,
  Send,
  ShieldCheck,
  Sparkles,
  Trash2,
  User,
} from "lucide-react";

import type {
  AgentResponse,
} from "@/types/agent";

interface ChatMessage {
  id: number;

  role:
    | "user"
    | "assistant";

  content: string;

  response?:
    AgentResponse;
}

const examples = [
  "Why is RCA-13 diagnosed as terrain propagation?",
  "What action is PLAN-2 recommending?",
  "Why is GX-CELL-001 degraded?",
  "Can Guardian X execute PLAN-2 automatically?",
];

export default function AgentChat() {
  const [
    question,
    setQuestion,
  ] = useState("");

  const [
    caseId,
    setCaseId,
  ] = useState("");

  const [
    planId,
    setPlanId,
  ] = useState("");

  const [
    deviceId,
    setDeviceId,
  ] = useState("");

  const [
    cellId,
    setCellId,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const [
    lastQuestion,
    setLastQuestion,
  ] = useState("");

  const [
    messages,
    setMessages,
  ] = useState<
    ChatMessage[]
  >([
    {
      id: 1,

      role:
        "assistant",

      content:
        "Guardian X Agent is ready. Ask about verified RCA findings, alerts, telemetry, cells, devices, or guarded action plans. The agent is read-only and cannot execute network changes.",
    },
  ]);

  async function submitQuestion(
    submittedQuestion: string
  ) {
    const clean =
      submittedQuestion.trim();

    if (
      !clean ||
      loading
    ) {
      return;
    }

    setError(null);
    setLastQuestion(clean);

    setMessages(
      (current) => [
        ...current,
        {
          id:
            Date.now(),

          role:
            "user",

          content:
            clean,
        },
      ]
    );

    setQuestion("");
    setLoading(true);

    try {
      const body:
        Record<
          string,
          unknown
        > = {
          question:
            clean,
        };

      if (
        caseId.trim()
      ) {
        body.case_id =
          Number(
            caseId
          );
      }

      if (
        planId.trim()
      ) {
        body.action_plan_id =
          Number(
            planId
          );
      }

      if (
        deviceId.trim()
      ) {
        body.device_id =
          deviceId.trim();
      }

      if (
        cellId.trim()
      ) {
        body.cell_id =
          cellId.trim();
      }

      const response =
        await fetch(
          "/api/agent/query",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                body
              ),
          }
        );

      const data =
        await response.json() as
          | AgentResponse
          | {
              detail?: string;
            };

      if (!response.ok) {
        const detail =
          "detail" in data &&
          typeof data.detail ===
            "string"
            ? data.detail
            : "Guardian Agent request failed.";

        throw new Error(
          detail
        );
      }

      const result =
        data as AgentResponse;

      setMessages(
        (current) => [
          ...current,
          {
            id:
              Date.now() + 1,

            role:
              "assistant",

            content:
              result.answer,

            response:
              result,
          },
        ]
      );

    } catch (exception) {
      setError(
        exception instanceof Error
          ? exception.message
          : "Guardian Agent request failed."
      );

    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(
    event:
      FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    void submitQuestion(
      question
    );
  }

  function clearChat() {
    setMessages([
      {
        id:
          Date.now(),

        role:
          "assistant",

        content:
          "Conversation cleared. Guardian X Agent remains read-only and evidence-grounded.",
      },
    ]);

    setError(null);
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_300px]">
      <section className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02]">
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-400/15 bg-cyan-400/10">
              <Sparkles className="h-4 w-4 text-cyan-300" />
            </div>

            <div>
              <p className="text-sm font-medium text-white">
                Guardian X Agent
              </p>

              <p className="mt-0.5 text-[10px] uppercase tracking-[0.14em] text-white/30">
                Evidence-grounded · Read only
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={
              clearChat
            }
            className="rounded-lg border border-white/10 bg-white/5 p-2 text-white/35 transition hover:text-white"
            title="Clear chat"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>

        <div className="h-[520px] space-y-5 overflow-y-auto p-5">
          {messages.map(
            (
              message
            ) => (
              <div
                key={
                  message.id
                }
                className={[
                  "flex gap-3",
                  message.role ===
                  "user"
                    ? "justify-end"
                    : "justify-start",
                ].join(" ")}
              >
                {message.role ===
                "assistant" ? (
                  <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-cyan-400/15 bg-cyan-400/10">
                    <Bot className="h-3.5 w-3.5 text-cyan-300" />
                  </div>
                ) : null}

                <div
                  className={[
                    "max-w-[82%] rounded-2xl px-4 py-3",
                    message.role ===
                    "user"
                      ? "bg-cyan-400/10 text-white/75"
                      : "border border-white/10 bg-black/20 text-white/60",
                  ].join(" ")}
                >
                  <div className="whitespace-pre-wrap text-xs leading-6">
                    {
                      message.content
                    }
                  </div>

                  {message.response ? (
                    <div className="mt-4 border-t border-white/10 pt-3">
                      <div className="flex flex-wrap gap-2">
                        <span className="rounded-full border border-violet-400/15 bg-violet-400/10 px-2 py-1 text-[9px] text-violet-200">
                          {
                            message
                              .response
                              .intent
                          }
                        </span>

                        {message
                          .response
                          .entities
                          .case_id ? (
                          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] text-white/40">
                            RCA-
                            {
                              message
                                .response
                                .entities
                                .case_id
                            }
                          </span>
                        ) : null}

                        {message
                          .response
                          .entities
                          .action_plan_id ? (
                          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] text-white/40">
                            PLAN-
                            {
                              message
                                .response
                                .entities
                                .action_plan_id
                            }
                          </span>
                        ) : null}

                        <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[9px] text-white/40">
                          {
                            message
                              .response
                              .sources
                              .length
                          }{" "}
                          sources
                        </span>

                        <span className="rounded-full border border-emerald-400/15 bg-emerald-400/10 px-2 py-1 text-[9px] text-emerald-200">
                          {
                            message
                              .response
                              .model
                          }
                        </span>
                      </div>
                    </div>
                  ) : null}
                </div>

                {message.role ===
                "user" ? (
                  <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/5">
                    <User className="h-3.5 w-3.5 text-white/45" />
                  </div>
                ) : null}
              </div>
            )
          )}

          {loading ? (
            <div className="flex gap-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-cyan-400/15 bg-cyan-400/10">
                <Bot className="h-3.5 w-3.5 text-cyan-300" />
              </div>

              <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3">
                <div className="flex items-center gap-2">
                  <LoaderCircle className="h-3.5 w-3.5 animate-spin text-cyan-300" />

                  <span className="text-xs text-white/45">
                    Analyzing Guardian X evidence...
                  </span>
                </div>

                <p className="mt-2 text-[10px] text-white/25">
                  Local qwen3.5:4b may take around 1–2 minutes on this machine.
                </p>
              </div>
            </div>
          ) : null}
        </div>

        {error ? (
          <div className="mx-5 mb-4 flex items-center justify-between gap-4 rounded-xl border border-red-400/15 bg-red-400/5 p-3">
            <p className="text-xs text-red-200/80">
              {error}
            </p>

            {lastQuestion ? (
              <button
                type="button"
                disabled={
                  loading
                }
                onClick={() =>
                  void submitQuestion(
                    lastQuestion
                  )
                }
                className="inline-flex shrink-0 items-center gap-1.5 text-[10px] text-red-200"
              >
                <RotateCcw className="h-3 w-3" />
                Retry
              </button>
            ) : null}
          </div>
        ) : null}

        <form
          onSubmit={
            handleSubmit
          }
          className="border-t border-white/10 p-4"
        >
          <div className="flex gap-3">
            <textarea
              value={
                question
              }
              onChange={(
                event
              ) =>
                setQuestion(
                  event.target.value
                )
              }
              rows={2}
              disabled={
                loading
              }
              placeholder="Ask Guardian X about RCA, alerts, telemetry or actions..."
              className="min-h-[64px] flex-1 resize-none rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-xs text-white/70 outline-none placeholder:text-white/20 focus:border-cyan-400/30"
            />

            <button
              type="submit"
              disabled={
                loading ||
                !question.trim()
              }
              className="flex w-14 items-center justify-center rounded-xl border border-cyan-400/20 bg-cyan-400/10 text-cyan-200 transition hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-30"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </form>
      </section>

      <aside className="space-y-4">
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-4 w-4 text-violet-300" />

            <h2 className="text-xs font-medium text-white">
              Optional Context
            </h2>
          </div>

          <div className="mt-4 space-y-3">
            <input
              type="number"
              min="1"
              value={
                caseId
              }
              onChange={(
                event
              ) =>
                setCaseId(
                  event.target.value
                )
              }
              placeholder="RCA case ID"
              className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-white/60 outline-none"
            />

            <input
              type="number"
              min="1"
              value={
                planId
              }
              onChange={(
                event
              ) =>
                setPlanId(
                  event.target.value
                )
              }
              placeholder="Action plan ID"
              className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-white/60 outline-none"
            />

            <input
              value={
                deviceId
              }
              onChange={(
                event
              ) =>
                setDeviceId(
                  event.target.value
                )
              }
              placeholder="GX-DEVICE-001"
              className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-white/60 outline-none"
            />

            <input
              value={
                cellId
              }
              onChange={(
                event
              ) =>
                setCellId(
                  event.target.value
                )
              }
              placeholder="GX-CELL-001"
              className="w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-white/60 outline-none"
            />
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-4">
          <p className="text-[10px] uppercase tracking-[0.15em] text-white/30">
            Example Questions
          </p>

          <div className="mt-3 space-y-2">
            {examples.map(
              (
                example
              ) => (
                <button
                  key={
                    example
                  }
                  type="button"
                  disabled={
                    loading
                  }
                  onClick={() =>
                    setQuestion(
                      example
                    )
                  }
                  className="w-full rounded-lg border border-white/10 bg-black/10 p-3 text-left text-[11px] leading-5 text-white/40 transition hover:border-cyan-400/20 hover:text-white/65"
                >
                  {example}
                </button>
              )
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.04] p-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-300" />

            <p className="text-xs font-medium text-emerald-200">
              Safety Boundary
            </p>
          </div>

          <p className="mt-3 text-[11px] leading-5 text-white/35">
            Verified deterministic RCA remains authoritative. The AI agent cannot override RCA, approve actions, or execute network changes.
          </p>
        </div>
      </aside>
    </div>
  );
}
