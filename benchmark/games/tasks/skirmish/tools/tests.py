"""Generate the small per-step entry files; shared checks remain ordinary pytest helpers."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COMMON='''from copy import deepcopy
import pytest
from checks import exact_scenarios, fuzz, paired, refusal, order, visible, check_view

def test_committed_literal_scenarios(game):
    exact_scenarios(game, STEP)

def test_seeded_fuzz_at_least_2000_commands(game_factory):
    fuzz(game_factory(), game_factory(), STEP)

'''

F1='''
def invalid_requests():
    bad=[('', 'bad_json'), ('{', 'bad_json'), ('{} {}', 'bad_json')]
    for v in ['[]','null','true','1','{}','{"cmd":null}','{"cmd":false}']:
        bad.append((v,'bad_request'))
    bad.append(({'cmd':'unknown','extra':0},'unknown_command'))
    templates=[{'cmd':'state'},{'cmd':'new'},{'cmd':'end_turn','player':1},
               {'cmd':'reachable','player':1,'unit':1},
               {'cmd':'forecast','player':1,'unit':1,'target':2},
               order(1,1,{'type':'hold'})]
    for c in templates:
        bad.append((dict(c,extra=0),'bad_request'))
        for k in c:
            d=deepcopy(c);del d[k];bad.append((d,'bad_request'))
        for k in ['player','unit','target']:
            if k in c:
                for n in [None,True,1.0,'1',[],{},0,-1,100 if k!='player' else 3]:
                    d=deepcopy(c);d[k]=n;bad.append((d,'bad_request'))
    for o in [None,{},[],{'type':'HOLD'},{'type':True},{'type':'hold','to':[0,0]},
              {'type':'move'},{'type':'move','to':[0]},{'type':'move','to':[0,0,0]},
              {'type':'move','to':[0,False]},{'type':'move','to':[0,1.0]},
              {'type':'move','to':[-1,0]},{'type':'move','to':[9,0]},
              {'type':'attack'},{'type':'attack','target':True},
              {'type':'attack','target':0},{'type':'attack','target':100}]:
        bad.append((order(1,1,o),'bad_request'))
    u=[dict(id=1,owner=1,kind='bolt',x=0,y=0),dict(id=2,owner=2,kind='lancer',x=1,y=0)]
    for units in [None,[],u[:1],u*11,[None]+u,u+[deepcopy(u[0])]]:
        bad.append(({'cmd':'new','units':units},'bad_request'))
    for field,values in [('id',[0,100,True,1.0]),('owner',[0,3,False]),
                         ('kind',['phantom',None,True]),('x',[-1,9,False]),('y',[-1,9,1.0])]:
        for v in values:
            us=deepcopy(u);us[0][field]=v;bad.append(({'cmd':'new','units':us},'bad_request'))
    for k in u[0]:
        us=deepcopy(u);del us[0][k];bad.append(({'cmd':'new','units':us},'bad_request'))
    us=deepcopy(u);us[0]['extra']=0;bad.append(({'cmd':'new','units':us},'bad_request'))
    us=deepcopy(u);us[0].update(kind='lancer',x=3,y=2);bad.append(({'cmd':'new','units':us},'bad_request'))
    us=deepcopy(u);us[1]['owner']=1;bad.append(({'cmd':'new','units':us},'bad_request'))
    us=deepcopy(u);us[1].update(x=0,y=0);bad.append(({'cmd':'new','units':us},'bad_request'))
    bad.append(('{"cmd":"end_turn","player":1e0}','bad_request'))
    return bad

@pytest.mark.parametrize('command,error',invalid_requests())
def test_shape_refusals_preserve_the_next_turn(game_factory,command,error):
    a,b=game_factory(),game_factory()
    paired(a,b,{'cmd':'new'})
    paired(a,b,order(1,1,{'type':'move','to':[2,0]}))
    paired(a,b,{'cmd':'end_turn','player':1})
    refusal(a,b,command,error)

def test_phase_and_order_error_precedence(game_factory):
    a,b=game_factory(),game_factory()
    for c in [order(1,1,{'type':'hold'}),{'cmd':'reachable','player':1,'unit':1},
              {'cmd':'forecast','player':1,'unit':1,'target':2}]:
        r,_=paired(a,b,c);assert r=={'ok':False,'error':'not_started'}
    paired(a,b,{'cmd':'new','units':[dict(id=1,owner=1,kind='bolt',x=0,y=0),
                                  dict(id=2,owner=2,kind='lancer',x=4,y=0)]})
    checks=[(order(1,2,{'type':'hold'}),'unavailable'),
            (order(1,99,{'type':'attack','target':98}),'unavailable'),
            (order(1,1,{'type':'attack','target':99}),'unavailable'),
            (order(1,1,{'type':'attack','target':1}),'invalid_order'),
            (order(1,1,{'type':'attack','target':2}),'invalid_order'),
            (order(1,1,{'type':'move','to':[0,0]}),'invalid_order'),
            (order(1,1,{'type':'move','to':[8,8]}),'invalid_order')]
    for c,e in checks:
        r,_=paired(a,b,c);assert r=={'ok':False,'error':e}
    paired(a,b,{'cmd':'end_turn','player':1})
    for c in [order(1,99,{'type':'hold'}),{'cmd':'end_turn','player':1}]:
        r,_=paired(a,b,c);assert r=={'ok':False,'error':'turn_ended'}
    r,_=paired(a,b,{'cmd':'reachable','player':1,'unit':1});assert r['ok']
    paired(a,b,{'cmd':'end_turn','player':2})
    a.finish();b.finish()
'''

F2='''
@pytest.mark.parametrize('kind,to,error', [('lancer',[6,1],'invalid_order'),
                                         ('glider',[7,2],'invalid_order')])
def test_cost_budget_and_non_glider_crag(game_factory,kind,to,error):
    a,b=game_factory(),game_factory()
    paired(a,b,{'cmd':'new','units':[dict(id=1,owner=1,kind=kind,x=5,y=1),
                                  dict(id=2,owner=2,kind='bolt',x=8,y=8)]})
    refusal(a,b,order(1,1,{'type':'move','to':to}),error)

def test_legal_crag_deployment_and_start_cost_zero(game):
    assert game.send({'cmd':'new','units':[dict(id=1,owner=1,kind='glider',x=6,y=1),
                                         dict(id=2,owner=2,kind='bolt',x=8,y=8)]})=={'ok':True}
    assert game.send(order(1,1,{'type':'move','to':[4,1]}))=={'ok':True}
    assert game.send({'cmd':'end_turn','player':1})=={'ok':True}
    assert game.send({'cmd':'end_turn','player':2})=={'ok':True}
    assert [game.state()['units'][0][k] for k in ['x','y']]==[4,1]
'''

F3='''
@pytest.mark.parametrize('command',[{'cmd':'view'}, {'cmd':'view','player':True},
                                  {'cmd':'view','player':1.0}, {'cmd':'view','player':3},
                                  {'cmd':'view','player':1,'extra':0}])
def test_view_shape_refusals(game_factory,command):
    a,b=game_factory(),game_factory();paired(a,b,{'cmd':'new'})
    refusal(a,b,command,'bad_request')

def test_player_commands_are_indistinguishable_with_hidden_enemies(game_factory):
    a,b=game_factory(),game_factory()
    # Move an unseen enemy between the queried destination and another unseen cell.
    for other in [[3,0],[4,0],[8,8]]:
        for g,pos in [(a,[3,0]),(b,other)]:
            assert g.send({'cmd':'new','units':[dict(id=1,owner=1,kind='glider',x=0,y=0),
                                             dict(id=2,owner=2,kind='bolt',x=pos[0],y=pos[1])]})=={'ok':True}
        commands=[{'cmd':'view','player':1},{'cmd':'reachable','player':1,'unit':1},
                  {'cmd':'forecast','player':1,'unit':1,'target':2},
                  order(1,1,{'type':'attack','target':2}),order(1,2,{'type':'hold'}),
                  order(1,1,{'type':'move','to':[3,0]}),{'cmd':'end_turn','player':1}]
        for c in commands:assert a.send(c)==b.send(c)

def test_finished_and_empty_sight(game):
    game.send({'cmd':'new','units':[dict(id=1,owner=1,kind='glider',x=8,y=0),
                                  dict(id=2,owner=2,kind='glider',x=7,y=0)]})
    for _ in range(3):
        for p,i,t in [(1,1,2),(2,2,1)]:game.send(order(p,i,{'type':'attack','target':t}))
        game.send({'cmd':'end_turn','player':1});game.send({'cmd':'end_turn','player':2})
    for p in [1,2]:check_view(game.send({'cmd':'view','player':p}),game.state(),p)
'''

F4='''
def test_mender_sides_ranges_and_terrain(game_factory):
    a,b=game_factory(),game_factory()
    paired(a,b,{'cmd':'new','units':[dict(id=1,owner=1,kind='mender',x=0,y=0),
                                  dict(id=3,owner=1,kind='bolt',x=2,y=0),
                                  dict(id=2,owner=2,kind='bolt',x=1,y=0)]})
    for c in [order(1,1,{'type':'attack','target':1}),order(1,1,{'type':'attack','target':2}),
              order(1,1,{'type':'attack','target':3})]:
        r,_=paired(a,b,c);assert r=={'ok':False,'error':'invalid_order'}
    us=[dict(id=1,owner=1,kind='mender',x=3,y=2),dict(id=2,owner=2,kind='bolt',x=8,y=8)]
    refusal(a,b,{'cmd':'new','units':us},'bad_request')

def test_stacked_repairs_cap_once_and_doomed_mender_repairs(game):
    us=[dict(id=1,owner=1,kind='mender',x=0,y=0),dict(id=3,owner=1,kind='bolt',x=1,y=0),
        dict(id=4,owner=1,kind='mender',x=1,y=1),dict(id=2,owner=2,kind='bolt',x=2,y=0)]
    assert game.send({'cmd':'new','units':us})=={'ok':True}
    for _ in range(2):
        game.send(order(2,2,{'type':'attack','target':3}));game.send({'cmd':'end_turn','player':1});game.send({'cmd':'end_turn','player':2})
    assert next(u for u in game.state()['units'] if u['id']==3)['hp']==2
    for i in [1,4]:assert game.send(order(1,i,{'type':'attack','target':3}))=={'ok':True}
    game.send({'cmd':'end_turn','player':1});game.send({'cmd':'end_turn','player':2})
    assert next(u for u in game.state()['units'] if u['id']==3)['hp']==6
    # Reduce the first mender to 1 hp, then it repairs on its death turn.
    for _ in range(3):
        game.send(order(2,2,{'type':'attack','target':1}));game.send({'cmd':'end_turn','player':1});game.send({'cmd':'end_turn','player':2})
    assert game.state()['units'][0]['hp']==1
    game.send(order(2,2,{'type':'attack','target':3}));game.send({'cmd':'end_turn','player':1});game.send({'cmd':'end_turn','player':2})
    game.send(order(1,1,{'type':'attack','target':3}));game.send(order(2,2,{'type':'attack','target':1}))
    game.send({'cmd':'end_turn','player':1});game.send({'cmd':'end_turn','player':2})
    assert all(u['id']!=1 for u in game.state()['units'])
    assert next(u for u in game.state()['units'] if u['id']==3)['hp']==6
'''

F5='''
def test_queries_refuse_bad_combat_requests_atomically(game_factory):
    a,b=game_factory(),game_factory();paired(a,b,{'cmd':'new'})
    for c in [{'cmd':'forecast','player':1,'unit':1,'target':None},
              {'cmd':'forecast','player':1,'unit':1,'target':1.0},
              {'cmd':'forecast','player':1,'unit':1,'target':True}]:
        r,_=paired(a,b,c);assert r=={'ok':False,'error':'bad_request'}
    refusal(a,b,order(1,1,{'type':'attack','target':99}),'unavailable')

def test_repair_ignores_shelter(game):
    assert game.send({'cmd':'new','units':[dict(id=1,owner=1,kind='mender',x=1,y=1),
                                         dict(id=3,owner=1,kind='bolt',x=2,y=1),
                                         dict(id=2,owner=2,kind='lancer',x=2,y=0)]})=={'ok':True}
    game.send(order(2,2,{'type':'attack','target':3}));game.send({'cmd':'end_turn','player':1});game.send({'cmd':'end_turn','player':2})
    assert game.send({'cmd':'forecast','player':1,'unit':1,'target':3})=={'ok':True,'effect':'repair','amount':1}
    game.send(order(1,1,{'type':'attack','target':3}));game.send({'cmd':'end_turn','player':1});game.send({'cmd':'end_turn','player':2})
    assert next(u for u in game.state()['units'] if u['id']==3)['hp']==6
'''

F6='''
def base_document():
    return {'turn':3,'phase':'planning','winner':None,'ended':[1],
            'units':[dict(id=1,owner=1,kind='mender',x=0,y=0,hp=7,order={'type':'attack','target':3}),
                     dict(id=2,owner=2,kind='bolt',x=2,y=0,hp=6,order=None),
                     dict(id=3,owner=1,kind='lancer',x=1,y=0,hp=4,order={'type':'hold'})]}

def invalid_documents():
    d=base_document();bad=[None,[],True,1,{},dict(d,extra=0)]
    for k in d:
        x=deepcopy(d);del x[k];bad.append(x)
    for k,vs in [('turn',[-1,2147483648,True,1.0,'3',0]),('phase',['other',None,True]),
                 ('winner',[False,3,1]),('ended',[None,[1,2],[1,1],[0],[True],[1.0]]),
                 ('units',[None,{},[None]])]:
        for v in vs:x=deepcopy(d);x[k]=v;bad.append(x)
    for k,vs in [('id',[0,100,True,1.0]),('owner',[0,3,False]),('kind',['phantom',None]),
                 ('x',[-1,9,True,1.0,None]),('y',[-1,9,False,None]),('hp',[0,8,True,1.0]),
                 ('order',[{},[],{'type':'hold','extra':0},{'type':'attack','target':99},
                           {'type':'attack','target':2},{'type':'attack','target':1},
                           {'type':'move','to':[8,8]},{'type':'move','to':[1,0]},
                           {'type':'attack','target':3.0}])]:
        for v in vs:x=deepcopy(d);x['units'][0][k]=v;bad.append(x)
    for k in d['units'][0]:
        x=deepcopy(d);del x['units'][0][k];bad.append(x)
    x=deepcopy(d);x['units'][1].update(x=0,y=0);bad.append(x) # Single intended f6 miss.
    x=deepcopy(d);x['units'][1]['id']=1;bad.append(x)
    x=deepcopy(d);x['units']=x['units'][::-1];bad.append(x)
    x=deepcopy(d);x['units'][1].update(x=3,y=2);bad.append(x)
    x=deepcopy(d);x['units'][0]['extra']=0;bad.append(x)
    for p in ['idle','finished']:
        x=deepcopy(d);x['phase']=p;bad.append(x)
    x=deepcopy(d);x['units'][1]['owner']=1;bad.append(x)
    x=deepcopy(d);x['units'][2]['kind']='phantom';bad.append(x)
    x=deepcopy(d);x['units'][2]['x']=99;bad.append(x) # A late bad target must not crash.
    x=deepcopy(d);x['units']*=7;bad.append(x)
    return bad

@pytest.mark.parametrize('document',invalid_documents())
def test_bad_document_preserves_half_ended_future(game_factory,document):
    a,b=game_factory(),game_factory()
    paired(a,b,{'cmd':'new'})
    paired(a,b,order(1,1,{'type':'move','to':[2,0]}));paired(a,b,{'cmd':'end_turn','player':1})
    refusal(a,b,{'cmd':'import','document':document},'bad_document')

@pytest.mark.parametrize('c',[{'cmd':'import'},{'cmd':'import','document':None,'extra':0},
                             {'cmd':'export','extra':0}])
def test_document_command_shapes(game_factory,c):
    a,b=game_factory(),game_factory();paired(a,b,{'cmd':'new'});refusal(a,b,c,'bad_request')

def test_roundtrip_continuation_all_phases(game_factory):
    a,b=game_factory(),game_factory()
    docs=[{'turn':0,'phase':'idle','winner':None,'ended':[],'units':[]},base_document(),
          {'turn':9,'phase':'finished','winner':1,'ended':[],
           'units':[dict(id=7,owner=1,kind='mender',x=0,y=0,hp=1,order=None)]},
          {'turn':4,'phase':'finished','winner':0,'ended':[],'units':[]},
          {'turn':2,'phase':'planning','winner':None,'ended':[2],
           'units':[dict(id=1,owner=1,kind='glider',x=6,y=1,hp=5,order={'type':'move','to':[5,1]}),
                    dict(id=2,owner=2,kind='bolt',x=8,y=8,hp=6,order=None)]}]
    for d in docs:
        paired(a,b,{'cmd':'import','document':d})
        out,_=paired(a,b,{'cmd':'export'});assert out=={'ok':True,'document':d}
        assert a.send({'cmd':'new'})=={'ok':True}
        assert a.send({'cmd':'import','document':out['document']})=={'ok':True}
        assert a.state()==b.state()
        for c in [order(2,2,{'type':'attack','target':3}),{'cmd':'end_turn','player':2},
                  {'cmd':'view','player':1},{'cmd':'end_turn','player':1}]:paired(a,b,c)

def test_turn_limit_and_finished_document_consistency(game_factory):
    a,b=game_factory(),game_factory();d=base_document();d['turn']=2147483647
    paired(a,b,{'cmd':'import','document':d})
    refusal(a,b,{'cmd':'end_turn','player':2},'bad_request')
    for d in [dict(turn=1,phase='finished',winner=0,ended=[],units=[]),
              dict(turn=2,phase='finished',winner=1,ended=[],units=[]),
              dict(turn=0,phase='idle',winner=None,ended=[1],units=[])]:
        refusal(a,b,{'cmd':'import','document':d},'bad_document')
'''

def main():
    for step,body in enumerate([F1,F2,F3,F4,F5,F6],1):
        (ROOT/'hidden'/f'test_f{step}.py').write_text(COMMON.replace('STEP',str(step))+body)
if __name__=='__main__':main()
