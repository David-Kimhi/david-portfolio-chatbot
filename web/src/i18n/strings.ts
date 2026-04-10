export type Lang = "en" | "he";

// All UI strings in both languages.
// Use t("key", lang) anywhere in the app instead of hardcoding text.
const STRINGS: Record<string, Record<Lang, string>> = {
  app_title: {
    en: "Professional Chatbot - David Kimhi",
    he: "צ׳אטבוט מקצועי - דוד קמחי",
  },
  admin_settings: {
    en: "Admin Settings",
    he: "הגדרות מנהל",
  },
  login_prompt: {
    en: "Login to upload RAG docs",
    he: "התחבר כדי להעלות מסמכי RAG",
  },
  login_title: {
    en: "Login",
    he: "התחברות",
  },
  email: {
    en: "Email",
    he: "אימייל",
  },
  password: {
    en: "Password",
    he: "סיסמה",
  },
  login: {
    en: "Login",
    he: "התחברות",
  },
  logged_in: {
    en: "Logged in.",
    he: "התחברת בהצלחה.",
  },
  login_failed: {
    en: "Login failed.",
    he: "ההתחברות נכשלה.",
  },
  authenticated: {
    en: "Authenticated",
    he: "מחובר",
  },
  doc_title: {
    en: "Doc title",
    he: "כותרת המסמך",
  },
  source_url: {
    en: "Source URL",
    he: "כתובת (url)",
  },
  paste_text: {
    en: "Paste text to index",
    he: "הדבק טקסט לאינדוקס",
  },
  ingest: {
    en: "Ingest",
    he: "הוסף",
  },
  no_text: {
    en: "No text.",
    he: "לא הוזן טקסט.",
  },
  ingested: {
    en: "Ingested.",
    he: "נוסף בהצלחה.",
  },
  ingest_failed: {
    en: "Ingest failed",
    he: "הוספה נכשלה",
  },
  logout: {
    en: "Logout",
    he: "התנתק",
  },
  ask_title: {
    en: "Ask any question",
    he: "שאל כל שאלה",
  },
  chat_placeholder: {
    en: "Ask about David's professional experience...",
    he: "שאל על הניסיון המקצועי של דוד...",
  },
  sources: {
    en: "Sources",
    he: "מקורות",
  },
  language: {
    en: "Language",
    he: "שפה",
  },
  untitled: {
    en: "Untitled",
    he: "ללא",
  },
  preset_questions_title: {
    he: "שאלות לדוגמה:",
    en: "Example Questions:",
  },
  translate_button: {
    en: "Translate to English",
    he: "תרגם לעברית",
  },
  thinking: {
    en: "Thinking…",
    he: "חושב…",
  },
  settings: {
    en: "Settings",
    he: "הגדרות",
  },
  close: {
    en: "Close",
    he: "סגור",
  },
  try_again: {
    en: "Try again",
    he: "נסה שוב",
  },
  linkedin_placeholder: {
    en: "LinkedIn sign-in (coming soon)",
    he: "התחברות LinkedIn (בקרוב)",
  },
  stream_error: {
    en: "Something went wrong. Check the API and try again.",
    he: "משהו השתבש. בדוק את ה־API ונסה שוב.",
  },
  rate_limited: {
    en: "Too many requests — please wait a moment and try again.",
    he: "יותר מדי בקשות — המתן רגע ונסה שוב.",
  },
  send: {
    en: "Send",
    he: "שלח",
  },
  translation_timeout: {
    en: "Translation timed out. Try again.",
    he: "פג הזמן לתרגום. נסה שוב.",
  },
};

// Looks up a string by key + language. Falls back to the key itself if missing.
export function t(key: string, lang: Lang): string {
  return STRINGS[key]?.[lang] ?? key;
}

// Quick-question chips displayed above the chat input
export const PRESET_QUESTIONS: Record<Lang, string[]> = {
  en: [
    "👉  Summarize David's CV shortly",
    "👉  What is David specialized in?",
    "👉  List David's top technical skills",
    "👉  Describe David's most recent project",
  ],
  he: [
    "👈 סכם את קורות החיים של דוד בקצרה",
    "👈 במה דוד מתמחה?",
    "👈 רשום את הכישורים הטכניים המרכזיים של דוד",
    "👈 תאר את הפרויקט האחרון של דוד",
  ],
};
