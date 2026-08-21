from __future__ import annotations

import json
import re
import time

import milstd461h_v2_revision as revision

base = revision.base


# Final terminology pass applied after the generic NLLB normalization.
FINAL_REPLACEMENTS = {
    "라인 대 접지": "선-접지",
    "라인 대 지면": "선-접지",
    "라인-접지": "선-접지",
    "라인-대-지면": "선-접지",
    "라인 투 지면": "선-접지",
    "지면을 통한 구조": "접지면을 통한 구조",
    "동일한 지면": "동일한 접지면",
    "각 라인에 대한": "각 선의",
    "마이크로파라드": "마이크로패럿",
    "마이크로패러드": "마이크로패럿",
    "마이크로파드": "마이크로패럿",
    "마이크로 패럿": "마이크로패럿",
    "기술 매뉴얼": "기술교범",
    "계약상의 EMI": "계약상 EMI",
    "DoD 활동": "DoD 기관",
    "감응도": "내성",
    "3 dB 빔 폭": "3 dB 빔폭",
    "3dB 빔 폭": "3 dB 빔폭",
    "전기장 센서": "전계 센서",
    "전기 필드 센서": "전계 센서",
    "전기장": "전계",
    "전기 필드": "전계",
    "수신기 측정": "측정 수신기",
    "파워 미터": "전력계",
    "방향 커플러": "방향성 결합기",
    "리버버레이션 챔버": "잔향실",
    "반향 챔버": "잔향실",
    "모드 튜닝": "모드 조정",
    "모드-튜닝": "모드 조정",
    "테스트 설정": "시험 구성",
    "테스트 절차": "시험 절차",
    "테스트 장비": "시험 장비",
    "데이터 프레젠테이션": "데이터 제시",
    "군사 시험 및 인증": "군용 시험 및 인증",
    "EMC 군사 시험": "EMC 군용 시험",
    "요구 사항": "요구사항",
    "하위 시스템": "하위체계",
    "서브시스템": "하위체계",
}


def final_normalize(text: str) -> str:
    out = base.normalize_translation(text)
    for old, new in FINAL_REPLACEMENTS.items():
        out = out.replace(old, new)
    out = re.sub(r"\bHz\s*\(Hz\)", "Hz", out)
    out = re.sub(r"\s+([,.;:!?%\)\]])", r"\1", out)
    out = re.sub(r"([\(\[])\s+", r"\1", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


# Always segment multi-sentence requirements. The fine-tuned NLLB model is
# accurate sentence-by-sentence but may emit an early EOS for long regulatory
# paragraphs even when the nominal decoder limit is not reached.
def split_for_nllb(translator: base.NLLBTranslator, text: str, max_tokens: int = 90) -> list[str]:
    def token_count(value: str) -> int:
        return len(translator._encode(value))

    sentences = [part.strip() for part in re.split(r"(?<=[.!?;:])\s+", text) if part.strip()]
    if len(sentences) <= 1:
        sentences = [part.strip() for part in re.split(r"(?<=,)\s+", text) if part.strip()]
    if not sentences:
        sentences = [text]

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and token_count(candidate) > max_tokens:
            chunks.append(current)
            current = ""
        if token_count(sentence) <= max_tokens:
            current = f"{current} {sentence}".strip() if current else sentence
            continue
        # Split a single exceptionally long sentence at comma boundaries first.
        clauses = [part.strip() for part in re.split(r"(?<=,)\s+", sentence) if part.strip()]
        for clause in clauses:
            candidate = f"{current} {clause}".strip() if current else clause
            if current and token_count(candidate) > max_tokens:
                chunks.append(current)
                current = ""
            if token_count(clause) <= max_tokens:
                current = f"{current} {clause}".strip() if current else clause
                continue
            # Final fallback: word grouping.
            for word in clause.split():
                candidate = f"{current} {word}".strip() if current else word
                if current and token_count(candidate) > max_tokens:
                    chunks.append(current)
                    current = word
                else:
                    current = candidate
    if current:
        chunks.append(current)
    return chunks or [text]


def translate_all(self: base.NLLBTranslator, texts) -> None:
    pending: list[dict] = []
    for source in texts:
        if source in self.cache:
            continue
        exact = base.translate_exact_or_none(source)
        if exact is not None:
            self.cache[source] = final_normalize(exact)
            continue

        toc = base.TOC_RE.match(source)
        if toc:
            label, dots, page_no = toc.groups()
            exact_label = base.translate_exact_or_none(label.strip())
            if exact_label is not None:
                self.cache[source] = f"{final_normalize(exact_label)} {dots}{page_no}"
                continue
            protected, mapping = base.protect_text(label.strip())
            pending.append({
                "source": source,
                "chunks": split_for_nllb(self, protected),
                "mapping": mapping,
                "suffix": f" {dots}{page_no}",
            })
            continue

        protected, mapping = base.protect_text(source)
        pending.append({
            "source": source,
            "chunks": split_for_nllb(self, protected),
            "mapping": mapping,
            "suffix": "",
        })

    flat: list[tuple[int, int, str]] = []
    for item_index, item in enumerate(pending):
        for chunk_index, chunk in enumerate(item["chunks"]):
            flat.append((item_index, chunk_index, chunk))

    translated_chunks: dict[int, dict[int, str]] = {}
    print(
        f"Translation cache={len(self.cache)}; pending units={len(pending)}; chunks={len(flat)}",
        flush=True,
    )
    started = time.time()
    batch_limit = 64
    for offset in range(0, len(flat), batch_limit):
        batch = flat[offset : offset + batch_limit]
        source_tokens = [self._encode(meta[2]) for meta in batch]
        results = self.translator.translate_batch(
            source_tokens,
            target_prefix=[["kor_Hang"] for _ in source_tokens],
            beam_size=4,
            max_decoding_length=384,
            batch_type="tokens",
            max_batch_size=1536,
            return_scores=False,
            replace_unknowns=True,
        )
        for (item_index, chunk_index, _chunk), result in zip(batch, results):
            translated_chunks.setdefault(item_index, {})[chunk_index] = self._decode(result.hypotheses[0])
        if offset % (batch_limit * 5) == 0 or offset + batch_limit >= len(flat):
            done = min(len(flat), offset + batch_limit)
            elapsed = max(1.0, time.time() - started)
            print(f"Translated {done}/{len(flat)} chunks ({done / elapsed:.2f} chunks/s)", flush=True)

    for item_index, item in enumerate(pending):
        translated = " ".join(
            translated_chunks[item_index][chunk_index].strip()
            for chunk_index in range(len(item["chunks"]))
        )
        translated = base.restore_placeholders(translated, item["mapping"])
        translated = final_normalize(translated) + item["suffix"]
        if not base.KOREAN_RE.search(translated) and base.should_translate(item["source"]):
            translated = item["source"]
        self.cache[item["source"]] = translated

    self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")


base.NLLBTranslator.translate_all = translate_all


# Only genuinely bold/all-capital/numeric section headings are headings.
# Center position alone is not sufficient because ordinary continuation lines
# in indented lists are also visually centred within the text column.
def is_heading_line(line: base.LineBox, page_width: float) -> bool:
    text = base.normalize_source(line.text)
    english_words = base.ENGLISH_WORD_RE.findall(text)
    uppercase_heading = bool(english_words) and all(word.isupper() for word in english_words)
    numbered_heading = bool(re.match(r"^\d+(?:\.\d+)+\s+\S", text)) and (line.bold or len(text) < 140)
    return line.bold or uppercase_heading or numbered_heading


revision.is_heading_line = is_heading_line
base.is_heading_line = is_heading_line


if __name__ == "__main__":
    base.main()
