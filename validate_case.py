"""Independent audit: exact rational scores vs browser model, source rows and scenarios."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='scripts' else Path(__file__).resolve().parent
FLAT=not (ROOT/'web').exists();RAW=ROOT if FLAT else ROOT/'data/raw';OUT=ROOT if FLAT else ROOT/'analysis';PROC=ROOT if FLAT else ROOT/'data/processed'
case=json.loads((OUT/'pilot_case.json').read_text());data=json.loads((PROC/'census.json').read_text());checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
for m in json.loads((RAW/'manifest.json').read_text()):check('hash:'+m['file'],hashlib.sha256((RAW/m['file']).read_bytes()).hexdigest()==m['sha256'])
def raw_values(file,var,classification,category):
 d=json.loads((RAW/file).read_text());v=next(v for v in d if v['id']==var);r=next(r for r in v['resultados'] if any(c['id']==classification and category in c['categoria'] for c in r['classificacoes']));return {s['localidade']['id']:int(s['serie']['2017']) for s in r['series']}
base=raw_values('base.json','183','829','46302');internet=raw_values('internet.json','183','798','40696')
for r in case['observed']:
 check('raw-counts:'+r['uf'],r['internet']==internet[r['id']] and r['establishments']==base[r['id']]);check('rate:'+r['uf'],math.isclose(r['intensity'],100*internet[r['id']]/base[r['id']],abs_tol=1e-10))
rows=data['states'];counts=[internet[r['id']] for r in rows];rates=[Fraction(internet[r['id']],base[r['id']]) for r in rows]
def percentile(v,values):return Fraction(100, len(values)-1)*(sum(x<v for x in values)+Fraction(sum(x==v for x in values)-1,2))
for sensitivity in case['selection']['sensitivity']:
 w=sensitivity['weight'];scores={r['uf']:percentile(counts[i],counts)*Fraction(w,100)+percentile(rates[i],rates)*Fraction(100-w,100) for i,r in enumerate(rows)}
 cutoff=sorted(scores.values(),reverse=True)[2];eligible={uf for uf,s in scores.items() if s>=cutoff}
 check('eligible-ties:'+str(w),eligible==set(sensitivity['eligible_top_three']))
 for r in sensitivity['rows']:
  check('score:'+str(w)+':'+r['uf'],abs(float(scores[r['uf']])-r['score'])<1e-10);check('rank:'+str(w)+':'+r['uf'],r['rank']==1+sum(s>scores[r['uf']] for s in scores.values()))
check('reference-year',case['reference_year']==2017);check('hypothetical-label',case['status']=='fictional_case_no_field_results' and case['assumptions']['fictional'] is True)
check('snapshot-hash',case['source_snapshot_sha256']==hashlib.sha256((PROC/'census.json').read_bytes()).hexdigest())
check('selected-ufs',set(case['selection']['selected_states'])=={'PR','SC','RS'})
chosen=[r for r in rows if r['uf'] in case['selection']['selected_states']]
check('same-region-and-cluster-caveat',len({r['region'] for r in chosen})==len({r['cluster'] for r in chosen})==1)
for plan in case['plans']:
 check('unobserved-actuals:'+plan['uf'],all(v is None for v in plan['actuals'].values()));check('unvalidated-fields:'+plan['uf'],all(v is None for v in plan['current_validation'].values()))
 check('capacity:'+plan['uf'],plan['scenario']['contacts']==min(Fraction(plan['historical_base'],100),50)==50)
 check('scenario:'+plan['uf'],plan['scenario']['customers']==3 and plan['scenario']['mrr']==600 and plan['scenario']['prospectingCost']==2000)
 check('funnel-targets:'+plan['uf'],50>=plan['targets']['interviews']>=plan['targets']['activated_trials']>=plan['targets']['paid_customers'])
check('budget',case['scenario_totals']['total_incremental_cost']==150*40+18*1.5*100+1300==10000)
check('totals',case['scenario_totals']['contacts']==150 and case['scenario_totals']['customers']==9 and case['scenario_totals']['mrr']==1800)
for s in case['alternative_scenarios']:check('alternate-conversion:'+str(s['conversion_pct']),s['customers']==Fraction(150*s['conversion_pct'],100) and s['mrr_brl']==s['customers']*200)
report={'status':'passed','checks':len(checks),'method':'Independent Python Fraction percentile/ranking audit, raw-source reconciliation and scenario arithmetic','reference_year':2017,'actual_results':'all null','details':checks}
(OUT/'pilot_case_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='details'},ensure_ascii=False))
