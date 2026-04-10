// Key used to persist the admin JWT in sessionStorage (cleared on tab close)
const JWT_KEY = "portfolio_chat_jwt";

// Returns the backend base URL from the env var VITE_API_URL (empty in dev → uses Vite proxy)
export function getApiBase(): string {
  const raw = import.meta.env.VITE_API_URL?.trim() ?? "";
  return raw.replace(/\/$/, "");
}

// Prepends the base URL to a path, e.g. "/api/ask/stream"
export function apiUrl(path: string): string {
  const base = getApiBase();
  const p = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${p}` : p;
}

export function getStoredJwt(): string | null {
  try {
    return sessionStorage.getItem(JWT_KEY);
  } catch {
    return null;
  }
}

export function setStoredJwt(token: string | null): void {
  try {
    if (token) sessionStorage.setItem(JWT_KEY, token);
    else sessionStorage.removeItem(JWT_KEY);
  } catch {
    /* ignore */
  }
}

// The three event types the backend streams back as NDJSON lines
export type StreamEvent =
  | { type: "chunk"; data: string }                      // partial text from GPT
  | { type: "sources"; data: Record<string, unknown>[] } // RAG sources, sent once at the end
  | { type: "error"; data: string };

// Thrown when the server responds with HTTP 429 (rate limit exceeded)
export class RateLimitError extends Error {
  constructor() {
    super("rate_limited");
    this.name = "RateLimitError";
  }
}

/**
 * Async generator that POSTs to a streaming endpoint and yields parsed events.
 * Reads the response as a raw byte stream, decodes it, and splits on newlines.
 */
export async function* streamNdjson(
  path: string,
  payload: unknown,
  token?: string | null,
): AsyncGenerator<StreamEvent> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/x-ndjson, application/json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    if (res.status === 429) throw new RateLimitError();
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }

  const streamBody = res.body;
  if (!streamBody) throw new Error("No response body");

  // Pipe raw bytes → text → split on newlines → parse JSON per line
  const textReader = streamBody.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";

  while (true) {
    const { done, value } = await textReader.read();

    // If the stream is done, break the loop
    if (done) break;

    // Append the new text to the buffer
    buffer += value;

    // Split the buffer into lines
    const lines = buffer.split("\n");

    // The last line is the incomplete line, so we need to keep it in the buffer
    buffer = lines.pop() ?? ""; // last incomplete line stays in buffer
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        yield JSON.parse(trimmed) as StreamEvent;
      } catch {
        /* skip malformed line */
      }
    }
  }
  // Flush any remaining buffered text
  const tail = buffer.trim();
  if (tail) {
    try {
      yield JSON.parse(tail) as StreamEvent;
    } catch {
      /* ignore */
    }
  }
}

// POST /api/auth/login → returns JWT access token
export async function loginRequest(
  email: string,
  password: string,
): Promise<string> {
  const res = await fetch(apiUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`Login failed: ${res.status}`);
  const data = (await res.json()) as { access_token: string };
  if (!data.access_token) throw new Error("No access_token in response");
  return data.access_token;
}

// POST /api/ingest → sends documents to be embedded and stored in ChromaDB (requires JWT)
export async function ingestRequest(
  items: { id: string; text: string; meta: Record<string, string> }[],
  token: string,
): Promise<void> {
  const res = await fetch(apiUrl("/api/ingest"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(items),
  });
  if (!res.ok) throw new Error(`Ingest failed: ${res.status}`);
}
