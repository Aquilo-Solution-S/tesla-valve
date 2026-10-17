from copy import deepcopy
import pytest
from checks import exact_scenarios, fuzz, paired, refusal, order, visible, check_view

def test_committed_literal_scenarios(game):
    exact_scenarios(game, 1)

def test_seeded_fuzz_at_least_2000_commands(game_factory):
    fuzz(game_factory(), game_factory(), 1)


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
