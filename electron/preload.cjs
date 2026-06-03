const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("translatorCat", {
  onClipboardText(callback) {
    const listener = (_event, payload) => callback(payload);
    ipcRenderer.on("clipboard:text", listener);

    return () => {
      ipcRenderer.removeListener("clipboard:text", listener);
    };
  },
  getSettings() {
    return ipcRenderer.invoke("settings:get");
  },
  setScale(scale) {
    return ipcRenderer.invoke("settings:set-scale", scale);
  },
  minimize() {
    return ipcRenderer.invoke("window:minimize");
  },
  quit() {
    return ipcRenderer.invoke("window:quit");
  }
});
