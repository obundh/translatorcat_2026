const { app, BrowserWindow, clipboard, ipcMain, screen } = require("electron");
const fs = require("fs");
const path = require("path");
const { translateEnglishToKorean } = require("./local-translator.cjs");

let mainWindow;
let clipboardTimer;
let lastClipboardText = "";
let lastTranslatedSource = "";
let lastTranslatedResult = "";
let activeTranslationId = 0;
let settings;

const BASE_WINDOW_WIDTH = 360;
const BASE_WINDOW_HEIGHT = 220;
const CLIPBOARD_LIMIT = 500;
const DEFAULT_SETTINGS = {
  scale: 1
};

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function getSettingsPath() {
  return path.join(app.getPath("userData"), "settings.json");
}

function loadSettings() {
  try {
    const raw = fs.readFileSync(getSettingsPath(), "utf8");
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_SETTINGS,
      ...parsed,
      scale: clamp(Number(parsed.scale) || DEFAULT_SETTINGS.scale, 0.7, 1.35)
    };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

function saveSettings() {
  fs.mkdirSync(path.dirname(getSettingsPath()), { recursive: true });
  fs.writeFileSync(getSettingsPath(), JSON.stringify(settings, null, 2));
}

function getWindowSize(scale = settings?.scale || DEFAULT_SETTINGS.scale) {
  return {
    width: Math.round(BASE_WINDOW_WIDTH * scale),
    height: Math.round(BASE_WINDOW_HEIGHT * scale)
  };
}

function resizeWindowForScale(scale) {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  const currentBounds = mainWindow.getBounds();
  const size = getWindowSize(scale);
  mainWindow.setBounds({
    x: currentBounds.x + currentBounds.width - size.width,
    y: currentBounds.y + currentBounds.height - size.height,
    width: size.width,
    height: size.height
  });
}

function trimClipboardText(text) {
  const normalized = text.replace(/\r\n/g, "\n").trim();

  if (normalized.length <= CLIPBOARD_LIMIT) {
    return normalized;
  }

  return `${normalized.slice(0, CLIPBOARD_LIMIT).trimEnd()}\n...`;
}

function looksLikeEnglish(text) {
  if (!text || /[가-힣ㄱ-ㅎㅏ-ㅣ]/.test(text)) {
    return false;
  }

  const letters = text.match(/[A-Za-z]/g)?.length || 0;
  const nonSpace = text.replace(/\s/g, "").length || 1;
  return letters >= 3 && letters / nonSpace > 0.45;
}

function sendBubbleText(payload) {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  mainWindow.webContents.send("clipboard:text", {
    updatedAt: Date.now(),
    ...payload
  });
}

function getModelCacheRoot() {
  if (process.env.TRANSLATORCAT_MODEL_CACHE) {
    return process.env.TRANSLATORCAT_MODEL_CACHE;
  }

  if (app.isPackaged) {
    return path.join(app.getPath("userData"), "models");
  }

  return path.join(process.cwd(), "models", ".cache");
}

function getBundledModelRoot() {
  return app.isPackaged ? path.join(process.resourcesPath, "models") : null;
}

async function translateClipboardText(text, translationId) {
  if (text === lastTranslatedSource) {
    sendBubbleText({
      text: lastTranslatedResult,
      sourceText: text,
      status: "translated"
    });
    return;
  }

  try {
    sendBubbleText({
      text: "로컬 모델 준비 중...",
      sourceText: text,
      status: "loading"
    });

    const translated = await translateEnglishToKorean(text, {
      cacheRoot: getModelCacheRoot(),
      bundledRoot: getBundledModelRoot(),
      onStatus: (status) => {
        if (translationId !== activeTranslationId) {
          return;
        }

        if (status.phase === "download") {
          sendBubbleText({
            text: `로컬 모델 다운로드 중 ${status.percent}%`,
            sourceText: text,
            status: "loading"
          });
        } else if (status.phase === "load") {
          sendBubbleText({
            text: "로컬 모델 여는 중...",
            sourceText: text,
            status: "loading"
          });
        }
      }
    });

    if (translationId !== activeTranslationId) {
      return;
    }

    lastTranslatedSource = text;
    lastTranslatedResult = translated;
    sendBubbleText({
      text: translated,
      sourceText: text,
      status: "translated"
    });
  } catch (error) {
    if (translationId !== activeTranslationId) {
      return;
    }

    sendBubbleText({
      text: `번역 실패\n${text}`,
      sourceText: text,
      status: "error",
      detail: error.message
    });
  }
}

function sendClipboardText(force = false) {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  const text = trimClipboardText(clipboard.readText() || "");
  if (!force && text === lastClipboardText) {
    return;
  }

  lastClipboardText = text;
  activeTranslationId += 1;

  if (looksLikeEnglish(text)) {
    translateClipboardText(text, activeTranslationId);
    return;
  }

  sendBubbleText({
    text,
    sourceText: text,
    status: text ? "idle" : "empty"
  });
}

function startClipboardWatcher() {
  clearInterval(clipboardTimer);
  clipboardTimer = setInterval(sendClipboardText, 650);
  sendClipboardText(true);
}

function createWindow() {
  settings = loadSettings();
  const { workArea } = screen.getPrimaryDisplay();
  const size = getWindowSize();
  const x = Math.max(workArea.x, workArea.x + workArea.width - size.width - 18);
  const y = Math.max(workArea.y, workArea.y + Math.round((workArea.height - size.height) * 0.58));

  mainWindow = new BrowserWindow({
    width: size.width,
    height: size.height,
    x,
    y,
    frame: false,
    transparent: true,
    resizable: false,
    show: false,
    alwaysOnTop: true,
    skipTaskbar: false,
    hasShadow: false,
    backgroundColor: "#00000000",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.setMenuBarVisibility(false);
  mainWindow.setAlwaysOnTop(true, "floating");
  mainWindow.loadFile(path.join(__dirname, "..", "index.html"));

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    startClipboardWatcher();
  });

  mainWindow.on("closed", () => {
    clearInterval(clipboardTimer);
    mainWindow = null;
  });
}

ipcMain.handle("settings:get", () => settings || DEFAULT_SETTINGS);

ipcMain.handle("settings:set-scale", (_event, scale) => {
  settings = {
    ...(settings || DEFAULT_SETTINGS),
    scale: clamp(Number(scale) || DEFAULT_SETTINGS.scale, 0.7, 1.35)
  };
  saveSettings();
  resizeWindowForScale(settings.scale);
  return settings;
});

ipcMain.handle("window:minimize", () => {
  mainWindow?.minimize();
});

ipcMain.handle("window:quit", () => {
  app.quit();
});

app.whenReady().then(createWindow);

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
