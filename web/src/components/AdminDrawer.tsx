import { useState, useEffect, useCallback } from "react";
import type { Lang } from "../i18n/strings";
import { t } from "../i18n/strings";
import {
  ingestRequest,
  loginRequest,
  setStoredJwt,
  listDocs,
  deleteDoc,
  updateDoc,
  type DocItem,
} from "../api/client";
import "./AdminDrawer.css";

type Props = {
  open: boolean;
  onClose: () => void;
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  jwt: string | null;
  onJwtChange: (token: string | null) => void;
};

export function AdminDrawer({
  open,
  onClose,
  lang,
  onLangChange,
  jwt,
  onJwtChange,
}: Props) {
  // Login form
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Ingest form
  const [docTitle, setDocTitle] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [pasteText, setPasteText] = useState("");

  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Documents list state
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  // Inline edit state — which doc is expanded and its form values
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editUrl, setEditUrl] = useState("");

  // Fetch all docs whenever the drawer opens and the admin is logged in
  const fetchDocs = useCallback(async () => {
    if (!jwt) return;
    setDocsLoading(true);
    try {
      const fetched = await listDocs(jwt);
      setDocs(fetched);
    } catch {
      // silently ignore — user will see empty list
    } finally {
      setDocsLoading(false);
    }
  }, [jwt]);

  useEffect(() => {
    if (open && jwt) fetchDocs();
  }, [open, jwt, fetchDocs]);

  if (!open) return null;

  // ── Handlers ──────────────────────────────────────────────

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
    setDocs([]);
    setExpandedId(null);
    setNotice(null);
    setError(null);
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jwt) return;
    const text = pasteText.trim();
    if (!text) { setError(t("no_text", lang)); return; }
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
      setDocTitle("");
      setSourceUrl("");
      await fetchDocs(); // refresh the list after adding
    } catch {
      setError(t("ingest_failed", lang));
    }
  };

  const handleDelete = async (id: string) => {
    if (!jwt) return;
    if (!window.confirm(t("delete_confirm", lang))) return;
    setError(null);
    try {
      await deleteDoc(id, jwt);
      setDocs((prev) => prev.filter((d) => d.id !== id));
      if (expandedId === id) setExpandedId(null);
      setNotice(t("deleted", lang));
    } catch {
      setError(t("delete_failed", lang));
    }
  };

  const handleExpandEdit = (doc: DocItem) => {
    if (expandedId === doc.id) {
      setExpandedId(null); // collapse if already open
      return;
    }
    setExpandedId(doc.id);
    setEditText(doc.document);
    setEditUrl(doc.meta.url ?? "");
  };

  const handleUpdate = async (e: React.FormEvent, id: string) => {
    e.preventDefault();
    if (!jwt) return;
    const text = editText.trim();
    if (!text) return;
    setError(null);
    try {
      await updateDoc(id, text, { title: id, url: editUrl.trim() }, jwt);
      setNotice(t("updated", lang));
      setExpandedId(null);
      await fetchDocs(); // refresh list with updated content
    } catch {
      setError(t("update_failed", lang));
    }
  };

  // ── Render ────────────────────────────────────────────────

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
        {/* ── Header row ── */}
        <div className="admin-drawer__head">
          <h2 id="admin-drawer-title">{t("settings", lang)}</h2>
          <button type="button" className="admin-drawer__close" onClick={onClose}>
            {t("close", lang)}
          </button>
        </div>

        <div className="admin-drawer__body">

          {/* ── Section 1: LinkedIn user ── */}
          <div className="admin-drawer__section">
            <p className="admin-drawer__section-title">LinkedIn</p>
            <div className="admin-drawer__user-section">
              <div className="admin-drawer__avatar" aria-hidden />
              <span className="admin-drawer__user-label">
                {t("linkedin_placeholder", lang)}
              </span>
            </div>
          </div>

          <hr className="admin-drawer__divider" />

          {/* ── Section 2: Language ── */}
          <div className="admin-drawer__section">
            <p className="admin-drawer__section-title">{t("language", lang)}</p>
            <label className="admin-drawer__lang-label">
              <select
                value={lang}
                onChange={(e) => onLangChange(e.target.value as Lang)}
                className="admin-drawer__lang-select"
              >
                <option value="en">English</option>
                <option value="he">עברית</option>
              </select>
            </label>
          </div>

          <hr className="admin-drawer__divider" />

          {/* ── Section 3: Admin settings ── */}
          <div className="admin-drawer__section">
            <p className="admin-drawer__section-title">{t("admin_settings", lang)}</p>

            {notice && <p className="admin-drawer__notice">{notice}</p>}
            {error   && <p className="admin-drawer__error">{error}</p>}

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

                {/* ── Add new document ── */}
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
                      rows={4}
                      value={pasteText}
                      onChange={(e) => setPasteText(e.target.value)}
                    />
                  </label>
                  <button type="submit">{t("ingest", lang)}</button>
                </form>

                <hr className="admin-drawer__divider" />

                {/* ── Documents list ── */}
                <p className="admin-drawer__section-title">{t("documents", lang)}</p>

                {docsLoading ? (
                  <p className="admin-drawer__hint">…</p>
                ) : docs.length === 0 ? (
                  <p className="admin-drawer__hint">{t("no_documents", lang)}</p>
                ) : (
                  <ul className="admin-drawer__doc-list">
                    {docs.map((doc) => (
                      <li key={doc.id} className="admin-drawer__doc-item">

                        {/* Row: title + action buttons */}
                        <div className="admin-drawer__doc-row">
                          <span className="admin-drawer__doc-title" title={doc.id}>
                            {doc.meta.title || doc.id}
                          </span>
                          <div className="admin-drawer__doc-actions">
                            <button
                              type="button"
                              className="admin-drawer__doc-btn"
                              onClick={() => handleExpandEdit(doc)}
                            >
                              {expandedId === doc.id ? t("cancel", lang) : t("edit", lang)}
                            </button>
                            <button
                              type="button"
                              className="admin-drawer__doc-btn admin-drawer__doc-btn--danger"
                              onClick={() => handleDelete(doc.id)}
                            >
                              {t("delete", lang)}
                            </button>
                          </div>
                        </div>

                        {/* Inline edit form — shown when row is expanded */}
                        {expandedId === doc.id && (
                          <form
                            className="admin-drawer__form admin-drawer__doc-edit"
                            onSubmit={(e) => handleUpdate(e, doc.id)}
                          >
                            <label>
                              {t("source_url", lang)}
                              <input
                                type="url"
                                value={editUrl}
                                onChange={(e) => setEditUrl(e.target.value)}
                                placeholder="https://"
                              />
                            </label>
                            <label>
                              {t("paste_text", lang)}
                              <textarea
                                rows={5}
                                value={editText}
                                onChange={(e) => setEditText(e.target.value)}
                                required
                              />
                            </label>
                            <button type="submit">{t("save", lang)}</button>
                          </form>
                        )}

                      </li>
                    ))}
                  </ul>
                )}

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

        </div>
      </aside>
    </>
  );
}
