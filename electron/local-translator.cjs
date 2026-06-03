const fs = require("fs");
const path = require("path");

const MODEL_ID = "Xenova/m2m100_418M";
const MODEL_PATH = path.join("Xenova", "m2m100_418M");
const MODEL_DTYPE = "q8";

const REQUIRED_LOCAL_FILES = [
  "config.json",
  "generation_config.json",
  "tokenizer.json",
  "tokenizer_config.json",
  path.join("onnx", "encoder_model_quantized.onnx"),
  path.join("onnx", "decoder_model_merged_quantized.onnx")
];

const SINGLE_WORD_TRANSLATIONS = new Map([
  ["apple", "사과"],
  ["apples", "사과"]
]);

let translatorPromise;
let lastProgressKey = "";

function hasCompleteLocalModel(rootDir) {
  if (!rootDir) {
    return false;
  }

  const modelRoot = path.join(rootDir, MODEL_PATH);
  return REQUIRED_LOCAL_FILES.every((relativeFile) => {
    const filePath = path.join(modelRoot, relativeFile);
    return fs.existsSync(filePath) && fs.statSync(filePath).size > 0;
  });
}

function getDirectTranslation(text) {
  const normalized = text.trim();
  if (!/^[a-z]+s?$/u.test(normalized)) {
    return null;
  }

  return SINGLE_WORD_TRANSLATIONS.get(normalized) || null;
}

function createProgressHandler(onStatus) {
  return (progress) => {
    if (!onStatus) {
      return;
    }

    if (progress.status === "progress") {
      const percent = Math.round(progress.progress || 0);
      const progressKey = `${progress.file}:${Math.floor(percent / 5) * 5}`;
      if (progressKey === lastProgressKey) {
        return;
      }

      lastProgressKey = progressKey;
      onStatus({
        phase: "download",
        file: progress.file,
        percent
      });
      return;
    }

    if (progress.status === "ready") {
      onStatus({ phase: "load" });
    }
  };
}

async function loadTranslator(options) {
  const { cacheRoot, bundledRoot, onStatus } = options;
  const { pipeline, env } = await import("@huggingface/transformers");

  if (hasCompleteLocalModel(bundledRoot)) {
    env.localModelPath = bundledRoot;
    env.allowRemoteModels = false;
  } else if (hasCompleteLocalModel(cacheRoot)) {
    env.localModelPath = cacheRoot;
    env.allowRemoteModels = false;
  } else {
    env.cacheDir = cacheRoot;
    env.allowRemoteModels = true;
  }

  onStatus?.({ phase: "load" });
  return pipeline("translation", MODEL_ID, {
    dtype: MODEL_DTYPE,
    progress_callback: createProgressHandler(onStatus)
  });
}

async function translateEnglishToKorean(text, options) {
  const source = text.trim();
  const directTranslation = getDirectTranslation(source);
  if (directTranslation) {
    return directTranslation;
  }

  if (!translatorPromise) {
    translatorPromise = loadTranslator(options);
  }

  const translator = await translatorPromise;
  const output = await translator(source, {
    src_lang: "en",
    tgt_lang: "ko",
    max_new_tokens: Math.min(220, Math.max(32, Math.ceil(source.length * 1.25)))
  });

  const translation = Array.isArray(output) ? output[0]?.translation_text : output?.translation_text;
  return String(translation || source).trim();
}

module.exports = {
  MODEL_ID,
  hasCompleteLocalModel,
  translateEnglishToKorean
};
