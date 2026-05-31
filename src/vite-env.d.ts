/// <reference types="vite/client" />

type TranslationStatus = "idle" | "translating" | "done" | "error";

interface TranslatorCatSettings {
  endpoint: string;
  apiKey: string;
  sourceLang: string;
  targetLang: string;
  autoClipboard: boolean;
  showOriginal: boolean;
  keepOnTop: boolean;
  maxChars: number;
}

interface TranslatorCatState {
  status: TranslationStatus;
  sourceText: string;
  translatedText: string;
  error: string;
  sourceLang: string;
  targetLang: string;
  trigger: string;
  updatedAt: number;
}

interface TranslatorCatSnapshot {
  settings: TranslatorCatSettings;
  state: TranslatorCatState;
}

interface TranslatorCatApi {
  getSnapshot: () => Promise<TranslatorCatSnapshot>;
  updateSettings: (settings: Partial<TranslatorCatSettings>) => Promise<TranslatorCatSnapshot>;
  translateClipboard: () => Promise<TranslatorCatSnapshot>;
  translateText: (text: string) => Promise<TranslatorCatSnapshot>;
  minimize: () => Promise<void>;
  close: () => Promise<void>;
  placeRight: () => Promise<void>;
  onSnapshot: (callback: (snapshot: TranslatorCatSnapshot) => void) => () => void;
}

interface Window {
  translatorCat: TranslatorCatApi;
}
