import {
  Clipboard,
  ClipboardCheck,
  Download,
  Languages,
  LocateFixed,
  Minus,
  Pin,
  PinOff,
  RotateCcw,
  Settings,
  X
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import catMascot from "./assets/translator-cat.png";

const LANGUAGES = [
  { value: "auto", label: "Auto" },
  { value: "ko", label: "한국어" },
  { value: "en", label: "English" },
  { value: "ja", label: "日本語" },
  { value: "zh", label: "中文" },
  { value: "es", label: "Español" },
  { value: "fr", label: "Français" },
  { value: "de", label: "Deutsch" },
  { value: "ru", label: "Русский" },
  { value: "vi", label: "Tiếng Việt" },
  { value: "th", label: "ไทย" },
  { value: "id", label: "Indonesia" }
];

const DEFAULT_SETTINGS: TranslatorCatSettings = {
  endpoint: "http://localhost:5000/translate",
  apiKey: "",
  sourceLang: "auto",
  targetLang: "ko",
  autoClipboard: true,
  showOriginal: true,
  keepOnTop: true,
  maxChars: 1400
};

const DEFAULT_SNAPSHOT: TranslatorCatSnapshot = {
  settings: DEFAULT_SETTINGS,
  state: {
    status: "idle",
    sourceText: "",
    translatedText: "",
    error: "",
    sourceLang: "auto",
    targetLang: "ko",
    trigger: "startup",
    updatedAt: Date.now()
  }
};

function App() {
  const [snapshot, setSnapshot] = useState<TranslatorCatSnapshot>(DEFAULT_SNAPSHOT);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [draft, setDraft] = useState<TranslatorCatSettings>(DEFAULT_SETTINGS);
  const [manualText, setManualText] = useState("");

  useEffect(() => {
    let alive = true;

    window.translatorCat.getSnapshot().then((next) => {
      if (!alive) {
        return;
      }

      setSnapshot(next);
      setDraft(next.settings);
    });

    const unsubscribe = window.translatorCat.onSnapshot((next) => {
      setSnapshot(next);
      setDraft((current) => (settingsOpen ? current : next.settings));
    });

    return () => {
      alive = false;
      unsubscribe();
    };
  }, [settingsOpen]);

  const statusText = useMemo(() => {
    if (snapshot.state.status === "translating") {
      return "번역 중";
    }

    if (snapshot.state.status === "done") {
      return "완료";
    }

    if (snapshot.state.status === "error") {
      return "확인 필요";
    }

    return "준비 완료";
  }, [snapshot.state.status]);

  const saveSettings = async (event?: FormEvent) => {
    event?.preventDefault();
    const next = await window.translatorCat.updateSettings(draft);
    setSnapshot(next);
    setSettingsOpen(false);
  };

  const toggleSetting = async (key: keyof TranslatorCatSettings, value: boolean) => {
    const nextSettings = { ...snapshot.settings, [key]: value };
    setDraft(nextSettings);
    const next = await window.translatorCat.updateSettings(nextSettings);
    setSnapshot(next);
  };

  const translateManualText = async (event: FormEvent) => {
    event.preventDefault();
    await window.translatorCat.translateText(manualText);
  };

  const hasResult = snapshot.state.translatedText.trim().length > 0;
  const hasSource = snapshot.state.sourceText.trim().length > 0;
  const isBusy = snapshot.state.status === "translating";
  const isError = snapshot.state.status === "error";

  return (
    <main className={`stage status-${snapshot.state.status}`}>
      <section className="bubble" aria-live="polite">
        <div className="bubbleTop">
          <span className="statusPill">
            <Languages size={15} aria-hidden="true" />
            {statusText}
          </span>
          <div className="topActions">
            <button
              className={`iconButton ${snapshot.settings.autoClipboard ? "isActive" : ""}`}
              type="button"
              title="클립보드 자동 번역"
              onClick={() => toggleSetting("autoClipboard", !snapshot.settings.autoClipboard)}
            >
              {snapshot.settings.autoClipboard ? <ClipboardCheck size={17} /> : <Clipboard size={17} />}
            </button>
            <button
              className="iconButton"
              type="button"
              title="클립보드 번역"
              onClick={() => window.translatorCat.translateClipboard()}
            >
              <RotateCcw size={17} />
            </button>
            <button
              className="iconButton"
              type="button"
              title="설정"
              onClick={() => setSettingsOpen((open) => !open)}
            >
              <Settings size={17} />
            </button>
          </div>
        </div>

        <div className="translationPane">
          {isBusy && <p className="typingDots">...</p>}

          {isError && (
            <p className="errorText">
              {snapshot.state.error || "번역에 실패했습니다."}
            </p>
          )}

          {!isBusy && !isError && hasResult && (
            <>
              {snapshot.settings.showOriginal && hasSource && (
                <p className="sourceText">{snapshot.state.sourceText}</p>
              )}
              <p className="translatedText">{snapshot.state.translatedText}</p>
            </>
          )}

          {!isBusy && !isError && !hasResult && (
            <p className="idleText">nyaa</p>
          )}
        </div>

        <form className="manualForm" onSubmit={translateManualText}>
          <textarea
            value={manualText}
            onChange={(event) => setManualText(event.target.value)}
            maxLength={snapshot.settings.maxChars}
            spellCheck={false}
            aria-label="직접 번역할 텍스트"
          />
          <button className="translateButton" type="submit" disabled={!manualText.trim() || isBusy}>
            번역
          </button>
        </form>
      </section>

      <section className="catDock">
        <div className="windowBar">
          <button className="iconButton" type="button" title="오른쪽 정렬" onClick={() => window.translatorCat.placeRight()}>
            <LocateFixed size={16} />
          </button>
          <button
            className={`iconButton ${snapshot.settings.keepOnTop ? "isActive" : ""}`}
            type="button"
            title="항상 위"
            onClick={() => toggleSetting("keepOnTop", !snapshot.settings.keepOnTop)}
          >
            {snapshot.settings.keepOnTop ? <Pin size={16} /> : <PinOff size={16} />}
          </button>
          <button className="iconButton" type="button" title="최소화" onClick={() => window.translatorCat.minimize()}>
            <Minus size={16} />
          </button>
          <button className="iconButton danger" type="button" title="닫기" onClick={() => window.translatorCat.close()}>
            <X size={16} />
          </button>
        </div>

        <div className={`catWrap ${isBusy ? "isWorking" : ""}`}>
          <img src={catMascot} alt="" draggable={false} />
        </div>
      </section>

      {settingsOpen && (
        <form className="settingsPanel" onSubmit={saveSettings}>
          <div className="settingsGrid">
            <label>
              <span>Source</span>
              <select
                value={draft.sourceLang}
                onChange={(event) => setDraft({ ...draft, sourceLang: event.target.value })}
              >
                {LANGUAGES.map((language) => (
                  <option key={language.value} value={language.value}>
                    {language.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Target</span>
              <select
                value={draft.targetLang}
                onChange={(event) => setDraft({ ...draft, targetLang: event.target.value })}
              >
                {LANGUAGES.filter((language) => language.value !== "auto").map((language) => (
                  <option key={language.value} value={language.value}>
                    {language.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="wideLabel">
            <span>Endpoint</span>
            <input
              value={draft.endpoint}
              onChange={(event) => setDraft({ ...draft, endpoint: event.target.value })}
              spellCheck={false}
            />
          </label>

          <button className="setupButton" type="button" onClick={() => window.translatorCat.setupLocalEngine()}>
            <Download size={15} aria-hidden="true" />
            로컬 엔진 설치
          </button>

          <label className="wideLabel">
            <span>API Key</span>
            <input
              value={draft.apiKey}
              onChange={(event) => setDraft({ ...draft, apiKey: event.target.value })}
              type="password"
              spellCheck={false}
            />
          </label>

          <div className="settingsGrid">
            <label>
              <span>Max</span>
              <input
                value={draft.maxChars}
                onChange={(event) => setDraft({ ...draft, maxChars: Number(event.target.value) })}
                type="number"
                min={120}
                max={5000}
                step={100}
              />
            </label>

            <label className="toggleLine">
              <input
                checked={draft.showOriginal}
                onChange={(event) => setDraft({ ...draft, showOriginal: event.target.checked })}
                type="checkbox"
              />
              <span>원문</span>
            </label>
          </div>

          <button className="saveButton" type="submit">
            저장
          </button>
        </form>
      )}
    </main>
  );
}

export default App;
