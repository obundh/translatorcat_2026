const { app, BrowserWindow, clipboard, globalShortcut, ipcMain, screen } = require("electron");
const fs = require("node:fs");
const path = require("node:path");

const DEFAULT_SETTINGS = {
  endpoint: "https://libretranslate.com/translate",
  apiKey: "",
  sourceLang: "auto",
  targetLang: "ko",
  autoClipboard: true,
  showOriginal: true,
  keepOnTop: true,
  maxChars: 1400
};

const DEFAULT_STATE = {
  status: "idle",
  sourceText: "",
  translatedText: "",
  error: "",
  sourceLang: "auto",
  targetLang: "ko",
  trigger: "startup",
  updatedAt: Date.now()
};

let mainWindow = null;
let settings = { ...DEFAULT_SETTINGS };
let translationState = { ...DEFAULT_STATE };
let clipboardTimer = null;
let clipboardDebounce = null;
let lastClipboardText = "";
let translateRunId = 0;
let hasShownWindow = false;

function getSettingsPath() {
  return path.join(app.getPath("userData"), "settings.json");
}

function loadSettings() {
  try {
    const raw = fs.readFileSync(getSettingsPath(), "utf8");
    const parsed = JSON.parse(raw);
    settings = sanitizeSettings({ ...DEFAULT_SETTINGS, ...parsed });
  } catch {
    settings = { ...DEFAULT_SETTINGS };
  }
}

function saveSettings() {
  fs.mkdirSync(app.getPath("userData"), { recursive: true });
  fs.writeFileSync(getSettingsPath(), JSON.stringify(settings, null, 2), "utf8");
}

function sanitizeSettings(next) {
  const maxChars = Number(next.maxChars);
  return {
    endpoint: String(next.endpoint || DEFAULT_SETTINGS.endpoint).trim(),
    apiKey: String(next.apiKey || ""),
    sourceLang: String(next.sourceLang || DEFAULT_SETTINGS.sourceLang),
    targetLang: String(next.targetLang || DEFAULT_SETTINGS.targetLang),
    autoClipboard: Boolean(next.autoClipboard),
    showOriginal: Boolean(next.showOriginal),
    keepOnTop: Boolean(next.keepOnTop),
    maxChars: Number.isFinite(maxChars) ? Math.min(Math.max(maxChars, 120), 5000) : DEFAULT_SETTINGS.maxChars
  };
}

function getSnapshot() {
  return {
    settings,
    state: translationState
  };
}

function broadcastSnapshot() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  mainWindow.webContents.send("translatorcat:snapshot", getSnapshot());
}

function setTranslationState(next) {
  translationState = {
    ...translationState,
    ...next,
    sourceLang: settings.sourceLang,
    targetLang: settings.targetLang,
    updatedAt: Date.now()
  };
  broadcastSnapshot();
}

function normalizeEndpoint(endpoint) {
  const trimmed = String(endpoint || "").trim();
  if (!trimmed) {
    return DEFAULT_SETTINGS.endpoint;
  }

  if (/\/translate\/?$/.test(trimmed)) {
    return trimmed.replace(/\/$/, "");
  }

  return `${trimmed.replace(/\/$/, "")}/translate`;
}

function normalizeClipboardText(text) {
  return String(text || "")
    .replace(/\r\n/g, "\n")
    .replace(/\u0000/g, "")
    .trim();
}

function buildTranslateBody(text) {
  const body = {
    q: text,
    source: settings.sourceLang,
    target: settings.targetLang,
    format: "text"
  };

  if (settings.apiKey.trim()) {
    body.api_key = settings.apiKey.trim();
  }

  return body;
}

async function translateText(rawText, trigger = "manual") {
  const cleanText = normalizeClipboardText(rawText);

  if (!cleanText) {
    setTranslationState({
      status: "idle",
      sourceText: "",
      translatedText: "",
      error: "",
      trigger
    });
    return getSnapshot();
  }

  const clippedText = cleanText.length > settings.maxChars ? cleanText.slice(0, settings.maxChars) : cleanText;
  const runId = ++translateRunId;

  setTranslationState({
    status: "translating",
    sourceText: clippedText,
    translatedText: "",
    error: "",
    trigger
  });

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 22000);

  try {
    const response = await fetch(normalizeEndpoint(settings.endpoint), {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(buildTranslateBody(clippedText)),
      signal: controller.signal
    });

    const payloadText = await response.text();
    let payload = {};

    try {
      payload = payloadText ? JSON.parse(payloadText) : {};
    } catch {
      payload = {};
    }

    if (!response.ok) {
      const serverMessage = payload.error || payload.message || payloadText.slice(0, 180);
      throw new Error(serverMessage || `HTTP ${response.status}`);
    }

    const translatedText = payload.translatedText || payload.translation || payload.translated_text;

    if (!translatedText) {
      throw new Error("Translation response did not include translatedText.");
    }

    if (runId === translateRunId) {
      setTranslationState({
        status: "done",
        sourceText: clippedText,
        translatedText: String(translatedText),
        error: "",
        trigger
      });
    }
  } catch (error) {
    if (runId === translateRunId) {
      const message = error && error.name === "AbortError" ? "Translation request timed out." : String(error.message || error);
      setTranslationState({
        status: "error",
        sourceText: clippedText,
        translatedText: "",
        error: message,
        trigger
      });
    }
  } finally {
    clearTimeout(timeout);
  }

  return getSnapshot();
}

function translateClipboard(trigger = "manual") {
  const text = clipboard.readText("clipboard");
  return translateText(text, trigger);
}

function startClipboardWatcher() {
  if (clipboardTimer) {
    return;
  }

  clipboardTimer = setInterval(() => {
    if (!settings.autoClipboard) {
      return;
    }

    const text = normalizeClipboardText(clipboard.readText("clipboard"));
    if (!text || text === lastClipboardText) {
      return;
    }

    lastClipboardText = text;
    clearTimeout(clipboardDebounce);
    clipboardDebounce = setTimeout(() => translateText(text, "clipboard"), 360);
  }, 900);
}

function placeWindowOnRight(win) {
  const display = screen.getDisplayNearestPoint(screen.getCursorScreenPoint());
  const area = display.workArea;
  const bounds = win.getBounds();
  const x = Math.round(area.x + area.width - bounds.width - 20);
  const y = Math.round(area.y + area.height / 2 - bounds.height / 2);
  win.setPosition(x, Math.max(area.y + 12, y), false);
}

function showMainWindow() {
  if (!mainWindow || mainWindow.isDestroyed() || hasShownWindow) {
    return;
  }

  hasShownWindow = true;
  mainWindow.show();
  mainWindow.moveTop();
  mainWindow.focus();
  broadcastSnapshot();

  setTimeout(() => {
    if (settings.autoClipboard) {
      translateClipboard("startup");
    }
  }, 500);
}

async function createWindow() {
  const display = screen.getPrimaryDisplay();
  const area = display.workArea;
  const width = 500;
  const height = 370;

  mainWindow = new BrowserWindow({
    width,
    height,
    x: Math.round(area.x + area.width - width - 20),
    y: Math.round(area.y + area.height / 2 - height / 2),
    minWidth: width,
    minHeight: height,
    maxWidth: width,
    maxHeight: height,
    frame: false,
    transparent: true,
    resizable: false,
    movable: true,
    show: true,
    skipTaskbar: false,
    hasShadow: false,
    backgroundColor: "#00000000",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  mainWindow.setAlwaysOnTop(settings.keepOnTop, "floating");
  mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  mainWindow.once("ready-to-show", showMainWindow);
  mainWindow.webContents.once("did-finish-load", showMainWindow);
  setTimeout(showMainWindow, 1200);

  mainWindow.on("closed", () => {
    mainWindow = null;
    hasShownWindow = false;
  });

  mainWindow.webContents.setWindowOpenHandler(() => ({ action: "deny" }));

  const distIndex = path.join(__dirname, "..", "dist", "index.html");
  const devUrl = process.env.VITE_DEV_SERVER_URL || "";

  if (devUrl) {
    try {
      await mainWindow.loadURL(devUrl);
    } catch {
      await mainWindow.loadFile(distIndex);
    }
  } else {
    await mainWindow.loadFile(distIndex);
  }
}

function registerIpc() {
  ipcMain.handle("translatorcat:get-snapshot", () => getSnapshot());

  ipcMain.handle("translatorcat:update-settings", (_event, nextSettings) => {
    settings = sanitizeSettings({ ...settings, ...nextSettings });
    saveSettings();

    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.setAlwaysOnTop(settings.keepOnTop, "floating");
    }

    setTranslationState({});
    return getSnapshot();
  });

  ipcMain.handle("translatorcat:translate-clipboard", () => translateClipboard("manual"));
  ipcMain.handle("translatorcat:translate-text", (_event, text) => translateText(text, "manual"));

  ipcMain.handle("translatorcat:window-minimize", () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.minimize();
    }
  });

  ipcMain.handle("translatorcat:window-close", () => app.quit());

  ipcMain.handle("translatorcat:window-place-right", () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      placeWindowOnRight(mainWindow);
    }
  });
}

const gotLock = app.requestSingleInstanceLock();

if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) {
        mainWindow.restore();
      }
      mainWindow.showInactive();
      placeWindowOnRight(mainWindow);
    }
  });

  app.whenReady().then(async () => {
    loadSettings();
    registerIpc();
    startClipboardWatcher();
    await createWindow();

    globalShortcut.register("CommandOrControl+Shift+Y", () => {
      translateClipboard("shortcut");
    });

    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });
}

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
  clearInterval(clipboardTimer);
  clearTimeout(clipboardDebounce);
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
