import type { Lang } from "../i18n/strings";
import { t } from "../i18n/strings";
import "./Header.css";

type Props = {
  lang: Lang;
  onLangChange: (lang: Lang) => void;
  onOpenSettings: () => void; // opens the AdminDrawer
};

export function Header({ lang, onLangChange, onOpenSettings }: Props) {
  return (
    <header className="app-header">
      {/* Left: app title */}
      <div className="app-header__brand">
        <h1 className="app-header__title">{t("ask_title", lang)}</h1>
      </div>

      <div className="app-header__actions">
        {/* LinkedIn placeholder — not yet implemented */}
        <div className="app-header__user-slot" title={t("linkedin_placeholder", lang)}>
          <div className="app-header__avatar app-header__avatar--placeholder" aria-hidden />
          <span className="app-header__user-label">
            {t("linkedin_placeholder", lang)}
          </span>
        </div>

        {/* Language switcher: English / Hebrew */}
        <label className="app-header__lang">
          <span className="visually-hidden">{t("language", lang)}</span>
          <select
            value={lang}
            onChange={(e) => onLangChange(e.target.value as Lang)}
            aria-label={t("language", lang)}
          >
            <option value="en">English</option>
            <option value="he">עברית</option>
          </select>
        </label>

        {/* Opens the admin/settings drawer */}
        <button
          type="button"
          className="app-header__settings-btn"
          onClick={onOpenSettings}
        >
          {t("settings", lang)}
        </button>
      </div>
    </header>
  );
}
