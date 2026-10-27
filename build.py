"""Auditable, dependency-free data pipeline and standalone dashboard builder."""
import csv,hashlib,json,math,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='scripts' else Path(__file__).resolve().parent
FLAT=not (ROOT/'web').exists()
RAW=ROOT if FLAT else ROOT/'data/raw'; OUT=ROOT if FLAT else ROOT/'data/processed'
WEB=ROOT if FLAT else ROOT/'web'; ASSETS=ROOT if FLAT else ROOT/'assets'; DOCS=ROOT if FLAT else ROOT/'docs'
def load(name):return json.loads((RAW/name).read_text())
def number(v):
 if v=='-':return 0
 if v in ('...','..','X',''):return None
 return float(v) if '.' in v else int(v)
def extract(file,var,category):
 matches=[]
 for v in load(file):
  if v['id']!=str(var):continue
  for r in v['resultados']:
   cats={k for c in r['classificacoes'] for k in c['categoria']}
   if str(category) in cats:matches.append(r)
 if len(matches)!=1:raise ValueError((file,var,category,len(matches)))
 return {s['localidade']['id']:number(s['serie']['2017']) for s in matches[0]['series']}
def distance(a,b):return sum((x-y)**2 for x,y in zip(a,b))
def kmeans(x,k,seed):
 rng=random.Random(seed); centers=[x[rng.randrange(len(x))][:]]
 while len(centers)<k:
  weights=[min(distance(v,c) for c in centers) for v in x];target=rng.random()*sum(weights); acc=0
  for v,w in zip(x,weights):
   acc+=w
   if acc>=target:centers.append(v[:]);break
 labels=[-1]*len(x)
 for _ in range(150):
  nxt=[min(range(k),key=lambda j:distance(v,centers[j])) for v in x]
  if nxt==labels:break
  labels=nxt
  for j in range(k):
   rows=[v for v,l in zip(x,labels) if l==j]
   if not rows:return None
   centers[j]=[statistics.mean(c) for c in zip(*rows)]
 return labels,sum(distance(v,centers[l]) for v,l in zip(x,labels))
def silhouette(x,labels):
 scores=[]
 for i,v in enumerate(x):
  own=[math.sqrt(distance(v,w)) for j,w in enumerate(x) if i!=j and labels[j]==labels[i]]
  if not own:scores.append(0);continue
  a=statistics.mean(own)
  b=min(statistics.mean(math.sqrt(distance(v,w)) for j,w in enumerate(x) if labels[j]==c) for c in set(labels) if c!=labels[i])
  scores.append((b-a)/max(a,b) if max(a,b) else 0)
 return statistics.mean(scores)
def cluster(rows):
 features=['internet_pct','assistance_pct','tractor_pct','family_pct','log_mean_area']
 x0=[[r['internet']/r['establishments']*100,r['assistance']/r['establishments']*100,r['tractor_farms']/r['establishments']*100,r['family']/r['establishments']*100,math.log1p(r['area']/r['establishments'])] for r in rows]
 means=[statistics.mean(c) for c in zip(*x0)];std=[statistics.pstdev(c) for c in zip(*x0)]
 x=[[(v-m)/s for v,m,s in zip(row,means,std)] for row in x0]
 candidates=[]
 for k in range(2,6):
  fits=[f for seed in range(40) if (f:=kmeans(x,k,seed)) and min(f[0].count(c) for c in set(f[0]))>=3]
  if not fits:continue
  labels,inertia=min(fits,key=lambda f:f[1]);candidates.append({'k':k,'silhouette':silhouette(x,labels),'inertia':inertia,'labels':labels})
 best=max(candidates,key=lambda c:c['silhouette'])
 # Stable IDs ordered by average technical assistance; labels have no causal meaning.
 order=sorted(set(best['labels']),key=lambda c:statistics.mean(row['assistance']/row['establishments'] for row,l in zip(rows,best['labels']) if l==c))
 for row,l in zip(rows,best['labels']):row['cluster']=order.index(l)
 groups=[]
 for c in range(best['k']):
  members=[r for r in rows if r['cluster']==c]
  groups.append({'id':c,'name':f'Perfil {c+1}','members':[r['uf'] for r in members],'means':{key:statistics.mean(v[i] for v,r in zip(x0,rows) if r['cluster']==c) for i,key in enumerate(features)}})
 return {'algorithm':'k-means++ / z-score / Euclidean','features':features,'selection':'Maximum silhouette, k=2..5, minimum 3 UFs per group, lowest inertia of 40 initializations per k','n':27,'k':best['k'],'silhouette':best['silhouette'],'candidates':[{k:v for k,v in c.items() if k!='labels'} for c in candidates],'means':means,'std':std,'groups':groups,'limitations':'Exploratory description of 27 aggregated 2017 observations. No causal, predictive, individual-farm, or commercial validation.'}
def main():
 manifest=load('manifest.json')
 for m in manifest:
  assert hashlib.sha256((RAW/m['file']).read_bytes()).hexdigest()==m['sha256'],m['file']
 specs={'establishments':('base.json',183,46302),'area':('base.json',184,46302),'family':('base.json',183,46304),'family_area':('base.json',184,46304),'internet':('internet.json',183,40696),'no_internet':('internet.json',183,40697),'assistance':('assistance.json',183,113111),'no_assistance':('assistance.json',183,113559),'tractor_farms':('tractors.json',1918,46302),'tractors':('tractors.json',1862,46302)}
 values={key:extract(*spec) for key,spec in specs.items()}
 states=load('states.json');rows=[]
 for s in sorted(states,key=lambda s:s['id']):
  rows.append({'id':str(s['id']),'uf':s['sigla'],'name':s['nome'],'region':s['regiao']['nome'],**{key:v[str(s['id'])] for key,v in values.items()}})
 national={'id':'1','name':'Brasil',**{key:v['1'] for key,v in values.items()}}
 activities={}
 for r in load('activity.json')[0]['resultados']:
  c=next(c['categoria'] for c in r['classificacoes'] if c['id']=='12517');cid,name=next(iter(c.items()))
  if cid=='113601':continue
  activities[cid]={'name':name,'values':{s['localidade']['id']:number(s['serie']['2017']) for s in r['series']}}
 checks=[]
 for key in specs:
  actual=sum(r[key] for r in rows if r[key] is not None);official=national[key]
  # Areas are published rounded to whole hectares; allow one rounding unit per UF.
  tolerance=27 if key in ['area','family_area'] else 0
  assert abs(actual-official)<=tolerance,(key,actual,official)
  checks.append({'field':key,'sum_states':actual,'official_brazil':official,'difference':actual-official,'tolerance':tolerance})
 for r in rows+[national]:
  for key in ['family','internet','assistance','tractor_farms']:
   assert r[key] is not None and 0<=r[key]<=r['establishments'],(r['id'],key)
  assert r['internet']+r['no_internet']==r['establishments']
  assert r['assistance']+r['no_assistance']==r['establishments']
  av=[a['values'][r['id']] for a in activities.values()]
  assert all(v is not None for v in av),(r['id'],'suppressed activity')
  assert sum(av)==r['establishments'],(r['id'],'activities',sum(av))
 model=cluster(rows)
 data={'year':2017,'retrieved_at':max(m['retrieved_at'] for m in manifest),'states':rows,'national':national,'activities':activities,'model':model,'sources':manifest}
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'census.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 with (OUT/'states.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 qa={'status':'passed','n_states':len(rows),'national_reconciliations':checks,'partition_checks':84,'raw_hashes_checked':len(manifest),'missing_values':sum(v is None for r in rows for v in r.values()),'model':model}
 (OUT/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
 html=(WEB/'template.html').read_text().replace('__CSS__',(WEB/'style.css').read_text()).replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':'))).replace('__MODELS__',(WEB/'models.js').read_text()).replace('__I18N__',(WEB/'i18n.js').read_text()).replace('__APP__',(WEB/'app.js').read_text()).replace('__CHART__',(ASSETS/'chart.umd.min.js').read_text()).replace('__MAP__',make_map(load('brazil_states.geojson'),rows))
 (DOCS/'index.html').write_text(html)
 print(json.dumps({'national':national,'checks':len(checks),'groups':model['groups'],'silhouette':model['silhouette'],'html_bytes':len(html.encode())},ensure_ascii=False,indent=2))
def make_map(geo,rows):
 byid={r['id']:r for r in rows}
 def xy(c):return ((c[0]+74)*11,(-math.log(math.tan(math.pi/4+c[1]*math.pi/360))*180/math.pi+6)*11)
 paths=[]
 for f in geo['features']:
  r=byid[f['properties']['codarea']];g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
  ds=[]
  for poly in polys:
   for ring in poly:
    ds.append('M'+'L'.join(f'{xy(c)[0]:.2f},{xy(c)[1]:.2f}' for c in ring)+'Z')
  paths.append(f'<path d="{"".join(ds)}" data-state="{r["id"]}" role="button" tabindex="0" aria-label="Selecionar {r["name"]}"><title>{r["name"]}</title></path>')
 return ''.join(paths)
if __name__=='__main__':main()
