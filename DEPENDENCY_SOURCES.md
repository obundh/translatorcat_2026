# Dependency source locations

This file records source locations for the native and copyleft components used
by the versions locked in `package-lock.json`. Keep it with every packaged
build and attach matching source archives when publishing a binary release.

| Distributed component | Locked version | Corresponding source |
| --- | --- | --- |
| `@huggingface/transformers` | 4.2.0 | <https://github.com/huggingface/transformers.js> |
| `onnxruntime-node` | 1.24.3 | <https://github.com/microsoft/onnxruntime> |
| `onnxruntime-web` | 1.26.0-dev.20260416-b7804b056c | <https://github.com/microsoft/onnxruntime> |
| `sharp` | 0.34.5 | <https://github.com/lovell/sharp/tree/v0.34.5> |
| `@img/sharp-win32-x64` | 0.34.5 | <https://github.com/lovell/sharp/tree/v0.34.5/npm/win32-x64> |
| libvips used by the Sharp binary | 8.17.3 | <https://github.com/libvips/libvips/tree/v8.17.3> |
| Sharp libvips packaging scripts | 1.2.4 | <https://github.com/lovell/sharp-libvips/tree/v1.2.4> |

The installed `node_modules/@img/sharp-win32-x64/versions.json` file is the
machine-readable record for the remaining native libraries included in that
package. Its combined Apache-2.0 and LGPL-3.0-or-later license text is copied
to `resources/licenses` by the desktop build.
