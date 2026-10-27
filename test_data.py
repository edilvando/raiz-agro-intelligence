import hashlib,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='tests' else Path(__file__).resolve().parent
FLAT=not (ROOT/'web').exists()
RAW=ROOT if FLAT else ROOT/'data/raw'; OUT=ROOT if FLAT else ROOT/'data/processed';DOCS=ROOT if FLAT else ROOT/'docs'
sys.path.insert(0,str(ROOT if FLAT else ROOT/'scripts'))
import build
class CensusQA(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((OUT/'census.json').read_text())
 def test_official_national_counts_and_reconciliations(self):
  d=self.data;n=d['national'];self.assertEqual(len(d['states']),27);self.assertEqual(len({r['id'] for r in d['states']}),27)
  for key,value in {'establishments':5073324,'family':3897408,'internet':1430156,'assistance':1025443,'tractor_farms':734280,'tractors':1229907}.items():
   self.assertEqual(n[key],value);self.assertEqual(sum(r[key] for r in d['states']),value)
 def test_independent_raw_observations_match_every_state(self):
  mapping=[('internet.json','183','798','40696','internet'),('assistance.json','183','12567','113559','no_assistance'),('tractors.json','1918','829','46302','tractor_farms')]
  for file,var,classification,category,key in mapping:
   raw=json.loads((RAW/file).read_text());variable=next(v for v in raw if v['id']==var)
   result=next(r for r in variable['resultados'] if any(c['id']==classification and category in c['categoria'] for c in r['classificacoes']))
   source={s['localidade']['id']:int(s['serie']['2017']) for s in result['series']}
   for r in self.data['states']:self.assertEqual(r[key],source[r['id']])
 def test_partitions_and_geography(self):
  for r in self.data['states']+[self.data['national']]:
   self.assertEqual(r['internet']+r['no_internet'],r['establishments']);self.assertEqual(r['assistance']+r['no_assistance'],r['establishments'])
   self.assertEqual(sum(v['values'][r['id']] for v in self.data['activities'].values()),r['establishments'])
  geo=json.loads((RAW/'brazil_states.geojson').read_text());self.assertEqual({f['properties']['codarea'] for f in geo['features']},{r['id'] for r in self.data['states']})
 def test_manifest_and_null_semantics(self):
  for entry in json.loads((RAW/'manifest.json').read_text()):self.assertEqual(hashlib.sha256((RAW/entry['file']).read_bytes()).hexdigest(),entry['sha256'])
  self.assertIsNone(build.number('X'));self.assertIsNone(build.number('...'));self.assertEqual(build.number('-'),0)
 def test_cluster_reproducible_and_silhouette_independent_sanity(self):
  rows=json.loads(json.dumps(self.data['states']));self.assertEqual(build.cluster(rows),self.data['model']);self.assertTrue(all(sum(r['cluster']==c for r in rows)>=3 for c in range(self.data['model']['k'])))
  self.assertGreater(build.silhouette([[0],[1],[10],[11]],[0,0,1,1]),.8)
  model=self.data['model'];self.assertEqual(model['silhouette'],max(c['silhouette'] for c in model['candidates']))
 def test_standalone_artifact_has_no_placeholders(self):
  html=(DOCS/'index.html').read_text()
  for token in ['__CSS__','__DATA__','__APP__','__MAP__']:self.assertNotIn(token,html)
  self.assertEqual(html.count('data-state='),27)
if __name__=='__main__':unittest.main()
