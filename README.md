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
- LibreTranslate-compatible endpoint setting.
- Local LibreTranslate Docker setup for self-hosted translation.

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

The app uses a LibreTranslate-compatible endpoint. The default endpoint is:

```text
http://localhost:5000/translate
```

Start a local LibreTranslate container:

```powershell
docker compose up -d
```

This keeps the app API-key-free for users because translation runs on the user's machine.

If the app shows `fetch failed`, the local translation server is not running. Install/start Docker Desktop first, then run `docker compose up -d`, or change the endpoint in settings.

### Offline Engine Direction

For a public installer, the best API-key-free path is to bundle a local translation engine instead of calling a hosted API.

- Argos Translate: open-source offline translation library. Good first embedded engine candidate.
- LibreTranslate: open-source API server powered by Argos Translate. Good for local Docker and local sidecar server modes.
- Transformers.js: runs compatible Hugging Face models locally in browser/Electron without a server, but model size and Korean quality need testing.
- CTranslate2: fast local inference for Transformer translation models, but packaging native binaries and models is more work.

Current implementation uses local LibreTranslate-compatible HTTP so the UI can stay stable while the engine changes underneath.


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
