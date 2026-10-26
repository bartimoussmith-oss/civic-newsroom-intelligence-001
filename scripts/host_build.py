"""Dedicated public derived-data host; does not modify source repositories."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import engine
import file_parts

REPOSITORY='bartimoussmith-oss/civic-newsroom-intelligence-001'
TOOLKIT='18efc5218131792fb311493d4678b700c4d8d71a'
BUDGET=512*1024*1024
FILE_LIMIT=45*1024*1024

def digest(path):
    h=sha256()
    with Path(path).open('rb') as stream:
        for raw in iter(lambda:stream.read(1024*1024),b''):h.update(raw)
    return h.hexdigest()

def measure(root):return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())

def verify(public):
    public=Path(public);report=json.loads((public/'collection.json').read_text(encoding='utf-8'))
    metadata=report['file_manifest']
    if digest(public/metadata['path'])!=metadata['sha256']:raise ValueError('File manifest integrity failure')
    manifest=json.loads((public/metadata['path']).read_text(encoding='utf-8'))
    if manifest['schema']!='intelligence-files-v1':raise ValueError('Unexpected file manifest')
    for name in manifest['files']:file_parts.reconstruct(public,manifest,name)
    if any(p.is_symlink() for p in public.rglob('*')):raise ValueError('Unexpected output symlink')
    if any(p.stat().st_size>FILE_LIMIT for p in public.rglob('*') if p.is_file()):raise ValueError('Physical file exceeds 45 MiB')
    if measure(public)>BUDGET:raise ValueError('Dedicated host capacity exceeded: '+str(measure(public))+' bytes')
    return report

def build_release(dataset,out,expected_records):
    out=Path(out);previous=None
    try:engine.build(engine.load(dataset),out,TOOLKIT)
    except ValueError as error:
        if str(error) not in ('Intelligence file needs further partitioning','Intelligence output exceeds partition budget') or not (out/'public/collection.json').is_file():raise
        previous=str(error)
    public=out/'public';report=json.loads((public/'collection.json').read_text(encoding='utf-8'))
    with sqlite3.connect(out/'intelligence.sqlite') as db:
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity failure')
        if db.execute('SELECT count(*) FROM records').fetchone()[0]!=report['records'] or report['records']!=expected_records:raise ValueError('Incomplete source collection')
    source=json.loads((Path(dataset)/'published.json').read_text(encoding='utf-8'))
    report.update({'file_manifest':file_parts.pack(public),'previous_size_guard':previous,'source_dataset_revision':source['dataset_revision'],'source_manifest_sha256':source['manifest_sha256'],'host_builder_revision':os.environ.get('GITHUB_SHA'),'storage_policy':{'repository':REPOSITORY,'derived_budget_bytes':BUDGET,'physical_file_limit_bytes':FILE_LIMIT},'database_sha256':digest(out/'intelligence.sqlite'),'database_gzip_sha256':digest(out/'database.sqlite.gz'),'packaging_note':'All logical bytes retained; only newly generated storage encodings changed. No source records modified.'})
    file_parts.dump(public/'collection.json',report)
    verify(public)
    rows=engine.search(out/'intelligence.sqlite','annexation',3)
    if not rows:raise ValueError('Real-corpus retrieval smoke test returned no evidence')
    packet=engine.packet(out/'intelligence.sqlite',[rows[0]['passage_id']])
    if packet['evidence'][0]['text']!=rows[0]['text']:raise ValueError('Evidence retrieval mismatch')
    return report

def publish(public):
    if os.environ.get('GITHUB_REPOSITORY')!=REPOSITORY:raise ValueError('Refusing publication outside the dedicated host')
    public=Path(public);report=verify(public);run=os.environ['GITHUB_RUN_ID'];attempt=os.environ['GITHUB_RUN_ATTEMPT']
    if not run.isdigit() or not attempt.isdigit():raise ValueError('Invalid workflow identity')
    target=Path('data')/('run-'+run+'-'+attempt)
    if target.exists():raise ValueError('Immutable generation already exists')
    if measure('data')+measure(public)>BUDGET:raise ValueError('Existing plus incoming derived data exceeds host capacity; allocate another host instead of deleting history')
    shutil.copytree(public,target)
    def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
    git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('add',target.as_posix());git('commit','-m','data: verified intelligence generation '+run+'-'+attempt)
    revision=git('rev-parse','HEAD')
    pointer={'schema':'civic-intelligence-publication-v1','data_repository':REPOSITORY,'revision':revision,'base_url':'https://raw.githubusercontent.com/'+REPOSITORY+'/'+revision+'/'+target.as_posix()+'/','collection_sha256':digest(target/'collection.json'),'records':report['records'],'passages':report['passages'],'reference_mentions':report['reference_mentions'],'language_candidates':report['language_candidates'],'verified_entity_resolution':False,'source_independence':'unresolved','workflow_run':run,'stored_bytes':measure(target)}
    Path('intelligence-publication.json').write_text(json.dumps(pointer,indent=2),encoding='utf-8')
    git('add','intelligence-publication.json');git('commit','-m','publish: pin intelligence data '+revision)
    for retry in range(3):
        git('fetch','origin','main');git('merge','--no-edit','origin/main')
        if subprocess.run(['git','push','origin','HEAD:main']).returncode==0:return pointer
    raise RuntimeError('Publication push failed after bounded retries; no forced update attempted')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','publish']);p.add_argument('--dataset-repo');p.add_argument('--out',required=True);a=p.parse_args()
    try:
        if a.command=='build':
            expected=json.loads(Path('source-publication.json').read_text(encoding='utf-8'));actual=json.loads((Path(a.dataset_repo)/'published.json').read_text(encoding='utf-8'))
            if actual!=expected:raise ValueError('Unexpected source publication descriptor')
            result=build_release(a.dataset_repo,a.out,expected['records'])
        else:result=publish(Path(a.out)/'public')
        print(json.dumps(result,indent=2))
    except Exception as error:
        message=(type(error).__name__+': '+str(error)).replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print('::error::'+message[:1800],file=sys.stderr)
        raise
