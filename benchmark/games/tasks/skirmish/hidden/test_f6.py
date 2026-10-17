from copy import deepcopy
import pytest
from checks import exact_scenarios, fuzz, paired, refusal, order, visible, check_view

def test_committed_literal_scenarios(game):
    exact_scenarios(game, 6)

def test_seeded_fuzz_at_least_2000_commands(game_factory):
    fuzz(game_factory(), game_factory(), 6)


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
