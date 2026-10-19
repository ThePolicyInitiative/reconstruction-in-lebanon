"""Check all PPA listing pages and persist new tenders plus an alert outbox."""
from __future__ import annotations
import argparse
import concurrent.futures
import csv
import gzip
import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from .ppa_parser import START, listing, now, parse_detail

ROOT=Path(__file__).resolve().parent

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n'
    if path.exists() and path.read_text(encoding='utf-8')==content:
        return
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(content,encoding='utf-8',newline='\n')
    temp.replace(path)

def fetch_html(url):
    error=None
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={
                'User-Agent':'PPA-Tender-Monitor/1.0 (+https://github.com/ThePolicyInitiative/mona2asat)',
                'Accept':'text/html','Accept-Encoding':'gzip'})
            with urllib.request.urlopen(request,timeout=35) as response:
                body=response.read()
                if response.headers.get('Content-Encoding')=='gzip':
                    body=gzip.decompress(body)
            if b'<html' not in body.lower():
                raise ValueError('Expected an HTML page')
            return body
        except (OSError,ValueError,urllib.error.URLError) as exc:
            error=exc
            if isinstance(exc,urllib.error.HTTPError) and exc.code in (401,403,404):
                break
            if attempt<2:
                time.sleep(2**attempt*2)
    raise RuntimeError(f'Could not read {url}: {type(error).__name__}') from error

def collect_listing(fetch=fetch_html, workers=3):
    """Reject partial/drifting pagination. Retry once if the listing moves mid-scan."""
    last_error=None
    for attempt in range(2):
        first=listing(fetch(START),1)
        pages={1:first}
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            jobs={pool.submit(fetch,START+f'?page={p}'):p for p in range(2,first['last_page']+1)}
            for future in concurrent.futures.as_completed(jobs):
                p=jobs[future]
                pages[p]=listing(future.result(),p)
        ordered=[pages[p] for p in sorted(pages)]
        records=[r for page in ordered for r in page['records']]
        ids=[r['id'] for r in records]
        coherent=(len(ids)==first['total'] and len(set(ids))==len(ids)
                  and all(p['total']==first['total'] for p in ordered)
                  and [p['first'] for p in ordered]==[1+sum(len(q['records']) for q in ordered[:i]) for i in range(len(ordered))])
        if coherent:
            return records,len(ordered)
        last_error=RuntimeError('PPA listing changed during pagination; no state was advanced')
    raise last_error

def compact_index(record):
    def field(label):
        return next((v for f in record['fields'] if f['section_id']=='tenderInfo' and not f['context']
                     and f['label']==label for v in f['values'] if v),'')
    h,lv=record['header'],record['listing_values']
    return {'id':record['id'],'title':record['title'],'procuring_entity':h.get('الجهة الشارية',''),
            'procurement_code':lv.get('رمز الشراء',''),'procurement_method':lv.get('طريقة الشراء',''),
            'status':h.get('الحالة',''),'announced_on':h.get('أُعلنت في',lv.get('أعلنت في','')),
            'submission_deadline':field('الموعد النهائي لتقديم العروض'),
            'opening_at':field('موعد جلسة فتح العروض الإدارية والفنية'),
            'source_url':record['source_url'],'attachment_links':len(record['attachments']),
            'detail_file':f"tenders/{record['id']}.json"}

def write_index(data_dir,index):
    ordered=sorted(index.values(),key=lambda r:int(r['id']),reverse=True)
    save_json(data_dir/'index.json',ordered)
    if ordered:
        buffer=io.StringIO(newline='')
        writer=csv.DictWriter(buffer,fieldnames=list(ordered[0]),lineterminator='\n')
        writer.writeheader()
        writer.writerows(ordered)
        (data_dir/'tenders.csv').write_text('\ufeff'+buffer.getvalue(),encoding='utf-8',newline='\n')

def process_scan(data_dir, records, page_count, fetch=fetch_html, workers=3, max_new=25):
    """A failed detail stays pending and is retried even if it leaves the list."""
    state_path=data_dir/'state.json'
    if not state_path.exists():
        raise RuntimeError('Missing baseline state. Run seed.py before enabling alerts.')
    state=read_json(state_path)
    if state.get('schema_version')!=1 or not isinstance(state.get('known_ids'),list):
        raise ValueError('Invalid baseline state')
    known=set(state['known_ids'])
    pending=state.setdefault('pending_details',{})
    for r in records:
        if r['id'] not in known:
            pending[r['id']]=r
    # Persist discoveries before the network phase; a retry will not forget them.
    save_json(state_path,state)
    index={r['id']:r for r in read_json(data_dir/'index.json')}
    outbox=read_json(data_dir/'alerts.json')
    failures=[]
    added=[]
    batch=list(pending.values())[:max_new]
    def get_detail(r):
        return parse_detail(r,fetch(r['source_url']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(get_detail,r):r for r in batch}
        for future in concurrent.futures.as_completed(jobs):
            r=jobs[future]
            try:
                detail=future.result()
                save_json(data_dir/'tenders'/(r['id']+'.json'),detail)
                index[r['id']]=compact_index(detail)
                # Preserve an existing alert result when recovering from a partial save.
                outbox.setdefault(r['id'],{'created_at':now(),'status':'pending'})
                known.add(r['id'])
                del pending[r['id']]
                added.append(r['id'])
            except Exception as exc:
                failures.append({'id':r['id'],'error':str(exc)})
    if added:
        write_index(data_dir,index)
    save_json(data_dir/'alerts.json',outbox)
    state['known_ids']=sorted(known,key=int)
    save_json(state_path,state)
    summary={'checked_at':now(),'listing_pages':page_count,'listed_tenders':len(records),
             'new_tenders':len(added),'new_ids':sorted(added,key=int),
             'pending_details':len(pending),'detail_failures':failures}
    # One heartbeat commit per day, plus meaningful changes. Full check times remain in Actions.
    status_path=data_dir/'status.json'
    previous=read_json(status_path) if status_path.exists() else {}
    if added or failures or previous.get('checked_at','')[:10]!=summary['checked_at'][:10] or previous.get('pending_details')!=len(pending) or previous.get('detail_failures'):
        save_json(status_path,summary)
    return summary

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-dir',type=Path,default=ROOT/'data')
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--max-new',type=int,default=25)
    args=parser.parse_args()
    records,pages=collect_listing(workers=args.workers)
    summary=process_scan(args.data_dir,records,pages,workers=args.workers,max_new=args.max_new)
    print(json.dumps(summary,ensure_ascii=False))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
            f.write(f"## Tender check\n\nChecked at {summary['checked_at']}. Scanned {pages} pages and {len(records)} tenders. "
                    f"New details saved: {summary['new_tenders']}. Pending retries: {summary['pending_details']}.\n")
    if summary['detail_failures']:
        raise SystemExit(1)

if __name__=='__main__':
    main()
