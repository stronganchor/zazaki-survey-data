"""Build a staged public release from an anonymized Atlas snapshot and private WAV index.

Never pass a raw administrative export as --snapshot. See docs/SYNC_WORKFLOW.md.
No network calls, Git commands, website writes, or changes to the input repository.
"""
import argparse
import copy
import csv
import hashlib
import json
import re
import shutil
import wave
from collections import Counter
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def rows(root, name):
    return [json.loads(x) for x in (root/'data'/f'{name}.jsonl').read_text('utf-8').splitlines()]


def jsonl(root, name, data):
    (root/'data'/f'{name}.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False, allow_nan=False)+'\n' for x in data), encoding='utf-8', newline='\n')


def checksums(root):
    files = sorted(p for p in root.rglob('*') if p.is_file() and not {'.git','__pycache__'} & set(p.relative_to(root).parts)
                   and p.name != 'SHA256SUMS' and p.suffix not in ('.pyc','.pyo'))
    (root/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(root).as_posix()}\n' for p in files), encoding='utf-8', newline='\n')


def tables(root, recordings, responses, forms, annotations):
    by_recording = {r['id']:r for r in recordings}
    ann_by = {}
    for a in annotations:
        ann_by.setdefault(a['recording_id'],a)
    utterances = []
    for r in recordings:
        a = ann_by[r['id']]
        utterances.append({**r,'target_concepts':';'.join(r['target_concepts']),
            'working_transcription':a['orthography'],'working_research_ipa':a.get('research_ipa'),
            'working_transcription_status':a['transcription_status'],
            'selected_comparison_forms':';'.join(f['orthography'] for f in forms if r['id'] in f['recording_ids']),
            'quality_flags':';'.join(r['quality_flags'])})
    lingpy = [{'ID':i,'CONCEPT':f['concept_id'],'DOCULECT':f['speaker_id'],'IPA':f.get('research_ipa'),
        'FORM':f['orthography'],'AUDIO':';'.join(by_recording[k]['audio_path'] for k in f['recording_ids']),
        'ROLE':f['role'],'CERTAINTY':f['certainty']} for i,f in enumerate(forms,1)]
    for name,data in [('coverage',responses),('forms',forms),('recordings',recordings),('utterances',utterances),('parse-lingpy',lingpy)]:
        path = root/'data'/f'{name}.tsv'
        columns = path.read_text('utf-8').splitlines()[0].split('\t')
        with path.open('w',encoding='utf-8',newline='') as handle:
            writer = csv.DictWriter(handle,fieldnames=columns,delimiter='\t',lineterminator='\n')
            writer.writeheader()
            writer.writerows({k:'' if r.get(k) is None else r.get(k) for k in columns} for r in data)


def validate_snapshot(snapshot):
    assert snapshot['schema_version']==1
    assert set(snapshot)=={'schema_version','source','source_content_sha256','concepts','speakers','responses'}
    assert re.fullmatch('[0-9a-f]{64}',snapshot['source_content_sha256'])
    assert snapshot['source']=='https://zazacaogren.com/atlas/'
    ids = [s['id'] for s in snapshot['speakers']]
    assert len(ids)==len(set(ids)) and all(re.fullmatch(r'spk\d{2,}',s) for s in ids)
    allowed_speaker={'id','label','language','language_iso639_3','sex','location','location_precision','location_note','release_license'}
    for s in snapshot['speakers']:
        assert set(s)<=allowed_speaker and s['release_license']=='CC0-1.0'
        assert set(s['location'])<= {'village_tr','village_zz','district_tr','district_zz','province_tr','province_zz'}
    for c in snapshot['concepts']:
        assert set(c)=={'id','label_en','label_tr','category','source_concept'}
    allowed={'id','speaker_id','concept_id','version','orthography','ipa','eligibility','user_reviewed','visible',
             'display_forms','forms','alternate_forms','segment_distance_eligible','lexical_family_comparison_allowed','published_audio_sha256'}
    keys=[]
    for r in snapshot['responses']:
        assert set(r)==allowed and r['speaker_id'] in ids
        assert r['id']==r['speaker_id']+':'+r['concept_id']
        keys.append(r['id'])
        assert r['published_audio_sha256'] is None or re.fullmatch('[0-9a-f]{64}',r['published_audio_sha256'])
        for f in r['display_forms']:
            assert set(f)<= {'role','orthography','ipa','audio_scope','certainty'}
        for f in r['forms']+r['alternate_forms']:
            assert set(f)<= {'form','full_form','lexeme_id','accepted','certainty'}
    assert len(keys)==len(set(keys))


def build(repo, snapshot, masters, output, release_date, approve_new=()):
    validate_snapshot(snapshot)
    assert not output.exists(), 'Choose a fresh staging directory.'
    shutil.copytree(repo,output,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc','*.pyo'))
    names=('speakers','concepts','sessions','recordings','responses','forms','annotations')
    data={n:rows(output,n) for n in names}
    speakers,concepts,sessions,recordings,responses,forms,annotations=(data[n] for n in names)
    existing={s['id'] for s in speakers}
    incoming={s['id'] for s in snapshot['speakers']}
    assert existing<=incoming, 'A speaker disappeared: inspect consent/removal before exporting.'
    assert incoming-existing <= set(approve_new), 'New speakers need explicit release/consent approval.'
    speakers[:]=snapshot['speakers']
    by_concept={c['id']:c for c in concepts}
    active={c['id'] for c in snapshot['concepts']}
    for c in concepts:c['current_survey']=c['id'] in active
    for c in snapshot['concepts']:
        if c['id'] not in by_concept:
            new={**c,'current_survey':True,'derived_comparison_unit':False,'parse_list_label':None}
            concepts.append(new);by_concept[c['id']]=new
        else:by_concept[c['id']].update(c)
    by_response={r['id']:r for r in responses}
    for sid in incoming:
        for c in concepts:
            key=sid+':'+c['id']
            if key not in by_response:
                new={'id':key,'speaker_id':sid,'concept_id':c['id'],'current_survey':c['current_survey'],
                    'response_status':'not_elicited','selected_recording_ids':[],'supplemental_recording_ids':[],
                    'transcription_orthography':'','transcription_research_ipa':None,'comparison_eligibility':'missing',
                    'user_reviewed':False,'recording_available':False}
                responses.append(new);by_response[key]=new
    for r in responses:r['current_survey']=r['concept_id'] in active
    by_recording={r['id']:r for r in recordings}
    pcm_index={(r['speaker_id'],r['pcm_sha256']):r for r in recordings}
    counters=Counter({sid:max([int(r['id'].rsplit('-r',1)[1]) for r in recordings if r['speaker_id']==sid] or [0]) for sid in incoming})
    changed=[];new_audio=[]
    for live in snapshot['responses']:
        if live['concept_id'] not in active:continue  # retain explicitly released historical research rows
        r=by_response[live['id']]
        before=copy.deepcopy(r)
        if r['response_status']=='withheld':
            assert not live['visible'] and not live['published_audio_sha256'], 'Explicit hold needs adjudicated release.'
            continue
        selected=[]
        if live['visible'] and live['published_audio_sha256']:
            master=masters[live['published_audio_sha256']]
            path=Path(master['path'])
            assert sha(path)==master['sha256'], f'Master changed: {live["id"]}'
            with wave.open(str(path),'rb') as w:
                assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype())==(1,2,16000,'NONE')
                pcm=w.readframes(w.getnframes())
            pcmsha=hashlib.sha256(pcm).hexdigest()
            rec=pcm_index.get((r['speaker_id'],pcmsha))
            if rec is None:
                sid=r['speaker_id']; counters[sid]+=1;rid=f'{sid}-r{counters[sid]:03}'
                dest=output/'audio'/sid/(rid+'.wav');dest.parent.mkdir(parents=True,exist_ok=True)
                with wave.open(str(dest),'wb') as w:
                    w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(pcm)
                session_id=sid+'-atlas'
                if not any(s['id']==session_id for s in sessions):
                    sessions.append({'id':session_id,'speaker_id':sid,'roster_id':None,'session_kind':'reviewed_atlas_clip_updates',
                                     'source_capture_format':'see_original_session','source_audio_in_repository':False})
                rec={'id':rid,'speaker_id':sid,'session_id':session_id,'roster_id':None,
                     'source_item_ids':master.get('source_item_ids',[]),'target_concepts':[r['concept_id']],
                     'audio_path':dest.relative_to(output).as_posix(),'audio_sha256':sha(dest),'pcm_sha256':pcmsha,
                     'duration_seconds':len(pcm)/32000,'sample_rate':16000,'channels':1,'sample_width_bytes':2,
                     'recording_kind':'selected_response','quality_flags':['updated_clip_requires_separate_training_alignment'],
                     'lossless_relative_to_reviewed_pcm':True,'original_capture_may_be_lossy':True,'license':'CC0-1.0',
                     'source_interval_seconds':master.get('source_interval_seconds'),'source_interval_basis':'reviewed_boundary_metadata',
                     'transcription_completeness':'not_verified','acoustic_training_eligible':False,
                     'acoustic_training_status':'publication_release_not_a_training_manifest',
                     'annotation_warnings':['A website publication update is not acoustic-training approval.']}
                recordings.append(rec);by_recording[rid]=rec;pcm_index[(sid,pcmsha)]=rec;new_audio.append(rid)
            rec['target_concepts']=sorted(set(rec['target_concepts'])|{r['concept_id']})
            selected=[rec['id']]
        old=r['selected_recording_ids']
        if old!=selected:
            if not live['visible'] and old:
                raise ValueError(f'{r["id"]}: public removal requires deliberate audio/consent disposition; do not archive automatically.')
            for rid in old:
                if rid not in selected:
                    r.setdefault('superseded_recording_ids',[])
                    if rid not in r['superseded_recording_ids']:r['superseded_recording_ids'].append(rid)
                    old_ann=next((a for a in annotations if a['id']==r['id']),None)
                    if old_ann and old_ann['recording_id']==rid:
                        old_ann['id']=r['id']+':superseded:'+rid
                        old_ann['transcription_status']='historical_publication_transcription'
        r.update(selected_recording_ids=selected,transcription_orthography=live['orthography'],
                 transcription_research_ipa=live['ipa'],comparison_eligibility=live['eligibility'],
                 user_reviewed=live['user_reviewed'],atlas_version=live['version'],
                 published_audio_sha256=live['published_audio_sha256'])
        if live['visible']:r['response_status']='available'
        elif r['response_status']=='available':r['response_status']='unresolved_or_different_meaning'
        r['recording_available']=bool(selected+r['supplemental_recording_ids']+r.get('superseded_recording_ids',[]))
        forms[:]=[f for f in forms if (f['speaker_id'],f['concept_id'])!=(r['speaker_id'],r['concept_id'])]
        for i,f in enumerate(live['display_forms'],1):
            forms.append({'id':r['id']+f':{i}','speaker_id':r['speaker_id'],'concept_id':r['concept_id'],
                'orthography':f['orthography'],'research_ipa':f.get('ipa'),'role':f['role'],'certainty':f['certainty'],
                'audio_scope':f['audio_scope'],'recording_ids':selected if f['audio_scope']=='response' else [],
                'token_timestamps_verified':False,'current_survey':True})
        annotations[:]=[a for a in annotations if a['id']!=r['id']]
        if selected:
            annotations.append({'id':r['id'],'recording_id':selected[0],'target_concept':r['concept_id'],
                'orthography':live['orthography'],'research_ipa':live['ipa'],
                'transcription_status':'owner_reviewed_working_transcription' if live['user_reviewed'] else 'provisional',
                'annotation_scope':'released_response_clip','token_timestamps_verified':False})
        if before!=r:changed.append(r['id'])
    for f in forms:f['current_survey']=f['concept_id'] in active
    for r in recordings:
        selected_now=any(r['id'] in x['selected_recording_ids'] for x in responses)
        if not selected_now and any(r['id'] in x.get('superseded_recording_ids',[]) for x in responses):
            r['recording_kind']='superseded_publication_clip'
    for name in names:
        data[name].sort(key=lambda x:x['id'])
        jsonl(output,name,data[name])
    tables(output,recordings,responses,sorted(forms,key=lambda x:x['id']),annotations)
    write(output/'data/atlas-current.json',snapshot)
    summary=load(output/'release.json')
    summary.update(release_date=release_date,speakers=len(speakers),current_survey_concepts=len(active),
        historical_concept_registry=len(concepts),unique_recording_clips=len(recordings),
        audio_duration_seconds=round(sum(r['duration_seconds'] for r in recordings),8),
        audio_bytes=sum((output/r['audio_path']).stat().st_size for r in recordings),curated_form_rows=len(forms),
        annotation_rows=len(annotations),speaker_concept_slots=len(responses),
        counts_by_speaker=dict(sorted(Counter(r['speaker_id'] for r in recordings).items())),
        current_visible_transcription_counts=[sum(r['speaker_id']==s['id'] and r['visible'] and r['concept_id'] in active for r in snapshot['responses']) for s in speakers],
        explicit_withheld_slots=sum(r['response_status']=='withheld' for r in responses),
        superseded_publication_clips=sum(r['recording_kind']=='superseded_publication_clip' for r in recordings),
        current_selected_unique_clips=len({rid for r in responses if r['current_survey'] for rid in r['selected_recording_ids']}),
        website_source_content_sha256=snapshot['source_content_sha256'])
    write(output/'release.json',summary)
    checksums(output)
    return {'updated_response_rows':len(changed),'new_audio_clips':new_audio,'changed_ids':changed}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--masters',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--date',required=True);p.add_argument('--approve-new-speaker',action='append',default=[])
    a=p.parse_args()
    print(json.dumps(build(a.repo,load(a.snapshot),load(a.masters),a.output,a.date,a.approve_new_speaker),ensure_ascii=False))


if __name__=='__main__':main()
