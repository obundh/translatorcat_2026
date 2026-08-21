from __future__ import annotations

from pathlib import Path

import ctranslate2
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

MODEL_REPO = "skywood/NHNDQ-nllb-finetuned-en2ko-ct2-float16"
TOKENIZER_REPO = "NHNDQ/nllb-finetuned-en2ko"

SAMPLES = [
    "Electronic, electrical, and electromechanical equipment and subsystems shall comply with the applicable general interface requirements in 4.2.",
    "General requirements for verification shall be in accordance with 4.3.",
    "The use of line-to-ground filters for EMI control shall be minimized.",
    "Such filters establish low impedance paths for structure (common mode) currents through the ground plane and can be a major cause of interference in systems, platforms, or installations because the currents can couple into other equipment using the same ground plane.",
    "The test setup shall be as follows:",
    "Antennas shall be placed 1 meter or greater from the test setup boundary as follows:",
    "For testing from 200 MHz up to 1 GHz, place the antenna in a sufficient number of positions such that the entire area of each EUT enclosure and the first 35 cm of cables and leads interfacing with the EUT enclosure are within the 3 dB beamwidth of the antenna.",
    "This requirement is primarily intended for EUTs to withstand the fast rise time, free-field transient environment of EMP.",
    "The EMP field is simulated in the laboratory using bounded wave TEM radiators such as TEM cells and parallel plate transmission lines.",
    "Since the polarization of the incident EMP field in the installation is not known, the EUT must be tested in all orthogonal axes.",
    "The correlation coefficient should drop to below 0.36 within five shifts of the data.",
    "If any significant level is present, corrections to the setup should be undertaken, such as tightening of connectors and introduction of additional isolation, such as better shielded cables, alternative routing, or shielding barriers.",
]


def main() -> None:
    model_dir = snapshot_download(MODEL_REPO)
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_REPO, src_lang="eng_Latn")
    translator = ctranslate2.Translator(
        model_dir,
        device="cpu",
        compute_type="int8",
        inter_threads=2,
        intra_threads=2,
    )
    token_batches = [tokenizer.convert_ids_to_tokens(tokenizer.encode(x)) for x in SAMPLES]
    prefixes = [["kor_Hang"] for _ in SAMPLES]
    results = translator.translate_batch(
        token_batches,
        target_prefix=prefixes,
        beam_size=4,
        max_decoding_length=512,
        batch_type="tokens",
        max_batch_size=1024,
    )
    lines = []
    for src, result in zip(SAMPLES, results):
        tokens = result.hypotheses[0][1:]
        text = tokenizer.decode(tokenizer.convert_tokens_to_ids(tokens), skip_special_tokens=True)
        lines.extend(["EN: " + src, "KO: " + text.strip(), ""])
    Path("nllb_sample_output.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)


if __name__ == "__main__":
    main()
