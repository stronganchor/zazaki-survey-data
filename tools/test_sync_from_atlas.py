"""Regression tests against the released corpus; no network or site writes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from sync_from_atlas import build, load, rows, sha

ROOT=Path(__file__).resolve().parents[1]


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='atlas-sync-test-')
        self.addCleanup(self.temp.cleanup)
        self.output=Path(self.temp.name)/'release'
        self.snapshot=load(ROOT/'data/atlas-current.json')
        self.responses={r['id']:r for r in rows(ROOT,'responses')}
        self.recordings={r['id']:r for r in rows(ROOT,'recordings')}
        self.masters={}
        active={c['id'] for c in self.snapshot['concepts']}
        for r in self.snapshot['responses']:
            if r['concept_id'] in active and r['visible'] and r['published_audio_sha256']:
                rec=self.recordings[self.responses[r['id']]['selected_recording_ids'][0]]
                path=ROOT/rec['audio_path']
                self.masters[r['published_audio_sha256']]={'path':str(path),'sha256':sha(path)}

    def run_build(self):
        return build(ROOT,self.snapshot,self.masters,self.output,load(ROOT/'release.json')['release_date'])

    def test_repeat_is_byte_identical(self):
        result=self.run_build()
        self.assertEqual(result['new_audio_clips'],[])
        self.assertEqual(result['updated_response_rows'],0)
        for path in (ROOT/'data').iterdir():
            self.assertEqual(path.read_bytes(),(self.output/'data'/path.name).read_bytes(),path.name)
        self.assertEqual((ROOT/'release.json').read_bytes(),(self.output/'release.json').read_bytes())

    def test_website_change_updates_views_but_not_training(self):
        live=next(r for r in self.snapshot['responses'] if r['id']=='spk01:ear')
        live['orthography']='updated-test-form';live['ipa']='test'
        live['display_forms'][0]['orthography']='updated-test-form'
        live['display_forms'][0]['ipa']='test'
        self.run_build()
        response=next(r for r in rows(self.output,'responses') if r['id']==live['id'])
        ann=next(r for r in rows(self.output,'annotations') if r['id']==live['id'])
        form=next(r for r in rows(self.output,'forms') if r['id']==live['id']+':1')
        self.assertEqual(response['transcription_orthography'],'updated-test-form')
        self.assertEqual(ann['orthography'],'updated-test-form')
        self.assertEqual(form['orthography'],'updated-test-form')
        self.assertEqual(rows(ROOT,'recordings'),rows(self.output,'recordings'))
        for name in ('coverage','forms','utterances','parse-lingpy'):
            self.assertIn('updated-test-form',(self.output/'data'/f'{name}.tsv').read_text('utf-8'))

    def test_unknown_media_fails(self):
        live=next(r for r in self.snapshot['responses'] if r['id']=='spk01:ear')
        live['published_audio_sha256']='0'*64
        with self.assertRaises(KeyError):self.run_build()

    def test_changed_master_fails(self):
        key=next(iter(self.masters));self.masters[key]['sha256']='0'*64
        with self.assertRaisesRegex(AssertionError,'Master changed'):self.run_build()

    def test_new_public_removal_requires_review(self):
        live=next(r for r in self.snapshot['responses'] if r['id']=='spk01:ear')
        live['visible']=False;live['display_forms']=[];live['published_audio_sha256']=None
        with self.assertRaisesRegex(ValueError,'disposition'):self.run_build()

    def test_hold_cannot_be_released_implicitly(self):
        live=next(r for r in self.snapshot['responses'] if self.responses[r['id']]['response_status']=='withheld')
        live['visible']=True
        with self.assertRaisesRegex(AssertionError,'Explicit hold'):self.run_build()

    def test_new_speaker_needs_release_approval(self):
        speaker=copy.deepcopy(self.snapshot['speakers'][0]);speaker['id']='spk100';speaker['label']='Speaker 100'
        self.snapshot['speakers'].append(speaker)
        with self.assertRaisesRegex(AssertionError,'New speakers'):self.run_build()

    def test_private_field_rejected(self):
        self.snapshot['speakers'][0]['email']='private-field-test'
        with self.assertRaises(AssertionError):self.run_build()


if __name__=='__main__':unittest.main()
