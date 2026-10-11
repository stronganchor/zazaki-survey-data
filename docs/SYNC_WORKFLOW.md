# Website-authoritative synchronization

The [live Atlas](https://zazacaogren.com/atlas/) is the source of truth for current
published transcriptions, IPA, primary/alternate forms, comparison curation and
publication status. This repository is a versioned anonymous export, not a source
for overwriting newer website edits.

## Required on every survey processing session

1. Check repository status, fetch and fast-forward before editing. Preserve existing work.
2. Before preparing website additions, capture a complete private live snapshot with
   response versions and media hashes; verify the dataset stayed stable during capture.
3. Pull website edits into the canonical local transcription/comparison records and
   save a dated preimage. Keep original source text, private notes, separately approved
   as-spoken training targets and frozen listener stimuli distinct.
4. Produce an anonymous allowlisted snapshot and verified lossless WAV master index.
   Review new-speaker publication/license approval. Unknown masters require investigation;
   do not substitute a lossy download or infer audio matches from filenames.
5. Stage, validate, inspect, commit and push the reconciled changes. Re-capture the
   website before pushing and compare its content fingerprint. Rebuild if it changed.
6. Prepare the requested website update against this baseline. Immediately before
   writing, recheck affected versions and media hashes. Use scoped version-checked
   patches; do not blindly reimport an old cohort.
7. After successful live readback, repeat the capture, local reconciliation, validated
   export, commit and push. Verify remote HEAD and validate a clean archive of that commit.

A processed survey requires the final pushed commit or a verified no-change result.
Do not create empty commits. Preserve and report any work whose push fails. This is a
required processing-time feedback loop, **not an instant webhook or background watcher**.

## Portable staging tool

Private capture, identity mapping, consent checks and local reconciliation happen
outside this repository. Never commit the raw administrative capture or master paths.
The private workflow supplies an anonymous snapshot and a private media index:

```text
python -B tools/sync_from_atlas.py --repo . --snapshot <anonymous-snapshot.json> --masters <private-master-index.json> --output <new-staging-directory> --date YYYY-MM-DD
python -B <new-staging-directory>/tools/validate.py
```

The exporter copies its input repository into a fresh staging directory. It preserves
stable IDs and deduplicates identical PCM per speaker. New speakers additionally
require `--approve-new-speaker spkNN`, following consent and anonymization review.
It performs no website, network or Git writes. Complete the commit/push steps above.
Recompute `SHA256SUMS` after any file changes; all text files use UTF-8 and LF.

## Current and historical data

`data/atlas-current.json` contains public codes, current curation, response versions
and published-media hashes. The private capture's fingerprint is recorded without
embedding private IDs, names, initials, contacts, questionnaires, notes or feedback.

Current accepted website data feeds active `responses`, `forms`, `annotations` and
their TSV projections. Full response text stays separate from selected display forms.
Retired concepts and separately approved supplemental utterances remain historical.

For replaced audio, `selected_recording_ids` points to the current clip, while
`superseded_recording_ids` retains the earlier published clip and its annotation.
An older clip can remain selected for a historical concept that shared it. New
boundaries receive new recording IDs and do not inherit acoustic-training approval.
Previously approved as-spoken targets remain attached to their original recordings;
lexical website edits do not automatically revise them. Filter by current selection
and training status before using the data for model training.

The exporter stops on public removals or lifted holds that require a deliberate
archival/consent decision. It never silently restores withheld audio. Publication
updates do not change frozen listener trials or establish acoustic training eligibility.
