import { useState } from "react";
import type { Lang } from "../i18n/strings";
import { t } from "../i18n/strings";
import { ingestRequest, loginRequest, setStoredJwt } from "../api/client";
import "./AdminDrawer.css";

type Props = {
  open: boolean;
  onClose: () => void;
  lang: Lang;
  jwt: string | null;       // null = not logged in
  onJwtChange: (token: string | null) => void;
};

export function AdminDrawer({
  open,
  onClose,
  lang,
  jwt,
  onJwtChange,
}: Props) {
  // Login form fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Ingest form fields
  const [docTitle, setDocTitle] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [pasteText, setPasteText] = useState("");

  const [notice, setNotice] = useState<string | null>(null); // success message
  const [error, setError] = useState<string | null>(null);   // error message

  // Don't render anything when the drawer is closed
  if (!open) return null;

  // POST /api/auth/login → stores JWT on success
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    try {
      const token = await loginRequest(email, password);
      setStoredJwt(token);
      onJwtChange(token);
      setNotice(t("logged_in", lang));
      setPassword("");
    } catch {
      setError(t("login_failed", lang));
    }
  };

  const handleLogout = () => {
    setStoredJwt(null);
    onJwtChange(null);
    setNotice(null);
    setError(null);
  };

  // POST /api/ingest → sends text to be embedded and stored in ChromaDB
  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jwt) return;
    const text = pasteText.trim();
    if (!text) {
      setError(t("no_text", lang));
      return;
    }
    setError(null);
    setNotice(null);
    const title = docTitle.trim() || t("untitled", lang);
    try {
      await ingestRequest(
        [{ id: title, text, meta: { title, url: sourceUrl.trim() } }],
        jwt,
      );
      setNotice(t("ingested", lang));
      setPasteText("");
    } catch {
      setError(t("ingest_failed", lang));
    }
  };

  return (
    <>
      {/* Semi-transparent backdrop — click to close */}
      <button
        type="button"
        className="admin-drawer__backdrop"
        aria-label={t("close", lang)}
        onClick={onClose}
      />
      <aside
        className="admin-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="admin-drawer-title"
      >
        <div className="admin-drawer__head">
          <h2 id="admin-drawer-title">{t("admin_settings", lang)}</h2>
          <button
            type="button"
            className="admin-drawer__close"
            onClick={onClose}
          >
            {t("close", lang)}
          </button>
        </div>

        <div className="admin-drawer__body">
          {notice && <p className="admin-drawer__notice">{notice}</p>}
          {error && <p className="admin-drawer__error">{error}</p>}

          {/* Show login form when not authenticated, ingest form when authenticated */}
          {!jwt ? (
            <>
              <p className="admin-drawer__hint">{t("login_prompt", lang)}</p>
              <form onSubmit={handleLogin} className="admin-drawer__form">
                <label>
                  {t("email", lang)}
                  <input
                    type="email"
                    autoComplete="username"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </label>
                <label>
                  {t("password", lang)}
                  <input
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </label>
                <button type="submit">{t("login", lang)}</button>
              </form>
            </>
          ) : (
            <>
              <p className="admin-drawer__hint">{t("authenticated", lang)}</p>
              {/* Ingest form: paste any text → gets embedded and added to ChromaDB */}
              <form onSubmit={handleIngest} className="admin-drawer__form">
                <label>
                  {t("doc_title", lang)}
                  <input
                    value={docTitle}
                    onChange={(e) => setDocTitle(e.target.value)}
                    placeholder={t("untitled", lang)}
                  />
                </label>
                <label>
                  {t("source_url", lang)}
                  <input
                    type="url"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    placeholder="https://"
                  />
                </label>
                <label>
                  {t("paste_text", lang)}
                  <textarea
                    rows={5}
                    value={pasteText}
                    onChange={(e) => setPasteText(e.target.value)}
                  />
                </label>
                <button type="submit">{t("ingest", lang)}</button>
              </form>
              <button
                type="button"
                className="admin-drawer__logout"
                onClick={handleLogout}
              >
                {t("logout", lang)}
              </button>
            </>
          )}
        </div>
      </aside>
    </>
  );
}
