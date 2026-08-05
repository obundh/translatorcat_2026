# Third-Party Notices

TranslatorCat uses the following third-party open-source software and model files. Their respective license terms continue to apply.

| Component | Purpose | License |
| --- | --- | --- |
| Electron | Desktop application runtime | MIT |
| electron-builder | Windows application packaging | MIT |
| Transformers.js (`@huggingface/transformers`) | Local model inference | Apache-2.0 |
| ONNX Runtime | Local ONNX model execution | MIT |
| Sharp 0.34.5 | Node image runtime required by Transformers.js | Apache-2.0 |
| `@img/sharp-win32-x64` 0.34.5 / libvips 8.17.3 | Windows native runtime required by Sharp | Apache-2.0 AND LGPL-3.0-or-later |
| `Xenova/m2m100_418M` / `facebook/m2m100_418M` | English-to-Korean translation model | MIT |

The application source code is licensed under the MIT License as described in the root `LICENSE` file.

Packaged Windows builds include the applicable license texts in the `resources/licenses` folder. Exact versions and corresponding-source locations for native components are recorded in `DEPENDENCY_SOURCES.md`. Model weights downloaded after installation remain subject to the model repository's license and notices.
