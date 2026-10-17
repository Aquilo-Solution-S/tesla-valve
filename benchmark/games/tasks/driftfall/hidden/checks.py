import json
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parent
KINDS={'sprig':3,'prong':5,'ramp':5,'arch':5,'reed':5,'pulse':3}
ERRORS={'bad_json','bad_request','unknown_command','not_started','finished','paused','hold_used','bad_replay'}


def exact_scenarios(game, step):
    cases=json.loads((ROOT/f'scenarios_f{step}.json').read_text())
    for case in cases:
        for i, event in enumerate(case['events']):
            got=game.send(event['command'])
            assert got==event['reply'], (case['name'],i,got,event['reply'])
            snapshot=game.state()
            # New steps add specified fields; earlier scenarios compare every field
            # specified at their own step, permitting those later additions.
            expected=event['state']
            assert {k:snapshot[k] for k in expected}==expected, (case['name'],i,snapshot,expected)
            invariants(snapshot)


def refusal(game, command, error):
    before=game.state()
    assert game.send(command)=={'ok':False,'error':error}
    assert game.state()==before


def invariants(s):
    assert isinstance(s,dict)
    required={'phase','board','active','score','lines','level'}
    allowed=required|{'held','preview','hold_available','mode','elapsed_ms'}
    assert required<=s.keys()<=allowed
    assert s['phase'] in {'idle','playing','paused','over','won'}
    assert len(s['board'])==18
    assert all(type(row) is str and len(row)==10 and set(row)<={'.','#'} for row in s['board'])
    assert all(type(s[k]) is int and s[k]>=0 for k in ['score','lines','level'])
    assert s['level']==1+s['lines']//4
    a=s['active']
    if s['phase'] in {'idle','over','won'}:
        assert a is None
    else:
        assert set(a)=={'kind','cells'} and a['kind'] in KINDS
        cells=a['cells']
        assert len(cells)==KINDS[a['kind']]
        assert all(type(c) is list and len(c)==2 and all(type(v) is int for v in c) for c in cells)
        assert len({tuple(c) for c in cells})==len(cells)
        assert cells==sorted(cells,key=lambda c:(c[1],c[0]))
        for x,y in cells:
            assert 0<=x<10 and 0<=y<18 and s['board'][y][x]=='.'
    if 'held' in s:
        assert s['held'] is None or s['held'] in KINDS
        assert type(s['hold_available']) is bool
        assert len(s['preview'])==(0 if s['phase']=='idle' else 3)
        assert all(k in KINDS for k in s['preview'])
        if s['phase'] in {'idle','over','won'}: assert s['hold_available'] is False
    if 'mode' in s:
        assert s['mode'] in {'endless','rush'}
        assert type(s['elapsed_ms']) is int and s['elapsed_ms']>=0
        if s['phase']=='won': assert s['mode']=='rush' and s['lines']>=4


def replay(seed=742, mode='endless', events=None, end_ms=1200):
    if events is None:
        events=[{'at_ms':0,'key':'left'},{'at_ms':600,'key':'hard'}]
    return {'cmd':'replay','document':{'seed':seed,'mode':mode,'events':events,'end_ms':end_ms}}


def live(game, doc):
    assert game.send({'cmd':'new','seed':doc['seed'],'mode':doc['mode']})=={'ok':True}
    previous=0
    for e in doc['events']:
        game.send({'cmd':'tick','ms':e['at_ms']-previous})
        game.send({'cmd':e['key']} if e['key'] in {'pause','resume'} else {'cmd':'input','key':e['key']})
        previous=e['at_ms']
    game.send({'cmd':'tick','ms':doc['end_ms']-previous})
    return game.state()


def fuzz(game, step, count=2000):
    rng=random.Random(0xD71F000+step)
    assert game.send({'cmd':'new','seed':15 if step>=4 else 742})=={'ok':True}
    before=game.state()
    invariants(before)
    valid_keys=['left','right','rotate','soft','hard']+(['hold'] if step>=3 else [])
    invalids=['','{','[]','null','42','true','{}','{"cmd":3}','{"cmd":"unknown"}',
              {'cmd':'tick','ms':-1},{'cmd':'tick','ms':1000001},{'cmd':'tick','ms':True},
              {'cmd':'tick','ms':1.5},{'cmd':'tick'}, {'cmd':'input','key':'sideways'},
              {'cmd':'input','key':None},{'cmd':'new','seed':-1},{'cmd':'new','seed':4294967296},
              {'cmd':'new','seed':False},{'cmd':'state','extra':0},'{"cmd":"new","seed":1e0}']
    if step>=2: invalids += [{'cmd':'pause','ms':0},{'cmd':'resume','key':'left'}]
    if step>=3: invalids += [{'cmd':'input','key':['hold']},{'cmd':'input','key':'HOLD'}]
    if step>=5: invalids += [{'cmd':'new','seed':1,'mode':'other'},{'cmd':'new','seed':1,'mode':None}]
    if step>=6:
        invalids += [replay(events=[{'at_ms':100,'key':'hard'},{'at_ms':90,'key':'left'}]),
                     replay(events=[{'at_ms':0,'key':'unknown'}]),{'cmd':'replay','document':None}]
    failures=accepted=0
    for _ in range(count):
        roll=rng.random()
        if roll<.25:
            c=rng.choice(invalids)
        elif roll<.31:
            c={'cmd':'new','seed':rng.randrange(2**32)}
            if step>=5: c['mode']=rng.choice(['endless','rush'])
        elif roll<.58:
            c={'cmd':'input','key':rng.choice(valid_keys)}
        elif roll<.80:
            c={'cmd':'tick','ms':rng.choice([0,1,89,599,600,601,1000000,rng.randrange(5000)])}
        elif roll<.92 and step>=2:
            c={'cmd':rng.choice(['pause','resume'])}
        elif roll<.97 and step>=6:
            keys=valid_keys+['pause','resume']
            times=sorted(rng.randrange(2000) for _ in range(rng.randrange(12)))
            c=replay(seed=rng.randrange(2**32),mode=rng.choice(['endless','rush']),
                     events=[{'at_ms':t,'key':rng.choice(keys)} for t in times],end_ms=2000)
        else:
            c={'cmd':'state'}
        r=game.send(c)
        after=game.state() # A reply and invariant check for EVERY random command.
        invariants(after)
        if not r['ok']:
            failures+=1
            assert r['error'] in ERRORS
            assert after==before, (c,r,before,after)
        else:
            accepted+=1
            if not isinstance(c,dict) or c.get('cmd') not in {'new','replay'}:
                assert after['score']>=before['score']
                assert after['lines']>=before['lines']
                if 'elapsed_ms' in after: assert after['elapsed_ms']>=before['elapsed_ms']
        assert game.proc.poll() is None
        before=after
    assert failures>=100 and accepted>=100
