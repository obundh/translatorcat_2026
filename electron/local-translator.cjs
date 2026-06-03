const fs = require("fs");
const path = require("path");
const { once } = require("events");
const { Readable } = require("stream");

const MODEL_ID = "sappho192/gemma3-multilingual-translator-270m";
const MODEL_PATH = path.join("sappho192", "gemma3-multilingual-translator-270m");
const MODEL_DATA_BYTES = 801090048;
const MODEL_DATA_URL =
  "https://huggingface.co/sappho192/gemma3-multilingual-translator-270m/resolve/main/onnx/model_q4.onnx_data";

const REQUIRED_LOCAL_FILES = [
  "config.json",
  "generation_config.json",
  "tokenizer.json",
  "tokenizer_config.json",
  path.join("onnx", "model_q4.onnx"),
  path.join("onnx", "model_q4.onnx_data")
];

let translatorPromise;

function hasCompleteLocalModel(rootDir) {
  if (!rootDir) {
    return false;
  }

  const modelRoot = path.join(rootDir, MODEL_PATH);
  return REQUIRED_LOCAL_FILES.every((relativeFile) => {
    const filePath = path.join(modelRoot, relativeFile);
    if (!fs.existsSync(filePath)) {
      return false;
    }

    if (relativeFile.endsWith("model_q4.onnx_data")) {
      return fs.statSync(filePath).size >= MODEL_DATA_BYTES;
    }

    return fs.statSync(filePath).size > 0;
  });
}

async function downloadModelData(cacheRoot, onStatus) {
  const dataPath = path.join(cacheRoot, MODEL_PATH, "onnx", "model_q4.onnx_data");
  const tempPath = `${dataPath}.download`;

  if (fs.existsSync(dataPath) && fs.statSync(dataPath).size >= MODEL_DATA_BYTES) {
    return;
  }

  fs.mkdirSync(path.dirname(dataPath), { recursive: true });
  onStatus?.({ phase: "download", percent: 0 });

  const response = await fetch(MODEL_DATA_URL);
  if (!response.ok || !response.body) {
    throw new Error(`model download failed (${response.status})`);
  }

  const total = Number(response.headers.get("content-length")) || MODEL_DATA_BYTES;
  const fileStream = fs.createWriteStream(tempPath);
  const readable = Readable.fromWeb(response.body);
  let downloaded = 0;
  let lastProgressAt = 0;

  for await (const chunk of readable) {
    downloaded += chunk.length;
    if (!fileStream.write(chunk)) {
      await once(fileStream, "drain");
    }

    const now = Date.now();
    if (now - lastProgressAt > 700) {
      lastProgressAt = now;
      onStatus?.({
        phase: "download",
        percent: Math.min(99, Math.round((downloaded / total) * 100))
      });
    }
  }

  fileStream.end();
  await once(fileStream, "finish");
  fs.renameSync(tempPath, dataPath);
  onStatus?.({ phase: "download", percent: 100 });
}

function cleanGeneratedText(generatedText, prompt) {
  return String(generatedText || "")
    .replace(prompt, "")
    .replace(/<eos>|<pad>|<bos>/g, "")
    .split("###")
    .pop()
    .trim();
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
    await downloadModelData(cacheRoot, onStatus);
  }

  onStatus?.({ phase: "load" });
  return pipeline("text-generation", MODEL_ID, { dtype: "q4" });
}

async function translateEnglishToKorean(text, options) {
  if (!translatorPromise) {
    translatorPromise = loadTranslator(options);
  }

  const translator = await translatorPromise;
  const source = text.trim();
  const prompt = `<src:en><tgt:ko>\n${source}\n###\n`;
  const maxNewTokens = Math.min(220, Math.max(48, Math.ceil(source.length * 1.4)));

  const output = await translator(prompt, {
    max_new_tokens: maxNewTokens,
    do_sample: false,
    return_full_text: false
  });

  const generatedText = Array.isArray(output) ? output[0]?.generated_text : output?.generated_text;
  return cleanGeneratedText(generatedText, prompt) || source;
}

module.exports = {
  MODEL_ID,
  hasCompleteLocalModel,
  translateEnglishToKorean
};

