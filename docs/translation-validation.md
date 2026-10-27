# Translation traceability validation

After a human or translation provider translates a script, check that the tracked claim markers and source URLs remain intact:

```sh
python scripts/validate_translation.py \
  --source artifacts/drafts/script-en.md \
  --translated artifacts/drafts/script-ur.md \
  --language ur
```

The validator checks that claim markers appear in the same order and that source URLs are preserved exactly and in order. It does not translate the script and cannot judge fluency, cultural context, factual accuracy, terminology, or whether the translated sentence still faithfully expresses the source claim.

Do not translate the text inside `[[claim:...]]` markers: those markers bind the translated narration to the original research ledger. A reviewer must assess the translated words around the marker and verify that the claim meaning has not changed.

A passing structural check is only one part of multilingual quality assurance; native-language editorial review is still required.
