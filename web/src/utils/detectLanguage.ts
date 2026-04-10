const HEB_RANGE = /[\u0590-\u05FF]/g; // Unicode block for Hebrew letters
const ENG_RANGE = /[A-Za-z]/g;

/**
 * Guesses the dominant language of a string by counting Hebrew vs. English characters.
 * Used to decide whether to show the translate button on an assistant message.
 */
export function detectLanguage(text: string): "he" | "en" | "unknown" {
  if (!text?.trim()) return "unknown";
  const heb = (text.match(HEB_RANGE) ?? []).length;
  const eng = (text.match(ENG_RANGE) ?? []).length;
  if (heb > eng) return "he";
  if (eng > heb) return "en";
  return "unknown";
}
