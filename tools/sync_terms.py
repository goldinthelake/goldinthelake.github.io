"""claude.ai 편집용 아티팩트 db 덤프(JSON) → 홈페이지 TERMS 배열 동기화.
사용: python3 sync_terms.py <glossary_dump_dir> <words_dump_dir> <homepage_dir>
- glossary: 업무 연관성(context) 제외, 공개 필드만
- words: context → memo, 기존 홈페이지 image 객체는 term 기준으로 유지
"""
import json, os, re, sys, glob

def load(d):
    out=[]
    for f in sorted(glob.glob(os.path.join(d,'*.json'))):
        j=json.load(open(f))
        out.append(j.get('data',j))
    return out

def js_array(items):
    return 'const TERMS=[\n' + ',\n'.join('  '+json.dumps(t,ensure_ascii=False) for t in items) + '\n];'

def existing(path):
    s=open(path).read()
    m=re.search(r'const TERMS=(\[[\s\S]*?\n\]);',s)
    return s,m

def pick(t,keys):
    o={}
    for k in keys:
        v=t.get(k)
        if v in (None,'',[]): continue
        o[k]=v
    return o

gdir,wdir,home=sys.argv[1:4]
G=[pick(t,['term','reading','category','aliases','definition','source','sourceUrl']) for t in load(gdir)]
W=[]
gp=os.path.join(home,'glossary/index.html'); wp=os.path.join(home,'words/index.html')
# keep images by term from current words page (parse via node)
import subprocess
ws,wm=existing(wp)
cur=json.loads(subprocess.run(['node','-e','process.stdout.write(JSON.stringify(eval(require("fs").readFileSync(0,"utf8"))))'],input=wm.group(1),capture_output=True,text=True,check=True).stdout)
imgs={t['term']:t['image'] for t in cur if t.get('image')}
for t in load(wdir):
    o=pick(t,['term','reading','category','aliases','definition','context','source','sourceUrl'])
    if 'context' in o: o['memo']=o.pop('context')
    if t['term'] in imgs: o['image']=imgs[t['term']]
    elif t.get('imageUrl'): print('NOTE: 사진 링크만 있고 홈페이지용 이미지 정보 없음 →',t['term'])
    W.append(o)
for path,items in [(gp,G),(wp,W)]:
    s,m=existing(path)
    s=s[:m.start()]+js_array(items)+s[m.end():]
    open(path,'w').write(s)
    print(path, len(items))
