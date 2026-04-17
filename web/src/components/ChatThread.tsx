import { useRef, useEffect, useState, type MutableRefObject } from "react";
import Markdown from "react-markdown";
import type { Lang } from "../i18n/strings";
import { t, PRESET_QUESTIONS } from "../i18n/strings";
import { detectLanguage } from "../utils/detectLanguage";
import { fetchRelevance } from "../api/client";
import "./ChatThread.css";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  sources?: Record<string, unknown>[];
};

type Props = {
  lang: Lang;
  messages: ChatMessage[];
  isStreaming: boolean;
  onSend: (text: string) => void;
  onTranslate: (messageIndex: number) => void;
  translatingIndex: number | null;
  contextEmbeddingRef: MutableRefObject<number[] | null>;
};

export function ChatThread({
  lang,
  messages,
  isStreaming,
  onSend,
  onTranslate,
  translatingIndex,
  contextEmbeddingRef,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState("");
  const [relevanceScore, setRelevanceScore] = useState<number | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  // Debounced relevance scoring — fires 300ms after the user stops typing
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const text = input.trim();
    if (text.length < 3) {
      setRelevanceScore(null);
      return;
    }
    debounceRef.current = setTimeout(() => {
      fetchRelevance(text, contextEmbeddingRef.current)
        .then((r) => {
          setRelevanceScore(r.score);
          if (r.context_embedding) {
            contextEmbeddingRef.current = r.context_embedding;
          }
        })
        .catch(() => setRelevanceScore(null));
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [input, contextEmbeddingRef]);

  const presets = PRESET_QUESTIONS[lang];
  const lastIdx = messages.length - 1;

  const MAX_CHARS = 200;
  const charsLeft = MAX_CHARS - input.length;
  const isOverLimit = charsLeft < 0;

  // Circle progress ring values
  const RADIUS = 10;
  const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
  const progress = Math.min(input.length / MAX_CHARS, 1);
  const dashOffset = CIRCUMFERENCE * (1 - progress);

  // Color: grey → yellow at 80% → red at 100%+
  const ringColor = isOverLimit
    ? "#e53e3e"
    : charsLeft <= 40
    ? "#f6ad55"
    : "#4f46e5";

  const relevanceBarColor =
    relevanceScore === null
      ? "transparent"
      : relevanceScore > 0.7
        ? "#22c55e"
        : relevanceScore > 0.3
          ? "#eab308"
          : "#ef4444";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || isStreaming || isOverLimit) return;
    setInput("");
    setRelevanceScore(null);
    onSend(q);
  };

  return (
    <div className="chat-thread">
      {/* Message list — or centered preset cards when the chat is empty */}
      <div className="chat-thread__messages">
        {messages.length === 0 ? (
          <div className="chat-thread__presets-wrap">
            <div className="chat-thread__presets" role="list">
              {presets.map((q) => (
                <button
                  key={q}
                  type="button"
                  className="chat-thread__chip"
                  disabled={isStreaming}
                  onClick={() => !isStreaming && onSend(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-thread__msg chat-thread__msg--${msg.role}`}
          >
            <div className="chat-thread__bubble">
              {msg.role === "user" ? (
                <p className="chat-thread__user-text">{msg.content}</p>
              ) : (
                <>
                  {msg.content ? (
                    // Render assistant text as Markdown
                    <div className="chat-thread__md">
                      <Markdown>{msg.content}</Markdown>
                    </div>
                  ) : isStreaming && idx === lastIdx ? (
                    // Show "Thinking…" while waiting for the first chunk
                    <p className="chat-thread__thinking">{t("thinking", lang)}</p>
                  ) : null}

                  {/* Collapsible sources list (only if sources exist) */}
                  {msg.sources && msg.sources.length > 0 && (
                    <details className="chat-thread__sources">
                      <summary>{t("sources", lang)}</summary>
                      <ul>
                        {msg.sources.map((s, i) => {
                          const title =
                            (s.title as string) || "Source";
                          const url = s.url as string | undefined;
                          const hasUrl = !!url?.trim();
                          return (
                            <li key={i}>
                              {hasUrl ? (
                                <a href={url} target="_blank" rel="noreferrer">
                                  {title}
                                </a>
                              ) : (
                                title
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </details>
                  )}

                  {/* Translate button — only shown when message language differs from UI language */}
                  {msg.role === "assistant" &&
                    msg.content &&
                    !(isStreaming && idx === lastIdx) &&
                    translatingIndex !== idx && (
                      <div className="chat-thread__actions">
                        {(() => {
                          const dl = detectLanguage(msg.content);
                          const show =
                            dl !== "unknown" && dl !== lang;
                          if (!show) return null;
                          return (
                            <button
                              type="button"
                              className="chat-thread__translate"
                              onClick={() => onTranslate(idx)}
                            >
                              {t("translate_button", lang)}
                            </button>
                          );
                        })()}
                      </div>
                    )}

                  {/* "Thinking…" spinner while translation is in progress */}
                  {translatingIndex === idx && (
                    <p className="chat-thread__thinking">{t("thinking", lang)}</p>
                  )}
                </>
              )}
            </div>
          </div>
          ))
        )}
        {/* Invisible anchor — scrolled into view after each update */}
        <div ref={bottomRef} />
      </div>

      {/* Text input + send button */}
      <form className="chat-thread__composer" onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("chat_placeholder", lang)}
          disabled={isStreaming}
          aria-label={t("chat_placeholder", lang)}
        />

        {/* Twitter-style character counter — only shown when user starts typing */}
        {input.length > 0 && (
          <div className="chat-thread__char-ring" aria-label={`${charsLeft} characters remaining`}>
            <svg width="28" height="28" viewBox="0 0 28 28">
              {/* Grey background track */}
              <circle cx="14" cy="14" r={RADIUS} fill="none" stroke="#e2e8f0" strokeWidth="2.5" />
              {/* Coloured progress arc */}
              <circle
                cx="14"
                cy="14"
                r={RADIUS}
                fill="none"
                stroke={ringColor}
                strokeWidth="2.5"
                strokeDasharray={CIRCUMFERENCE}
                strokeDashoffset={dashOffset}
                strokeLinecap="round"
                transform="rotate(-90 14 14)"
              />
            </svg>
            {/* Show numeric count only when close to or over the limit */}
            {charsLeft <= 20 && (
              <span className="chat-thread__char-count" style={{ color: ringColor }}>
                {charsLeft}
              </span>
            )}
          </div>
        )}

        <button type="submit" disabled={isStreaming || !input.trim() || isOverLimit}>
          {t("send", lang)}
        </button>
      </form>

      {/* Relevance bar — thin animated strip below the composer */}
      {relevanceScore !== null && (
        <div className="chat-thread__relevance-track">
          <div
            className="chat-thread__relevance-fill"
            style={{
              width: `${Math.round(relevanceScore * 100)}%`,
              backgroundColor: relevanceBarColor,
            }}
          />
        </div>
      )}
    </div>
  );
}
