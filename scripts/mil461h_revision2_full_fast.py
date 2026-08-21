from __future__ import annotations

# Importing the full terminology wrapper applies its reviewed terminology and
# mandatory-language post-editing to the shared revision engine.
import mil461h_revision2_full as reviewed

rev = reviewed.rev

_original_translate_all = rev.NLLBTranslator.translate_all


def fast_translate_all(self, texts, batch_size: int = 32):
    return _original_translate_all(self, texts, batch_size=32)


def fast_translate_batch(self, texts: list[str]) -> list[str]:
    token_batches = []
    maps = []
    for text in texts:
        protected, mapping = rev.protect(text)
        ids = self.tokenizer(protected, add_special_tokens=True)["input_ids"]
        token_batches.append(self.tokenizer.convert_ids_to_tokens(ids))
        maps.append(mapping)
    results = self.translator.translate_batch(
        token_batches,
        target_prefix=[[self.target_token] for _ in token_batches],
        beam_size=1,
        max_decoding_length=640,
        repetition_penalty=1.05,
    )
    outputs = []
    for source, result, mapping in zip(texts, results, maps):
        tokens = result.hypotheses[0]
        ids = self.tokenizer.convert_tokens_to_ids(tokens)
        text = self.tokenizer.decode(ids, skip_special_tokens=True)
        outputs.append(rev.post_edit(source, rev.restore(text, mapping)))
    return outputs


rev.NLLBTranslator.translate_all = fast_translate_all
rev.NLLBTranslator._translate_batch = fast_translate_batch

if __name__ == "__main__":
    rev.main()
