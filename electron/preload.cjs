const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("translatorCat", {
  getSnapshot: () => ipcRenderer.invoke("translatorcat:get-snapshot"),
  updateSettings: (settings) => ipcRenderer.invoke("translatorcat:update-settings", settings),
  translateClipboard: () => ipcRenderer.invoke("translatorcat:translate-clipboard"),
  translateText: (text) => ipcRenderer.invoke("translatorcat:translate-text", text),
  setupLocalEngine: () => ipcRenderer.invoke("translatorcat:setup-local-engine"),
  minimize: () => ipcRenderer.invoke("translatorcat:window-minimize"),
  close: () => ipcRenderer.invoke("translatorcat:window-close"),
  placeRight: () => ipcRenderer.invoke("translatorcat:window-place-right"),
  onSnapshot: (callback) => {
    const listener = (_event, snapshot) => callback(snapshot);
    ipcRenderer.on("translatorcat:snapshot", listener);
    return () => ipcRenderer.removeListener("translatorcat:snapshot", listener);
  }
});
