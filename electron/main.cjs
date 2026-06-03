const { app, BrowserWindow, clipboard, globalShortcut, ipcMain, screen, Tray, Menu, nativeImage, Notification } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

if (process.platform === "win32") {
  app.setAppUserModelId("com.obundh.translatorcat2026");
}

const LOCAL_ENGINE_PORT = 5127;
const LOCAL_ENGINE_ENDPOINT = `http://127.0.0.1:${LOCAL_ENGINE_PORT}/translate`;

const DEFAULT_SETTINGS = {
  endpoint: LOCAL_ENGINE_ENDPOINT,
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
let tray = null;
let isQuitting = false;
let localEngineProcess = null;

function getSettingsPath() {
  return path.join(app.getPath("userData"), "settings.json");
}

function loadSettings() {
  try {
    const raw = fs.readFileSync(getSettingsPath(), "utf8");
    const parsed = JSON.parse(raw);
    settings = sanitizeSettings({ ...DEFAULT_SETTINGS, ...parsed });
    saveSettings();
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
    endpoint: migrateEndpoint(next.endpoint),
    apiKey: String(next.apiKey || ""),
    sourceLang: String(next.sourceLang || DEFAULT_SETTINGS.sourceLang),
    targetLang: String(next.targetLang || DEFAULT_SETTINGS.targetLang),
    autoClipboard: Boolean(next.autoClipboard),
    showOriginal: Boolean(next.showOriginal),
    keepOnTop: Boolean(next.keepOnTop),
    maxChars: Number.isFinite(maxChars) ? Math.min(Math.max(maxChars, 120), 5000) : DEFAULT_SETTINGS.maxChars
  };
}

function migrateEndpoint(endpoint) {
  const trimmed = String(endpoint || DEFAULT_SETTINGS.endpoint).trim();

  if (
    trimmed === "http://localhost:5000/translate" ||
    trimmed === "http://127.0.0.1:5000/translate" ||
    trimmed === "https://libretranslate.com/translate"
  ) {
    return DEFAULT_SETTINGS.endpoint;
  }

  return trimmed;
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

function truncateForNotification(text, maxLength = 180) {
  const clean = normalizeClipboardText(text);
  if (clean.length <= maxLength) {
    return clean;
  }

  return `${clean.slice(0, maxLength - 1)}...`;
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

function getMascotPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "translator-cat.png");
  }

  return path.join(__dirname, "..", "src", "assets", "translator-cat.png");
}

function getRuntimeRoot() {
  if (app.isPackaged) {
    return process.resourcesPath;
  }

  return path.join(__dirname, "..");
}

function getLocalEngineRoot() {
  return path.join(getRuntimeRoot(), ".translatorcat-engine");
}

function getLocalEnginePythonPath() {
  return path.join(getLocalEngineRoot(), ".venv", "Scripts", "python.exe");
}

function getLocalEngineServerPath() {
  return path.join(getRuntimeRoot(), "scripts", "local-translate-server.py");
}

function getLocalEngineSetupPath() {
  return path.join(getRuntimeRoot(), "scripts", "setup-local-engine.ps1");
}

function isBuiltInLocalEndpoint(endpoint) {
  return normalizeEndpoint(endpoint) === LOCAL_ENGINE_ENDPOINT;
}

function localEngineInstallMessage() {
  return "Local Argos engine is not installed yet. Run `npm run setup:engine`, or open Settings and click Local Engine Install.";
}

async function pingLocalEngine(timeoutMs = 1200) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`http://127.0.0.1:${LOCAL_ENGINE_PORT}/health`, {
      signal: controller.signal
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

function isLocalEngineInstalled() {
  return fs.existsSync(getLocalEnginePythonPath()) && fs.existsSync(getLocalEngineServerPath());
}

function startLocalEngineProcess() {
  if (localEngineProcess && !localEngineProcess.killed) {
    return;
  }

  if (!isLocalEngineInstalled()) {
    throw new Error(localEngineInstallMessage());
  }

  localEngineProcess = spawn(
    getLocalEnginePythonPath(),
    [
      getLocalEngineServerPath(),
      "--serve",
      "--host",
      "127.0.0.1",
      "--port",
      String(LOCAL_ENGINE_PORT)
    ],
    {
      cwd: getRuntimeRoot(),
      env: {
        ...process.env,
        PYTHONUTF8: "1"
      },
      windowsHide: true
    }
  );

  localEngineProcess.on("exit", () => {
    localEngineProcess = null;
  });
}

async function ensureLocalEngineReady() {
  if (!isBuiltInLocalEndpoint(settings.endpoint)) {
    return;
  }

  if (await pingLocalEngine()) {
    return;
  }

  startLocalEngineProcess();

  for (let index = 0; index < 30; index += 1) {
    await new Promise((resolve) => setTimeout(resolve, 400));
    if (await pingLocalEngine(900)) {
      return;
    }
  }

  throw new Error("Local Argos engine did not start. Run `npm run setup:engine` and try again.");
}

function openLocalEngineSetup() {
  const setupPath = getLocalEngineSetupPath();

  if (!fs.existsSync(setupPath)) {
    throw new Error("Local engine setup script was not found.");
  }

  spawn(
    "powershell.exe",
    ["-NoExit", "-ExecutionPolicy", "Bypass", "-File", setupPath],
    {
      cwd: getRuntimeRoot(),
      detached: true,
      windowsHide: false
    }
  );
}

function getTrayImage() {
  const image = nativeImage.createFromPath(getMascotPath());

  if (image.isEmpty()) {
    return nativeImage.createEmpty();
  }

  image.setTemplateImage(false);
  return image.resize({ width: 16, height: 16 });
}

function updateTrayMenu() {
  if (!tray) {
    return;
  }

  const menu = Menu.buildFromTemplate([
    {
      label: "Show TranslatorCat",
      click: () => presentMainWindow()
    },
    {
      label: "Translate Clipboard",
      click: () => translateClipboard("tray")
    },
    {
      label: settings.autoClipboard ? "Disable Clipboard Watch" : "Enable Clipboard Watch",
      click: () => {
        settings = sanitizeSettings({ ...settings, autoClipboard: !settings.autoClipboard });
        saveSettings();
        updateTrayMenu();
        setTranslationState({});
      }
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(menu);
}

function createTray() {
  if (tray) {
    return;
  }

  tray = new Tray(getTrayImage());
  tray.setToolTip("TranslatorCat 2026");
  tray.on("click", () => presentMainWindow());
  tray.on("double-click", () => presentMainWindow());
  updateTrayMenu();
}

function shouldShowTranslationNotification() {
  return Notification.isSupported() && (!mainWindow || mainWindow.isDestroyed() || !mainWindow.isVisible());
}

function showTranslationNotification(title, body) {
  if (!shouldShowTranslationNotification()) {
    return;
  }

  const notification = new Notification({
    title,
    body: truncateForNotification(body),
    silent: false
  });

  notification.on("click", () => presentMainWindow());
  notification.show();
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

function isLocalEndpoint(endpoint) {
  return /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(?::\d+)?\b/i.test(String(endpoint || ""));
}

function explainFetchError(error) {
  const message = String(error && error.message ? error.message : error);

  if (/fetch failed/i.test(message) && isLocalEndpoint(settings.endpoint)) {
    return "Local Argos engine is not running. Run `npm run setup:engine`, or open Settings and click Local Engine Install.";
  }

  if (/fetch failed/i.test(message)) {
    return "Could not reach the translation endpoint. Check the endpoint URL, network, or server status.";
  }

  return message;
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
    await ensureLocalEngineReady();

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
      showTranslationNotification("TranslatorCat", String(translatedText));
    }
  } catch (error) {
    if (runId === translateRunId) {
      const message = error && error.name === "AbortError" ? "Translation request timed out." : explainFetchError(error);
      setTranslationState({
        status: "error",
        sourceText: clippedText,
        translatedText: "",
        error: message,
        trigger
      });
      showTranslationNotification("TranslatorCat needs attention", message);
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

function presentMainWindow() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  if (mainWindow.isMinimized()) {
    mainWindow.restore();
  }

  mainWindow.setSkipTaskbar(false);
  mainWindow.show();
  mainWindow.moveTop();
  mainWindow.focus();
  broadcastSnapshot();
}

function showMainWindow() {
  if (!mainWindow || mainWindow.isDestroyed() || hasShownWindow) {
    return;
  }

  hasShownWindow = true;
  presentMainWindow();

  setTimeout(() => {
    if (settings.autoClipboard) {
      translateClipboard("startup");
    }
  }, 500);
}

function hideMainWindowToTray() {
  createTray();

  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  mainWindow.setSkipTaskbar(true);
  mainWindow.hide();
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

  mainWindow.on("minimize", (event) => {
    event.preventDefault();
    hideMainWindowToTray();
  });

  mainWindow.on("close", (event) => {
    if (isQuitting) {
      return;
    }

    event.preventDefault();
    hideMainWindowToTray();
  });

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

    updateTrayMenu();
    setTranslationState({});
    return getSnapshot();
  });

  ipcMain.handle("translatorcat:translate-clipboard", () => translateClipboard("manual"));
  ipcMain.handle("translatorcat:translate-text", (_event, text) => translateText(text, "manual"));

  ipcMain.handle("translatorcat:setup-local-engine", () => {
    openLocalEngineSetup();
  });

  ipcMain.handle("translatorcat:window-minimize", () => {
    hideMainWindowToTray();
  });

  ipcMain.handle("translatorcat:window-close", () => {
    isQuitting = true;
    app.quit();
  });

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
      presentMainWindow();
      placeWindowOnRight(mainWindow);
    }
  });

  app.whenReady().then(async () => {
    loadSettings();
    createTray();
    registerIpc();
    startClipboardWatcher();
    await createWindow();
    ensureLocalEngineReady().catch((error) => {
      setTranslationState({
        status: "error",
        sourceText: "",
        translatedText: "",
        error: String(error.message || error),
        trigger: "engine"
      });
    });

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
  if (localEngineProcess && !localEngineProcess.killed) {
    localEngineProcess.kill();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
