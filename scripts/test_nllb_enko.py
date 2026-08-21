from __future__ import annotations

from pathlib import Path

import ctranslate2
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

MODEL_ID = "skywood/NHNDQ-nllb-finetuned-en2ko-ct2-float16"
TOKENIZER_ID = "NHNDQ/nllb-finetuned-en2ko"

SAMPLES = [
    "Electronic, electrical, and electromechanical equipment and subsystems shall comply with the applicable general interface requirements in 4.2.",
    "The use of line-to-ground filters for EMI control shall be minimized.",
    "Such filters establish low impedance paths for structure (common mode) currents through the ground plane and can be a major cause of interference in systems, platforms, or installations.",
    "When it is demonstrated that a CI selected by the contractor is responsible for equipment or subsystems failing to meet the contractual EMI requirements, either the CI shall be modified or replaced or interference suppression measures shall be employed.",
    "Antennas shall be placed 1 meter or greater from the test setup boundary as follows:",
    "For testing from 200 MHz up to 1 GHz, place the antenna in a sufficient number of positions such that the entire area of each EUT enclosure and the first 35 cm of cables and leads interfacing with the EUT enclosure are within the 3 dB beamwidth of the antenna.",
    "This requirement is primarily intended for EUTs to withstand the fast rise time, free-field transient environment of EMP.",
    "The EMP field is simulated in the laboratory using bounded wave TEM radiators such as TEM cells and parallel plate transmission lines.",
    "If the chamber time constant is greater than 0.4 of the pulse width of the modulation waveform, absorber material must be added to the chamber, or the pulse width must be increased.",
    "The correlation coefficient should drop to below 0.36 within five shifts of the data.",
]


def encode(tokenizer, text: str):
    ids = tokenizer(text, add_special_tokens=True)["input_ids"]
    return tokenizer.convert_ids_to_tokens(ids)


def main():
    model_dir = snapshot_download(MODEL_ID)
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_ID, src_lang="eng_Latn")
    translator = ctranslate2.Translator(model_dir, device="cpu", compute_type="int8_float32", inter_threads=2, intra_threads=4)
    source = [encode(tokenizer, text) for text in SAMPLES]
    results = translator.translate_batch(
        source,
        target_prefix=[["kor_Hang"] for _ in source],
        beam_size=4,
        max_decoding_length=512,
        batch_type="tokens",
        max_batch_size=1024,
        return_scores=True,
    )
    for idx, (src, result) in enumerate(zip(SAMPLES, results), start=1):
        tokens = result.hypotheses[0]
        ids = tokenizer.convert_tokens_to_ids(tokens)
        out = tokenizer.decode(ids, skip_special_tokens=True)
        print(f"[{idx}] EN: {src}")
        print(f"[{idx}] KO: {out}")
        print(f"[{idx}] SCORE: {result.scores[0] if result.scores else None}")
        print()


if __name__ == "__main__":
    main()
