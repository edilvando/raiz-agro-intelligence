"""Download immutable, traceable official IBGE Census 2017 snapshots."""
import concurrent.futures,gzip,hashlib,json,time,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='scripts' else Path(__file__).resolve().parent
RAW=ROOT/'data/raw' if (ROOT/'scripts').exists() else ROOT
def read(url):
 for attempt in range(3):
  try:
   b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CensoAgroIntelligence/1.0'}),timeout=50).read()
   if b[:2]==b'\x1f\x8b': b=gzip.decompress(b)
   return json.loads(b)
  except Exception:
   if attempt==2:raise
   time.sleep(1)
def main():
 if (RAW/'manifest.json').exists():raise SystemExit('Snapshot already exists; use a new version directory to refresh.')
 RAW.mkdir(parents=True,exist_ok=True)
 tables=[6753,6778,6846,6871,6962]
 manifest=[]
 def save(name,url):
  d=read(url);b=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode();(RAW/name).write_bytes(b)
  return {'file':name,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(b).hexdigest()}
 for t in tables:
  manifest.append(save(f'metadata_{t}.json',f'https://servicodados.ibge.gov.br/api/v3/agregados/{t}/metadados'))
  m=json.loads((RAW/f'metadata_{t}.json').read_text())
  print(t,m['nome'],flush=True)
 specs=[('base',6753,'183|184',{829:[46302,46304]}),('activity',6778,'183',{12517:[113601,111519,111520,111521,111522,111523,111524,111525,114349,111526]}),('assistance',6846,'183',{12567:[41151,113111,113559]}),('tractors',6871,'1918|1862',{}),('internet',6962,'183',{798:[47179,40696,40697]})]
 jobs=[]
 for name,t,variables,overrides in specs:
  m=json.loads((RAW/f'metadata_{t}.json').read_text())
  classification='|'.join(str(c['id'])+'['+','.join(map(str,overrides.get(c['id'],[c['categorias'][0]['id']])))+']' for c in m['classificacoes'])
  url=f'https://servicodados.ibge.gov.br/api/v3/agregados/{t}/periodos/2017/variaveis/{variables}?localidades=N1[all]|N3[all]&classificacao={classification}'
  jobs.append((name+'.json',url))
 jobs.append(('states.json','https://servicodados.ibge.gov.br/api/v1/localidades/estados'))
 jobs.append(('brazil_states.geojson','https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:
  for entry in ex.map(lambda p:save(*p),jobs):manifest.append(entry);print(entry['file'],flush=True)
 (RAW/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
