# Data dictionary

All text files use UTF-8. TSV files have a header; JSONL files contain one JSON object per line. Empty TSV cells correspond to absent/null values. JSONL retains arrays and booleans that TSV cannot represent cleanly. The JSONL tables are authoritative when a TSV offers fewer fields.

## Keys and joins

`speaker_id` joins `speakers.id`. `concept_id` (or `target_concept`) joins `concepts.id`. `recording_id` and recording-ID arrays join `recordings.id`. `session_id` joins `sessions.id`. `roster_id` joins the objects in `rosters.json`. All audio paths are relative to the repository root. IDs are release-local identifiers rather than personal identifiers.

`responses.id` is `speaker:concept`. `forms.id` adds an index within that speaker/concept. `annotations.id` identifies an annotation, not a separate audio file. A clip can support multiple concept rows; do not count references as distinct recordings.

## Speakers, concepts, and sessions

| Table | Fields |
| --- | --- |
| `speakers.jsonl` | Coded `id`/`label`, `language`, ISO 639-3 macrolanguage code `zza`, optional `sex`, public `location`, `location_precision`, `location_note`, and license |
| `concepts.jsonl` | Stable `id`, `label_en`, `label_tr`, `category`, source prompt `source_concept`, `current_survey`, `derived_comparison_unit`, nullable `parse_list_label` |
| `sessions.jsonl` | Speaker, original roster, session kind, original capture format, and whether the full capture is included (false) |
| `rosters.json` | Ordered concept IDs for each survey version, plus Speaker 01's preserved review mapping; one-based position corresponds to its `qNN` prompt number |

`source_concept` can differ from `id` for a derived comparison unit. A `parse_list_label` is a lexical-list match, not evidence of cognacy or a confirmed speaker answer.

## Recordings

| Field | Meaning |
| --- | --- |
| `audio_path` | Repository-relative WAV path |
| `audio_sha256`, `pcm_sha256` | Hash of the whole file and its raw PCM frames respectively |
| `duration_seconds`, `sample_rate`, `channels`, `sample_width_bytes` | Audio properties; sample width is 2 bytes |
| `source_item_ids` | Anonymous prompt IDs scoped to the recorded session/roster; supplemental IDs can include suffixes |
| `target_concepts` | Intended elicitation targets linked to this clip |
| `recording_kind` | Selected response or supplemental/mismatched response |
| `quality_flags` | Conditions requiring caution, including historically recovered boundaries and partial transcription |
| `source_interval_seconds` | Archived interval in the privately retained full session, where recoverable; not word alignment |
| `lossless_relative_to_reviewed_pcm` | Export preserves the reviewed master's PCM exactly |
| `original_capture_may_be_lossy` | True because original capture formats were compressed |
| `as_spoken_orthography`, `as_spoken_status` | Separately approved spoken layer where available; historical approvals may have boundary caveats |
| `as_spoken_research_ipa`, `as_spoken_ipa_status` | Spoken IPA layer and its separate review status |
| `normalized_orthography` | Optional distinct normalized layer; null does not instruct a transformation |
| `source_working_orthography`, `source_working_research_ipa`, `source_working_status` | Historical/source witness where no separate as-spoken approval exists; can differ from current curated spelling |
| `audio_origin` | Explicit provenance for the three archival MP3-derived caches |
| `annotation_warnings` | Human-readable cautions about a partial transcript or unresolved boundary |
| `as_spoken_interval_seconds` | Original annotation interval within the master, if supplied; not verified token timing or a new cut |
| `actual_concept`, `actual_gloss_en`, `target_match_status` | Supplemental responses' actual referent/meaning and match status; null can mean unresolved |
| `transcription_completeness`, `acoustic_training_eligible` | Optional explicit restriction; absence is not an approval for training |

Source intervals do not expose the original session recordings. A boundary caveat remains relevant even if a saved interval can be reproduced exactly.

## Responses, forms, and annotations

`responses.jsonl` is the complete seven-speaker × 57-concept grid. `current_survey` distinguishes the current 50 from seven historical units. `response_status` means:

- `available`: a selected comparison form is present, even if it lacks an approved audio link.
- `not_elicited`: no retained source response is recorded for that target.
- `unresolved_or_different_meaning`: source material exists but no accepted target form is selected.
- `withheld`: an explicit publication hold; text and all audio links are empty.

`selected_recording_ids` link the primary publication response. `supplemental_recording_ids` preserve approved extra utterances. `recording_available` means either array contains a clip; it does not assert a confirmed target match. `transcription_orthography` and `transcription_research_ipa` retain the working response transcription. `comparison_eligibility` reproduces lexical comparison classification, not STT eligibility. `user_reviewed` is historical review status, not a claim of fresh verification of every phoneme.

`forms.jsonl` preserves every released selected form with its `role`, `certainty`, `audio_scope`, and links. The form need not transcribe the whole recording. Alternatives can lack their own audio. `token_timestamps_verified` is false throughout.

`annotations.jsonl` retains working clip transcriptions, intended target, optional actual concept, and review/status fields. Supplemental IPA may be a source transcription that was not independently approved. No IPA transformation or spelling normalization is implied by this table.

## Checksums

`SHA256SUMS` lists all release files except itself. `release.json` supplies exact snapshot counts. To verify the downloaded package, run `python tools/validate.py` from any working directory. The script resolves its own repository root.
