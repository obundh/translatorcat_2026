const previewSettings: TranslatorCatSettings = {
  endpoint: "https://libretranslate.com/translate",
  apiKey: "",
  sourceLang: "auto",
  targetLang: "ko",
  autoClipboard: true,
  showOriginal: true,
  keepOnTop: true,
  maxChars: 1400
};

let previewSnapshot: TranslatorCatSnapshot = {
  settings: previewSettings,
  state: {
    status: "done",
    sourceText: "TranslatorCat is ready.",
    translatedText: "TranslatorCat 준비 완료.",
    error: "",
    sourceLang: "auto",
    targetLang: "ko",
    trigger: "preview",
    updatedAt: Date.now()
  }
};

const listeners = new Set<(snapshot: TranslatorCatSnapshot) => void>();

function emit() {
  listeners.forEach((listener) => listener(previewSnapshot));
}

export function installBrowserPreviewApi() {
  if (window.translatorCat) {
    return;
  }

  window.translatorCat = {
    getSnapshot: async () => previewSnapshot,
    updateSettings: async (settings) => {
      previewSnapshot = {
        ...previewSnapshot,
        settings: {
          ...previewSnapshot.settings,
          ...settings
        }
      };
      emit();
      return previewSnapshot;
    },
    translateClipboard: async () => {
      previewSnapshot = {
        ...previewSnapshot,
        state: {
          ...previewSnapshot.state,
          status: "done",
          sourceText: "Copied text appears here.",
          translatedText: "복사한 텍스트가 여기에 표시됩니다.",
          trigger: "preview",
          updatedAt: Date.now()
        }
      };
      emit();
      return previewSnapshot;
    },
    translateText: async (text) => {
      previewSnapshot = {
        ...previewSnapshot,
        state: {
          ...previewSnapshot.state,
          status: "done",
          sourceText: text,
          translatedText: text.trim() ? `번역 미리보기: ${text}` : "",
          trigger: "preview",
          updatedAt: Date.now()
        }
      };
      emit();
      return previewSnapshot;
    },
    minimize: async () => undefined,
    close: async () => undefined,
    placeRight: async () => undefined,
    onSnapshot: (callback) => {
      listeners.add(callback);
      return () => listeners.delete(callback);
    }
  };
}
