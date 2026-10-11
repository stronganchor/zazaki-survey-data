"""Validate release integrity without third-party dependencies or network access."""
import hashlib
import csv
import json
import re
import struct
import wave
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rows(name):
    result = [json.loads(line) for line in (ROOT / 'data' / (name + '.jsonl')).read_text(encoding='utf8').splitlines()]
    assert len({r['id'] for r in result}) == len(result), f'duplicate {name} IDs'
    return result


def main():
    manifest = {}
    for line in (ROOT / 'SHA256SUMS').read_text(encoding='utf8').splitlines():
        expected, relative = line.split('  ', 1)
        assert relative not in manifest
        path = ROOT / relative
        assert path.resolve().is_relative_to(ROOT)
        assert path.is_file() and digest(path.read_bytes()) == expected, f'checksum: {relative}'
        manifest[relative] = expected
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
              and '.git' not in p.relative_to(ROOT).parts and '__pycache__' not in p.relative_to(ROOT).parts
              and p.name != 'SHA256SUMS' and p.suffix not in ['.pyc', '.pyo']}
    assert actual == set(manifest), 'unmanifested or missing files'
    for path in (ROOT / 'data').glob('*.tsv'):
        with path.open(encoding='utf8', newline='') as f:
            table = list(csv.reader(f, delimiter='\t'))
        assert table and all(len(r) == len(table[0]) for r in table), f'TSV columns: {path.name}'
    speakers, concepts, sessions = rows('speakers'), rows('concepts'), rows('sessions')
    recordings, responses, forms, annotations = rows('recordings'), rows('responses'), rows('forms'), rows('annotations')
    speaker_ids = {r['id'] for r in speakers}
    concept_ids = {r['id'] for r in concepts}
    session_by = {r['id']: r for r in sessions}
    recording_by = {r['id']: r for r in recordings}
    rosters = {r['id']: r['concept_ids'] for r in json.loads((ROOT / 'data/rosters.json').read_text(encoding='utf8'))}
    assert all(len(c) == len(set(c)) and set(c) <= concept_ids for c in rosters.values())
    summary = json.loads((ROOT / 'release.json').read_text(encoding='utf8'))
    assert len(speakers) == summary['speakers'] and len(concepts) == summary['historical_concept_registry']
    assert sum(c['current_survey'] for c in concepts) == summary['current_survey_concepts']
    assert {(r['speaker_id'], r['concept_id']) for r in responses} == {(s, c) for s in speaker_ids for c in concept_ids}
    audio_paths = set()
    for r in recordings:
        assert r['speaker_id'] in speaker_ids and set(r['target_concepts']) <= concept_ids
        assert session_by[r['session_id']]['speaker_id'] == r['speaker_id']
        assert r['roster_id'] == session_by[r['session_id']]['roster_id']
        assert all(re.fullmatch(r'(q\d{2}[^/\\]*|additional-[a-z-]+|recall-[a-z0-9-]+|extra-q\d{2}-[a-z]+|archive-[a-z0-9-]+)', x) for x in r['source_item_ids'])
        assert re.fullmatch(r'audio/spk\d{2,}/spk\d{2,}-r\d{3,}\.wav', r['audio_path'])
        path = ROOT / r['audio_path']
        assert r['audio_path'] not in audio_paths and digest(path.read_bytes()) == r['audio_sha256']
        audio_paths.add(r['audio_path'])
        with wave.open(str(path), 'rb') as w:
            assert (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getcomptype()) == (1, 2, 16000, 'NONE')
            pcm = w.readframes(w.getnframes())
            assert abs(w.getnframes() / 16000 - r['duration_seconds']) < 1e-8
        assert digest(pcm) == r['pcm_sha256']
        content = path.read_bytes()
        offset, chunks = 12, []
        while offset + 8 <= len(content):
            chunks.append(content[offset:offset + 4])
            size = struct.unpack_from('<I', content, offset + 4)[0]
            offset += 8 + size + size % 2
        assert chunks == [b'fmt ', b'data'], f'non-audio WAV metadata: {path.name}'
    assert audio_paths == {p.relative_to(ROOT).as_posix() for p in (ROOT / 'audio').rglob('*.wav')}
    referenced = set()
    for r in responses:
        links = r['selected_recording_ids'] + r['supplemental_recording_ids'] + r.get('superseded_recording_ids', [])
        assert r['recording_available'] == bool(links)
        for key in links:
            assert recording_by[key]['speaker_id'] == r['speaker_id']
            assert r['concept_id'] in recording_by[key]['target_concepts']
            referenced.add(key)
        if r['response_status'] == 'withheld':
            assert not links and not r['transcription_orthography'] and not r['transcription_research_ipa']
            assert not any(f['speaker_id'] == r['speaker_id'] and f['concept_id'] == r['concept_id'] for f in forms)
    assert referenced == set(recording_by), 'unreferenced recording'
    for f in forms:
        assert f['speaker_id'] in speaker_ids and f['concept_id'] in concept_ids
        assert not f['token_timestamps_verified']
        if f['audio_scope'] != 'response':
            assert not f['recording_ids']
        for key in f['recording_ids']:
            assert recording_by[key]['speaker_id'] == f['speaker_id']
            assert f['concept_id'] in recording_by[key]['target_concepts']
    for a in annotations:
        assert a['recording_id'] in recording_by and a['target_concept'] in concept_ids
        assert not a['token_timestamps_verified']
    response_by = {r['id']: r for r in responses}
    assert sum(r['response_status'] == 'withheld' for r in responses) == summary['explicit_withheld_slots']
    snapshot_path = ROOT / 'data/atlas-current.json'
    if snapshot_path.exists():
        from sync_from_atlas import validate_snapshot
        snapshot = json.loads(snapshot_path.read_text(encoding='utf8'))
        validate_snapshot(snapshot)
        active = {c['id'] for c in snapshot['concepts']}
        assert snapshot['source_content_sha256'] == summary['website_source_content_sha256']
        for live in snapshot['responses']:
            if live['concept_id'] not in active: continue
            r = response_by[live['id']]
            if r['response_status'] == 'withheld':
                assert not live['visible'] and not live['published_audio_sha256']
                continue
            assert r['transcription_orthography'] == live['orthography']
            assert r['transcription_research_ipa'] == live['ipa']
            assert r['published_audio_sha256'] == live['published_audio_sha256']
            displayed = [f for f in forms if f['speaker_id'] == r['speaker_id'] and f['concept_id'] == r['concept_id']]
            expected = [{k:f.get(k) for k in ('role','orthography','ipa','audio_scope','certainty')} for f in live['display_forms']]
            actual = [{'role':f['role'],'orthography':f['orthography'],'ipa':f['research_ipa'],'audio_scope':f['audio_scope'],'certainty':f['certainty']} for f in displayed]
            assert actual == expected, live['id']
            if live['visible'] and live['published_audio_sha256']: assert r['selected_recording_ids']
    assert summary['unique_recording_clips'] == len(recordings)
    assert summary['curated_form_rows'] == len(forms) and summary['annotation_rows'] == len(annotations)
    assert summary['counts_by_speaker'] == dict(Counter(r['speaker_id'] for r in recordings))
    assert abs(summary['audio_duration_seconds'] - sum(r['duration_seconds'] for r in recordings)) < 1e-5
    # Catch accidentally exported local paths, source-account identifiers, contacts, and questionnaire keys.
    for relative in manifest:
        if relative.endswith('.wav') or relative.startswith('tools/'):
            continue
        text = (ROOT / relative).read_text(encoding='utf8')
        assert not re.search(r'\b[A-Z]:[\\/]|/(?:Users|home)/|AppData|LOCALAPPDATA|private_wav_path|source_review_path|GITHUB_TOKEN|phone_number|email_address|questionnaire_answers', text, re.I), relative
        if relative.startswith('data/'):
            assert not re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', text, re.I), relative
            assert not re.search(r'\b[0-9a-f]{32}\b|\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', text, re.I), relative
    print(f'PASS: {len(speakers)} speakers, {len(recordings)} WAV clips, {len(responses)} coverage rows, {len(forms)} comparison forms; checksums and links verified.')


if __name__ == '__main__':
    main()
