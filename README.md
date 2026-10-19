# Zazaki survey recordings and transcriptions

Public-domain audio and working transcriptions from a picture-based Zazaki lexical survey. The current release contains **431 clips from nine speakers**, including superseded/historical evidence, totaling approximately **8 minutes**, with orthographic transcriptions, research IPA, selected comparison forms, and speaker location metadata.

Current published transcriptions follow the live Atlas, synchronized on 2026-10-17. This is a versioned snapshot, with earlier evidence explicitly preserved. It combines responses to the earlier 40-item survey, the expanded 50-item survey, and selected supplementary elicitation. It preserves additional responses and lexical variants rather than forcing one recording per concept. It is incomplete: a missing response does not establish that a speaker lacks a word.

## Start here

| File | Purpose |
| --- | --- |
| [data/utterances.tsv](data/utterances.tsv) | One row per physical clip, with working and as-spoken text, selected forms, meanings, and quality flags |
| [data/coverage.tsv](data/coverage.tsv) | One row per speaker/concept, including missing, unresolved, and withheld entries |
| [data/forms.tsv](data/forms.tsv) | Selected lexical comparison forms and IPA; may be shorter than the spoken utterance |
| [data/recordings.tsv](data/recordings.tsv) | Audio paths, checksums, and independently approved as-spoken layers where available |
| [data/parse-lingpy.tsv](data/parse-lingpy.tsv) | Portable concept/doculect/IPA table for comparative work |
| [data/annotations.jsonl](data/annotations.jsonl) | Working utterance transcriptions and annotation status |
| [data/recordings.jsonl](data/recordings.jsonl) | Complete clip metadata, quality flags, source intervals, and links |
| [data/responses.jsonl](data/responses.jsonl) | Selected and supplemental recording links for each concept |
| [data/speakers.jsonl](data/speakers.jsonl) | Speaker codes and public regional metadata |
| [data/concepts.jsonl](data/concepts.jsonl) | English/Turkish labels, historical/current status, and PARSE-list overlap |
| [data/atlas-current.json](data/atlas-current.json) | Current anonymous website curation and version/hash provenance |
| [data/rosters.json](data/rosters.json) | The three survey versions with their original item orders |
| [docs/etymology/README.md](docs/etymology/README.md) | Etymology workbook, sortable research tables, sources, alternatives and qualitative confidence |

Audio lives in `audio/spk01/` through `audio/spk07/`, `audio/spk09/`, and `audio/spk10/`. All clips are **16 kHz mono PCM16 WAV**. The export preserves the selected PCM exactly, without another codec conversion or loudness adjustment. Original survey captures were compressed WebM/Opus; the supplementary session used AAC/M4A. Three Speaker 04 archival isolation backfills (cloud, stone, snow) preserve pre-existing PCM caches decoded from original MP3 files. WAV does not make those original captures lossless.

Download with GitHub's **Code → Download ZIP**, or clone:

```sh
git clone https://github.com/stronganchor/zazaki-survey-data.git
cd zazaki-survey-data
python tools/validate.py
```

The validator needs only Python's standard library. It checks the published checksums, audio format and PCM hashes, table links, coverage, and excluded entries. [SHA256SUMS](SHA256SUMS) covers every release file except itself.

## Interpret the layers correctly

`annotations.jsonl` contains the released working transcription of a response clip. `forms.jsonl` contains selected comparison words, including alternatives. These can differ: a speaker may have produced a phrase or a verb with a subject, while the comparison form contains only the selected word. Nouns and adjectives were elicited through pictures; actions were also picture prompts, without a uniform requirement for an infinitive, tense, person, or subject gender. Preserve the actual response form when doing morphological comparisons.

An explicitly approved **as-spoken orthography** is stored separately on its recording. It can retain subjects, particles, spacing, or vowel spellings omitted or normalized in the display layer. A working transcription is not automatically a complete as-spoken annotation. Orthography and IPA are independently editable research layers; the release preserves reviewed values and remaining inconsistencies. In this orthography, dotless `ı` represents [ɪ] or [ɨ], not [i].

`audio_scope=response` links a comparison form to the containing response clip, not to verified word-level timing. `audio_scope=none` means there is no approved audio link for that particular selected alternative. No token timestamps, cognate assignments, phonetic tokenization, or borrowing classifications have been invented.

The eight supplementary/historical recordings include repeated or alternative answers, responses to a different referent, and one unresolved referent. Their intended prompt and actual meaning are separate fields. These recordings are linguistic observations, not additional confirmed target matches.

## Versions, gaps, and quality

The current survey has **50 concepts**. The release registry retains **57 concepts/comparison units**, including retired items and the derived `bread-from-eating` and `to-listen` units. Derived units can reference the same clip as another concept. One physical clip is stored once per speaker, with multiple references where appropriate.

Speakers 01–06 originally answered the 40-item roster. Speaker 01 has a separately preserved review mapping: q11 is sun and q13 is cloud, opposite the shared legacy roster. Speaker 07 answered the 2026-10-08 50-item roster. The 2026-10-10 roster reordered the 50 prompts. Interpret `qNN` using its session's roster, never the latest order. Speaker 06 also completed the reordered 50-item roster in a follow-up session on 2026-10-11. Other supplementary sessions have no fixed picture-survey roster.

Publication holds are retained as empty coverage slots, currently Speaker 07's green and Speaker 09's head, green, and neck. The latter three are older archived supplements with website-only permission; no associated audio or transcription is included here. Speaker 06's ear and mountain now use newly reviewed singular follow-up recordings; the earlier held recordings remain unreleased. Speaker 03's mouth clip contains only the approved `fek` reading; the held lip reading is excluded. Skips, unresolved meanings, and unelicited newer prompts remain visible in coverage.

Speaker 01's historically recovered clips retain saved intervals whose final fine trims are not guaranteed. Speaker 03's mountain has an unresolved acoustic-boundary concern; the release includes its whole 0.730-second publication master, not the held 49-millisecond training interval. Speaker 07's sun includes following context that is not fully transcribed. Consult the per-recording `quality_flags` and transcription-completeness fields before acoustic analysis. This publication release is **not an approved STT training manifest**, and no new listening review is claimed.

Training-status fields describe editorial and alignment review, not additional license restrictions; the released material remains CC0.

See [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) for field definitions and joins, and [release.json](release.json) for exact counts.

## PARSE and comparative use

The export is informed by [Lucas Ardelean's PARSE project](https://github.com/ArdeleanLucas/PARSE): stable concept IDs, speaker codes as doculect IDs, IPA, audio references, and explicit alternatives. `parse-lingpy.tsv` includes `ID`, `CONCEPT`, `DOCULECT`, `IPA`, `COGID`, `TOKENS`, and `BORROWING`, with extra form/audio/status columns. The last three annotation columns are intentionally empty. This is a portable table; native PARSE workspace import compatibility has not been tested.

The concept registry marks exact label overlap with the supplied PARSE word list. Following the collector's clarification, `fly-insect` maps to `fly`; `to-fly` remains a separate action. The picture-survey verbs are not prompts from that supplied list.

## Public-domain dedication

The audio and original transcription/metadata contributions in this repository are dedicated to the public domain under **CC0-1.0**. The collector confirmed permission from the speakers to publish their audio in the public domain. Read [LICENSE](LICENSE), the complete [Creative Commons CC0 legal text](https://creativecommons.org/publicdomain/zero/1.0/).

Public speaker codes replace names and contact information. Raw questionnaires, full session recordings, private review notes, and prompt images are excluded. Regional descriptors reproduce the public research metadata and may be approximate.

Attribution is appreciated although CC0 does not require it. Suggested acknowledgement: *Zazaki survey recordings and transcriptions, stronganchor, release 2026-10-10*, with this repository's URL and the commit used. Future corrections can be tracked through Git history.

## Website synchronization

Current transcriptions follow the live Atlas. Every survey processing session must pull website edits into the local records and push the verified anonymous export. See [the required synchronization workflow](docs/SYNC_WORKFLOW.md). The 2026-10-11 synchronization includes current spelling/IPA corrections and seven repaired recording boundaries. Prior clips remain explicitly linked as superseded; original training annotations are preserved. Counts in `release.json` include historical clips and must not be interpreted as current training volume.

The Speaker 06 follow-up adds 38 selected recordings: 20 replace previous primary clips and 18 fill coverage gaps, bringing this speaker to 44 current words. Six older clips remain selected where preferable or where the new response names a different referent. Accepted earlier variants and superseded recordings remain linked. New clips require separate acoustic-training alignment; narrow research IPA is preserved without granting training eligibility.

Speaker 09 adds 46 owner-reviewed recordings from the 2026-10-10 reordered 50-item roster. Walking is excluded pending a matching masculine present form. The public regional label is Palu, Elazığ; the speaker also lived in central Genç during childhood. No village name or private relationship information is released. This addition does not change the previous speakers' recordings or transcriptions.

The 2026-10-13 update adds 12 reviewed follow-up recordings for Speaker 04, bringing current coverage to 47/50. The prior cloud recording remains selected; fish, head and writing still lack accepted recordings. Publication approval does not make these acoustic training targets automatically eligible.

The 2026-10-14 Atlas checkpoint synchronizes five reviewed transcription/display-form corrections for leaf and bone. Audio and recording IDs are unchanged. Speaker 08 and the three restricted Speaker 09 supplements remain excluded.

Speaker 10 adds 37 owner-reviewed recordings from the 2026-10-10 reordered 50-item roster. All carry a lower-quality recording flag. Thirteen current responses remain withheld with no released audio, transcription, or forms. Reviewed source intervals are retained; publication does not grant acoustic-training eligibility. Names, contact details, questionnaires, and full recordings remain private.

The 2026-10-17 Atlas synchronization preserves two reviewed spelling/form and research-IPA corrections for Speaker 02 lying down and Speaker 07 fish. Audio bytes, recording IDs, coverage status, publication holds, and training annotations are unchanged.
