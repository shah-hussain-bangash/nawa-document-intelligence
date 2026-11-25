"""Small loopback-only readiness probe, not a production load/soak test."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time
from urllib.parse import urlparse
import httpx


def probe(url, requests=100, concurrency=4):
    route=urlparse(url)
    if route.scheme!='http' or route.hostname not in {'localhost','127.0.0.1','::1'} or route.username or route.password or route.path not in {'','/'} or route.query or route.fragment:
        raise ValueError('Only a loopback HTTP application URL is accepted')
    if not 1<=requests<=200 or not 1<=concurrency<=8:
        raise ValueError('Use 1..200 requests and 1..8 workers')
    def once(_):
        started=time.monotonic()
        try:
            response=httpx.get(url.rstrip('/')+'/health/ready',timeout=5,trust_env=False,follow_redirects=False)
            ok=response.status_code==200 and response.json().get('status')=='ready'
        except (httpx.HTTPError,ValueError):ok=False
        return (time.monotonic()-started)*1000,ok
    started=time.monotonic()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:rows=list(executor.map(once,range(requests)))
    latencies=sorted(row[0] for row in rows)
    return {'scope':'Small developer loopback readiness/DB probe only; no authenticated workflow load, soak, SLO, RTO or capacity certification','requests':requests,'concurrency':concurrency,'failed':sum(not row[1] for row in rows),'duration_seconds':round(time.monotonic()-started,3),'p50_ms':round(latencies[len(rows)//2],2),'p95_ms':round(latencies[min(len(rows)-1,int(len(rows)*.95))],2)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:5173')
    parser.add_argument('--requests',type=int,default=100)
    parser.add_argument('--concurrency',type=int,default=4)
    parser.add_argument('--output',default='artifacts/load-probe.json')
    args=parser.parse_args()
    result=probe(args.url,args.requests,args.concurrency)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2)+'\n')
    print('Readiness probe:',result['requests'],'requests;',result['failed'],'failed; p95',result['p95_ms'],'ms. Report:',path)
    raise SystemExit(1 if result['failed'] else 0)
