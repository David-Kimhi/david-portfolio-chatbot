import { useCallback, useEffect, useState } from "react";
import type { Lang } from "./i18n/strings";
import { t } from "./i18n/strings";
import {
  getStoredJwt,
  setStoredJwt,
  streamNdjson,
  RateLimitError,
} from "./api/client";
import { Header } from "./components/Header";
import { AdminDrawer } from "./components/AdminDrawer";
import { ChatThread, type ChatMessage } from "./components/ChatThread";
import "./App.css";

export default function App() {
  // Global state
  const [lang, setLang] = useState<Lang>("en");          // active UI language
  const [settingsOpen, setSettingsOpen] = useState(false); // admin drawer visibility
  const [jwt, setJwt] = useState<string | null>(null);   // admin JWT token (null = not logged in)
  const [messages, setMessages] = useState<ChatMessage[]>([]); // full chat history
  const [isStreaming, setIsStreaming] = useState(false);  // true while GPT is responding
  const [translatingIndex, setTranslatingIndex] = useState<number | null>(null); // which message is being translated

  // Load saved JWT from sessionStorage on first render
  useEffect(() => {
    setJwt(getStoredJwt());
  }, []);

  // Sync page lang/dir/title whenever language changes
  useEffect(() => {
    document.documentElement.lang = lang === "he" ? "he" : "en";
    document.documentElement.dir = lang === "he" ? "rtl" : "ltr";
    document.title = t("app_title", lang);
  }, [lang]);

  // Called when user submits a question
  const handleSend = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || isStreaming) return;

      // Append user message + empty assistant placeholder immediately
      setMessages((m) => [
        ...m,
        { role: "user", content: q },
        { role: "assistant", content: "", sources: [] },
      ]);
      setIsStreaming(true);

      let full = "";
      let sources: Record<string, unknown>[] = [];

      try {
        // Stream NDJSON from /api/ask/stream
        // Each event: { type: "chunk", data: "..." } or { type: "sources", data: [...] }
        for await (const ev of streamNdjson(
          "/api/ask/stream",
          { question: q, top_k: 4 },
          jwt,
        )) {
          if (ev.type === "chunk") full += ev.data;
          else if (ev.type === "sources") sources = ev.data;
          else if (ev.type === "error") throw new Error(ev.data);

          // Update the last (assistant) message in real time
          setMessages((m) => {
            const next = [...m];
            const last = next[next.length - 1];
            if (last?.role === "assistant") {
              next[next.length - 1] = {
                ...last,
                content: full,
                sources: [...sources],
              };
            }
            return next;
          });
        }
      } catch (err) {
        // Show a specific message for rate limiting, generic for everything else
        const msg = err instanceof RateLimitError
          ? t("rate_limited", lang)
          : t("stream_error", lang);
        setMessages((m) => {
          const next = [...m];
          const last = next[next.length - 1];
          if (last?.role === "assistant") {
            next[next.length - 1] = { ...last, content: msg, sources: [] };
          }
          return next;
        });
      } finally {
        setIsStreaming(false);
      }
    },
    [isStreaming, jwt, lang],
  );

  // Called when user clicks the translate button on an assistant message
  const handleTranslate = useCallback(
    async (messageIndex: number) => {
      const msg = messages[messageIndex];
      if (!msg || msg.role !== "assistant" || !msg.content.trim()) return;

      setTranslatingIndex(messageIndex);
      let full = "";
      try {
        // Stream translation from /api/translate/stream, target = current UI language
        for await (const ev of streamNdjson(
          "/api/translate/stream",
          { text: msg.content, target_lang: lang },
          jwt,
        )) {
          if (ev.type === "chunk") full += ev.data;
          else if (ev.type === "error") throw new Error(ev.data);
        }
        // Replace the message content with translated text
        setMessages((m) =>
          m.map((x, i) =>
            i === messageIndex ? { ...x, content: full || msg.content } : x,
          ),
        );
      } catch {
        setMessages((m) =>
          m.map((x, i) =>
            i === messageIndex ? { ...x, content: t("stream_error", lang) } : x,
          ),
        );
      } finally {
        setTranslatingIndex(null);
      }
    },
    [messages, lang, jwt],
  );

  // Persist JWT to sessionStorage whenever it changes
  const onJwtChange = (token: string | null) => {
    setJwt(token);
    setStoredJwt(token);
  };

  return (
    <div className="app">
      <Header
        lang={lang}
        onOpenSettings={() => setSettingsOpen(true)}
      />
      <main className="app__main">
        <ChatThread
          lang={lang}
          messages={messages}
          isStreaming={isStreaming}
          onSend={handleSend}
          onTranslate={handleTranslate}
          translatingIndex={translatingIndex}
        />
      </main>
      {/* Slide-in admin panel for login + document ingestion */}
      <AdminDrawer
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        lang={lang}
        onLangChange={setLang}
        jwt={jwt}
        onJwtChange={onJwtChange}
      />
    </div>
  );
}
