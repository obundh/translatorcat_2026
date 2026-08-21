from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer

SAMPLES = [
    "GENERAL REQUIREMENTS",
    "Joint procurement.",
    "Filtering (Navy only).",
    "Electronic, electrical, and electromechanical equipment and subsystems shall comply with the applicable general interface requirements in 4.2.",
    "The use of line-to-ground filters for EMI control shall be minimized.",
    "Such filters establish low impedance paths for structure (common mode) currents through the ground plane and can be a major cause of interference in systems, platforms, or installations because the currents can couple into other equipment using the same ground plane.",
    "The operational performance of an equipment or subsystem shall not be degraded, nor shall it malfunction, when all of the units or devices in the equipment or subsystem are operating together at their designed levels of efficiency or their design capability.",
    "RS105, radiated susceptibility, transient electromagnetic field.",
    "This requirement is primarily intended for EUTs to withstand the fast rise time, free-field transient environment of EMP.",
    "The EMP field is simulated in the laboratory using bounded wave TEM radiators such as TEM cells and parallel plate transmission lines.",
    "Since the polarization of the incident EMP field in the installation is not known, the EUT must be tested in all orthogonal axes.",
]


def nllb():
    name="NHNDQ/nllb-finetuned-en2ko"
    tok=AutoTokenizer.from_pretrained(name, src_lang="eng_Latn")
    model=AutoModelForSeq2SeqLM.from_pretrained(name); model.eval()
    rows=[]
    forced=tok.convert_tokens_to_ids("kor_Hang")
    for text in SAMPLES:
        inp=tok(text,return_tensors="pt",truncation=True,max_length=512)
        with torch.inference_mode():
            out=model.generate(**inp,max_new_tokens=384,num_beams=4,do_sample=False,forced_bos_token_id=forced)
        rows.append(tok.decode(out[0],skip_special_tokens=True))
    return rows


def ket5():
    name="seongs/ke-t5-base-aihub-koen-translation-integrated-10m-en-to-ko"
    tok=AutoTokenizer.from_pretrained(name,use_fast=False)
    model=AutoModelForSeq2SeqLM.from_pretrained(name); model.eval()
    rows=[]
    for text in SAMPLES:
        inp=tok(text,return_tensors="pt",truncation=True,max_length=512)
        with torch.inference_mode():
            out=model.generate(**inp,max_new_tokens=384,num_beams=4,do_sample=False)
        rows.append(tok.decode(out[0],skip_special_tokens=True))
    return rows


def gemma():
    name="sappho192/gemma3-multilingual-translator-270m"
    tok=AutoTokenizer.from_pretrained(name)
    model=AutoModelForCausalLM.from_pretrained(name,torch_dtype=torch.float32); model.eval()
    rows=[]
    for text in SAMPLES:
        prompt=f"<src:en><tgt:ko>\n{text}\n###\n"
        inp=tok(prompt,return_tensors="pt")
        with torch.inference_mode():
            out=model.generate(**inp,max_new_tokens=384,do_sample=False,pad_token_id=tok.eos_token_id)
        full=tok.decode(out[0],skip_special_tokens=True)
        rows.append(full[len(prompt):].strip() if full.startswith(prompt) else full.split("###")[-1].strip())
    return rows


def main():
    torch.set_num_threads(4)
    report={"samples":SAMPLES,"models":{}}
    for name,fn in [("NHNDQ NLLB",nllb),("KE-T5",ket5),("Gemma3 translator 270M",gemma)]:
        started=time.time()
        try:
            outputs=fn()
            report["models"][name]={"seconds":time.time()-started,"outputs":outputs}
            print("\n=====",name,"=====")
            for s,o in zip(SAMPLES,outputs): print("EN:",s,"\nKO:",o,"\n")
        except Exception as exc:
            report["models"][name]={"error":repr(exc)}
            print(name,"ERROR",repr(exc),flush=True)
    Path("translation_models_v2.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__=="__main__": main()
