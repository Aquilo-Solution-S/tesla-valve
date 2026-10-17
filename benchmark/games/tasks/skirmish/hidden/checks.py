"""Black-box properties shared by cumulative tests. No reference is an oracle."""
from copy import deepcopy
import json
import heapq
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parent
MAP=['.........','..ss..#..','.s.#..#..','...#ss...','.##...##.',
     '...ss#...','..#..#.s.','..#..ss..','.........']
HP={'lancer':8,'bolt':6,'glider':5,'mender':7}
SIGHT={'lancer':3,'bolt':4,'glider':2,'mender':5}
ERRORS={'bad_json','bad_request','unknown_command','not_started','finished','turn_ended',
        'unavailable','invalid_order','bad_document'}

def invariants(s):
    assert set(s)=={'turn','phase','winner','ended','units'}
    assert type(s['turn']) is int and s['turn']>=0
    assert s['phase'] in {'idle','planning','finished'}
    assert s['winner'] is None or type(s['winner']) is int and s['winner'] in {0,1,2}
    assert s['ended'] in [[],[1],[2]]
    assert len(s['units'])<=20
    ids=set();positions=set();owners=set()
    for u in s['units']:
        assert set(u)=={'id','owner','kind','x','y','hp','order'}
        assert type(u['id']) is int and 1<=u['id']<=99 and u['id'] not in ids
        assert type(u['owner']) is int and u['owner'] in {1,2}
        assert u['kind'] in HP
        assert type(u['hp']) is int and 1<=u['hp']<=HP[u['kind']]
        assert all(type(u[k]) is int and 0<=u[k]<9 for k in ['x','y'])
        pos=(u['x'],u['y']);assert pos not in positions
        assert MAP[u['y']][u['x']]!='#' or u['kind']=='glider'
        ids.add(u['id']);positions.add(pos);owners.add(u['owner'])
        o=u['order']
        if o is not None:
            assert o['type'] in {'hold','move','attack'}
            if o['type']=='hold':assert set(o)=={'type'}
            if o['type']=='move':
                assert set(o)=={'type','to'} and len(o['to'])==2
                assert all(type(n) is int and 0<=n<9 for n in o['to'])
            if o['type']=='attack':assert set(o)=={'type','target'} and type(o['target']) is int and 1<=o['target']<=99
    assert [u['id'] for u in s['units']]==sorted(ids)
    if s['phase']=='idle':assert s==dict(turn=0,phase='idle',winner=None,ended=[],units=[])
    if s['phase']=='planning':assert s['turn']>=1 and s['winner'] is None and owners=={1,2}
    if s['phase']=='finished':
        assert s['turn']>=2 and not s['ended'] and len(owners)<=1
        assert s['winner']==(next(iter(owners)) if owners else 0)
        assert all(u['order'] is None for u in s['units'])

def visible(s,p):
    own=[u for u in s['units'] if u['owner']==p]
    return [[x,y] for y in range(9) for x in range(9) if any(
        abs(x-u['x'])+abs(y-u['y'])<=SIGHT[u['kind']] for u in own)]

def check_view(r,s,p):
    v=deepcopy(s);v['visible']=visible(s,p)
    v['units']=[u for u in v['units'] if u['owner']==p or [u['x'],u['y']] in v['visible']]
    for u in v['units']:
        if u['owner']!=p:u['order']=None
    assert r=={'ok':True,'view':v}

def sight_destinations(s,u):
    """Independent Dijkstra oracle for the rules stable from section 3 onward."""
    costs={(u['x'],u['y']):0};work=[(0,u['x'],u['y'])]
    budget={'lancer':3,'bolt':2,'glider':4,'mender':3}[u['kind']]
    while work:
        cost,x,y=heapq.heappop(work)
        if cost!=costs[(x,y)]:continue
        for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if not (0<=nx<9 and 0<=ny<9):continue
            terrain=MAP[ny][nx]
            if terrain=='#' and u['kind']!='glider':continue
            next_cost=cost+{'.':1,'s':2,'#':3}[terrain]
            if next_cost<=budget and next_cost<costs.get((nx,ny),1000):
                costs[(nx,ny)]=next_cost;heapq.heappush(work,(next_cost,nx,ny))
    cells=visible(s,u['owner'])
    occupied={(v['x'],v['y']) for v in s['units'] if v['owner']==u['owner'] or [v['x'],v['y']] in cells}
    return [list(c) for c in sorted(costs,key=lambda c:(c[1],c[0])) if c not in occupied]

def no_leak(c,r,s):
    if not isinstance(c,dict) or type(c.get('player')) is not int or c['player'] not in [1,2]:return
    p=c['player'];cmd=c.get('cmd')
    if cmd=='view' and r['ok']:check_view(r,s,p)
    own=next((u for u in s['units'] if u['id']==c.get('unit') and u['owner']==p),None)
    if cmd=='reachable' and r['ok']:
        assert own is not None and r['cells']==sight_destinations(s,own)
    if cmd=='order' and r['ok'] and c['order']['type']=='move':
        assert own is not None and c['order']['to'] in sight_destinations(s,own)
    target=c.get('target') if cmd=='forecast' else c.get('order',{}).get('target') if isinstance(c.get('order'),dict) else None
    if own is not None and target is not None and s['phase']=='planning' and (cmd!='order' or p not in s['ended']):
        enemy=next((u for u in s['units'] if u['id']==target),None)
        if enemy is not None and enemy['owner']!=p and [enemy['x'],enemy['y']] not in visible(s,p):
            assert r==dict(ok=False,error='unavailable')

def exact_scenarios(game,step):
    for case in json.loads((ROOT/f'scenarios_f{step}.json').read_text()):
        for n,event in enumerate(case['events']):
            assert game.send(event['command'])==event['reply'],(case['name'],n,event)
            s=game.state();invariants(s)
            # Compare only the snapshot members specified by this section.
            assert {k:s[k] for k in event['state']}==event['state'],(case['name'],n,s,event['state'])

def paired(a,b,c):
    """Only the first twin receives a refused input; both receive successes and future play."""
    before=a.state();assert b.state()==before
    r=a.send(c)
    if r['ok']:
        assert b.send(c)==r
    else:
        assert r['error'] in ERRORS
        assert a.state()==before,(c,r)
    after=a.state();invariants(after);assert after==b.state(),(c,r,after,b.state())
    return r,after

def refusal(a,b,c,error):
    r,_=paired(a,b,c);assert r==dict(ok=False,error=error)
    # Resolve the next boundary so equal snapshots cannot mask corrupted order storage.
    for p in [1,2]:paired(a,b,{'cmd':'end_turn','player':p})

def order(p,i,o):return dict(cmd='order',player=p,unit=i,order=o)

def query_outcome(a,b,s,rng,step):
    if step==1:
        # Section 1's sampled agreement cases use plain edge routes and plain targets.
        # Their expected outcomes remain valid when movement and defence rules change.
        _,s=paired(a,b,{'cmd':'new','units':[
            dict(id=1,owner=1,kind='bolt',x=8,y=0),
            dict(id=2,owner=2,kind='lancer',x=7,y=0)]})
    if s['phase']!='planning' or s['ended']:return
    # Isolate one queried action: others hold, including those with stored attacks.
    for u in s['units']:paired(a,b,order(u['owner'],u['id'],{'type':'hold'}))
    u=rng.choice(s['units']);p,i=u['owner'],u['id']
    if rng.random()<.55:
        r,_=paired(a,b,dict(cmd='reachable',player=p,unit=i))
        assert r['ok'] and r['cells']==sorted(r['cells'],key=lambda c:(c[1],c[0]))
        assert len({tuple(c) for c in r['cells']})==len(r['cells'])
        to=rng.choice(r['cells']) if r['cells'] and rng.random()<.7 else [rng.randrange(9),rng.randrange(9)]
        accepted=to in r['cells'];reply,_=paired(a,b,order(p,i,dict(type='move',to=to)))
        assert reply==({'ok':True} if accepted else dict(ok=False,error='invalid_order'))
        if accepted:
            occupied=any([v['x'],v['y']]==to for v in s['units'])
            for player in [1,2]:_,after=paired(a,b,dict(cmd='end_turn',player=player))
            v=next(v for v in after['units'] if v['id']==i)
            assert [v['x'],v['y']]==([u['x'],u['y']] if occupied else to)
            assert [(v['id'],v['hp']) for v in after['units']]==[(v['id'],v['hp']) for v in s['units']]
    else:
        targets=[v for v in s['units'] if step>=5 or MAP[v['y']][v['x']]!='s']
        target=rng.choice(targets)['id'] if targets and rng.random()<.9 else 99
        r,_=paired(a,b,dict(cmd='forecast',player=p,unit=i,target=target))
        got,_=paired(a,b,order(p,i,dict(type='attack',target=target)))
        assert got==({'ok':True} if r['ok'] else r)
        if r['ok']:
            v=next(v for v in s['units'] if v['id']==target)
            assert type(r['amount']) is int and r['amount']>=0
            expected=v['hp']+(r['amount'] if r['effect']=='repair' else -r['amount'])
            for player in [1,2]:_,after=paired(a,b,dict(cmd='end_turn',player=player))
            survivors=[v for v in after['units'] if v['id']==target]
            assert (survivors[0]['hp'] if survivors else 0)==max(0,expected)

def deployment(rng,step):
    kinds=['lancer','bolt','glider']+(['mender'] if step>=4 else [])
    cells=[(x,y) for y in range(9) for x in range(9) if MAP[y][x]!='#']
    rng.shuffle(cells)
    return {'cmd':'new','units':[dict(id=i+1,owner=1+i%2,kind=rng.choice(kinds),x=cells[i][0],y=cells[i][1]) for i in range(rng.randrange(2,9))]}

def fuzz(a,b,step,count=2000):
    rng=random.Random(0xA591000+step)
    paired(a,b,{'cmd':'new'})
    invalids=['','{','[]','null','true','42','{}','{"cmd":3}',
              {'cmd':'not_a_command'},{'cmd':'state','extra':0},
              {'cmd':'end_turn','player':True},{'cmd':'end_turn','player':0},
              {'cmd':'new','units':[]},{'cmd':'new','units':None},
              {'cmd':'reachable','player':1,'unit':1.0},
              order(1,1,{'type':'move','to':[0,True]}),
              order(1,1,{'type':'attack','target':100}),
              order(1,1,{'type':'hold','extra':0}),
              order(1,1,{'type':'unknown'}),
              '{"cmd":"forecast","player":1e0,"unit":1,"target":2}']
    if step>=3:invalids += [{'cmd':'view','player':3},{'cmd':'view','player':None}]
    if step>=4:invalids += [{'cmd':'new','units':[dict(id=1,owner=1,kind='mender',x=3,y=2),dict(id=2,owner=2,kind='bolt',x=8,y=8)]}]
    if step>=6:invalids += [{'cmd':'import','document':None},{'cmd':'import','document':{}},{'cmd':'export','extra':0}]
    successes=failures=0
    for index in range(count):
        s=a.state();invariants(s);roll=rng.random();p=rng.choice([1,2])
        own=[u for u in s['units'] if u['owner']==p]
        unit=rng.choice(own)['id'] if own and rng.random()<.8 else rng.randrange(1,100)
        if roll<.25:
            c=rng.choice(invalids)
            if step>=6 and rng.random()<.4:
                d=deepcopy(s)
                if rng.random()<.5:d['ended']=[1,2]
                elif d['units']:d['units'][-1]['x']=9
                else:d['turn']=-1
                c=dict(cmd='import',document=d)
        elif roll<.38:c=deployment(rng,step)
        elif roll<.58:
            o=rng.choice([{'type':'hold'},{'type':'move','to':[rng.randrange(9),rng.randrange(9)]},
                          {'type':'attack','target':rng.choice(s['units'])['id'] if s['units'] else 99}])
            c=order(p,unit,o)
        elif roll<.73:c=dict(cmd='end_turn',player=p)
        elif roll<.82:c=dict(cmd='reachable',player=p,unit=unit)
        elif roll<.90:c=dict(cmd='forecast',player=p,unit=unit,target=rng.choice(s['units'])['id'] if s['units'] else 99)
        elif roll<.95 and step>=3:c=dict(cmd='view',player=p)
        elif step>=6 and roll<.98:
            r,_=paired(a,b,{'cmd':'export'});c=dict(cmd='import',document=r['document'])
        else:c={'cmd':'state'}
        r,after=paired(a,b,c)
        if step>=3:no_leak(c,r,s)
        if r['ok']:successes+=1
        else:failures+=1
        if isinstance(c,dict) and c.get('cmd')=='view' and r['ok']:check_view(r,after,p)
        if index%17==0:query_outcome(a,b,after,rng,step)
        after=a.state()
        if step>=3 and index%19==0 and after['phase']=='planning':
            cells=visible(after,p);hidden=[v for v in after['units'] if v['owner']!=p and [v['x'],v['y']] not in cells]
            own=[v for v in after['units'] if v['owner']==p]
            if own and hidden:
                # A hidden target is indistinguishable from a genuinely absent ID.
                absent=next(i for i in range(1,100) if all(v['id']!=i for v in after['units']))
                for target in [hidden[0]['id'],absent]:
                    r,_=paired(a,b,dict(cmd='forecast',player=p,unit=own[0]['id'],target=target))
                    assert r==dict(ok=False,error='unavailable')
    assert successes>=100 and failures>=100
    for p in [1,2]:paired(a,b,dict(cmd='end_turn',player=p))
    a.finish();b.finish()
