import argparse
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


def _load_argos():
    try:
        import argostranslate.package
        import argostranslate.translate
    except Exception as exc:
        return None, None, exc

    return argostranslate.package, argostranslate.translate, None


def _installed_pair_exists(translate_module: Any, source: str, target: str) -> bool:
    try:
        languages = translate_module.get_installed_languages()
        from_language = next((language for language in languages if language.code == source), None)
        to_language = next((language for language in languages if language.code == target), None)

        if not from_language or not to_language:
            return False

        from_language.get_translation(to_language)
        return True
    except Exception:
        return False


def install_pairs(pairs: list[str]) -> int:
    package_module, translate_module, import_error = _load_argos()

    if import_error:
        print(f"Argos Translate is not installed: {import_error}", file=sys.stderr)
        return 2

    package_module.update_package_index()
    available_packages = package_module.get_available_packages()

    for pair in pairs:
        source, target = pair.split(":", 1)
        if _installed_pair_exists(translate_module, source, target):
            print(f"{source}:{target} already installed")
            continue

        package = next(
            (
                candidate
                for candidate in available_packages
                if candidate.from_code == source and candidate.to_code == target
            ),
            None,
        )

        if not package:
            print(f"No Argos package found for {source}:{target}", file=sys.stderr)
            continue

        print(f"Downloading {source}:{target}...")
        download_path = package.download()
        print(f"Installing {source}:{target}...")
        package_module.install_from_path(download_path)

    return 0


def choose_source(text: str, source: str, target: str) -> str:
    if source and source != "auto":
        return source

    if re.search(r"[가-힣]", text):
        return "en" if target == "ko" else "ko"

    if target == "en":
        return "ko"

    return "en"


def translate_text(text: str, source: str, target: str) -> str:
    _package_module, translate_module, import_error = _load_argos()

    if import_error:
        raise RuntimeError(
            "Local Argos engine is not installed. Run `npm run setup:engine` first."
        ) from import_error

    actual_source = choose_source(text, source, target)
    languages = translate_module.get_installed_languages()
    from_language = next((language for language in languages if language.code == actual_source), None)
    to_language = next((language for language in languages if language.code == target), None)

    if not from_language or not to_language:
        raise RuntimeError(
            f"Translation model {actual_source}:{target} is not installed. "
            "Run `npm run setup:engine` or install the required Argos package."
        )

    translation = from_language.get_translation(to_language)
    return translation.translate(text)


class TranslateHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/health":
            _package_module, translate_module, import_error = _load_argos()
            installed = []
            if translate_module and not import_error:
                try:
                    installed = [
                        language.code
                        for language in translate_module.get_installed_languages()
                    ]
                except Exception:
                    installed = []

            self._send_json(
                200,
                {
                    "ok": import_error is None,
                    "engine": "argos",
                    "installedLanguages": installed,
                    "error": str(import_error) if import_error else "",
                },
            )
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/translate":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body or "{}")
            query = payload.get("q", "")
            source = str(payload.get("source", "auto"))
            target = str(payload.get("target", "ko"))

            if isinstance(query, list):
                translated = [translate_text(str(item), source, target) for item in query]
            else:
                translated = translate_text(str(query), source, target)

            self._send_json(200, {"translatedText": translated})
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        print(format % args, file=sys.stderr)


def serve(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), TranslateHandler)
    print(f"TranslatorCat local Argos server listening on http://{host}:{port}", flush=True)
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5127)
    parser.add_argument("--install", nargs="*", default=[])
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()

    if args.install:
        return install_pairs(args.install)

    serve(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
