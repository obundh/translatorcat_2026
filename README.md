# TranslatorCat 2026

TranslatorCat 2026 is a tiny always-on-top desktop translator. A generated pixel cat floats near the right side of the screen, watches the clipboard, and shows translations in a speech bubble.

![TranslatorCat screenshot](docs/translatorcat-screenshot.png)

## Features

- Floating transparent Electron window with a generated pixel-art cat mascot.
- Automatic clipboard translation.
- Speech-bubble translation result with optional original text.
- Manual text input when you want to translate without touching the clipboard.
- `Ctrl+Shift+Y` global shortcut for instant clipboard translation.
- Tray mode: hide the cat to the system tray and restore it from the tray icon.
- Native desktop notifications for translation results while the cat is hidden.
- Local Argos Translate sidecar engine.
- LibreTranslate-compatible endpoint setting for advanced users.

## Mascot

The cat mascot was generated with the built-in image generation tool, then processed from a chroma-key source into a transparent PNG.

![Generated TranslatorCat mascot](src/assets/translator-cat.png)

Final asset:

```text
src/assets/translator-cat.png
```

Generation prompt summary:

```text
Cute 32-bit pixel art cat mascot for a desktop translation app, sitting upright, warm cream and orange fur, teal scarf accent, small speech-bubble charm, centered full-body sprite, no text, no watermark, on a flat #00ff00 chroma-key background for transparent PNG extraction.
```

## Run

```powershell
npm install
npm run dev
```

For the packaged-production renderer:

```powershell
npm start
```

## Translation Backend

TranslatorCat is designed to translate locally without a user API key. The default endpoint is the local Argos sidecar server started by the Electron app:

```text
http://127.0.0.1:5127/translate
```

Install the local engine once:

```powershell
npm run setup:engine
```

Then run the app:

```powershell
npm start
```

The setup script creates a project-local `.translatorcat-engine` Python virtual environment, installs Argos Translate, and installs the default `en:ko` and `ko:en` models.

If the app says the local Argos engine is not installed, run `npm run setup:engine` or open the app settings and click `로컬 엔진 설치`.

### Offline Engine Direction

For a public installer, the best API-key-free path is to bundle a local translation engine instead of calling a hosted API.

- Argos Translate: open-source offline translation library. Current local engine path.
- LibreTranslate: open-source API server powered by Argos Translate. Still compatible with the endpoint setting, but no longer required.
- Transformers.js: runs compatible Hugging Face models locally in browser/Electron without a server, but model size and Korean quality need testing.
- CTranslate2: fast local inference for Transformer translation models, but packaging native binaries and models is more work.

Current implementation uses a local LibreTranslate-compatible HTTP surface so the UI can stay stable while the engine changes underneath.


## Controls

- Clipboard icon: toggle automatic clipboard translation.
- Rotate icon: translate the current clipboard immediately.
- Pin icon: keep the cat above other windows.
- Locate icon: snap the window back to the right side.
- Minus icon: hide TranslatorCat to the system tray.
- Tray icon: show TranslatorCat, translate clipboard, toggle clipboard watch, or quit.
- `Ctrl+Shift+Y`: translate the current clipboard.

## Build Installer

```powershell
npm run dist
```

Installer output:

```text
release/TranslatorCat 2026 Setup 0.1.0.exe
```

The installer is generated locally and ignored by Git.
