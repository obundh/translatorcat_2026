from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer

SAMPLES = [
    "REQUIREMENTS FOR THE CONTROL OF ELECTROMAGNETIC INTERFERENCE CHARACTERISTICS OF SUBSYSTEMS AND EQUIPMENT",
    "This standard is approved for use by all Departments and Agencies of the Department of Defense.",
    "The stated interface requirements are considered necessary to provide reasonable confidence that a particular subsystem or equipment complying with these requirements will function within their designated design tolerances when operating in their intended electromagnetic environment (EME).",
    "Electronic, electrical, and electromechanical equipment and subsystems shall comply with the applicable general interface requirements in 4.2.",
    "The EUT shall not exhibit any malfunction, degradation of performance, or deviation from specified indications, beyond the tolerances indicated in the individual equipment or subsystem specification, when subjected to the radiated electric fields listed in Table XI.",
    "This test procedure is used to verify the ability of the EUT and associated cabling to withstand electric fields.",
    "This requirement is primarily intended for EUTs to withstand the fast rise time, free-field transient environment of EMP.",
    "There is a requirement to first test at 10% of the specified limit and then increase the amplitude in steps of 2 or 3 until the specified limit is reached for several reasons.",
    "If any significant level is present, corrections to the setup should be undertaken, such as tightening of connectors and introduction of additional isolation, such as better shielded cables, alternative routing, or shielding barriers.",
]


def run_seq2seq(model_name: str, kind: str):
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    model.eval()
    outputs = []
    for text in SAMPLES:
        kwargs = {}
        source = text
        if kind == "nllb":
            tok.src_lang = "eng_Latn"
            kwargs["forced_bos_token_id"] = tok.convert_tokens_to_ids("kor_Hang")
        inputs = tok(source, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            generated = model.generate(**inputs, max_new_tokens=512, num_beams=4, do_sample=False, **kwargs)
        outputs.append(tok.decode(generated[0], skip_special_tokens=True))
    return outputs


def run_gemma(model_name: str):
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)
    model.eval()
    outputs = []
    for text in SAMPLES:
        prompt = f"<src:en><tgt:ko>\n{text}\n###\n"
        inputs = tok(prompt, return_tensors="pt")
        with torch.no_grad():
            generated = model.generate(**inputs, max_new_tokens=512, do_sample=False, pad_token_id=tok.pad_token_id)
        result = tok.decode(generated[0], skip_special_tokens=True)
        outputs.append(result.split("###")[-1].strip())
    return outputs


def main():
    torch.set_num_threads(4)
    models = [
        ("seongs/ke-t5-base-aihub-koen-translation-integrated-10m-en-to-ko", "ket5"),
        ("facebook/nllb-200-distilled-600M", "nllb"),
        ("sappho192/gemma3-multilingual-translator-270m", "gemma"),
    ]
    report = {"samples": SAMPLES, "models": {}}
    for model_name, kind in models:
        start = time.time()
        print(f"\n===== {model_name} =====", flush=True)
        if kind == "gemma":
            outs = run_gemma(model_name)
        else:
            outs = run_seq2seq(model_name, kind)
        for idx, (src, dst) in enumerate(zip(SAMPLES, outs), 1):
            print(f"[{idx}] EN: {src}\n[{idx}] KO: {dst}\n", flush=True)
        report["models"][model_name] = {"seconds": time.time() - start, "outputs": outs}
        del outs
    Path("model_compare.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
