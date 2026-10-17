from copy import deepcopy
import pytest
from checks import exact_scenarios, fuzz, paired, refusal, order, visible, check_view

def test_committed_literal_scenarios(game):
    exact_scenarios(game, 5)

def test_seeded_fuzz_at_least_2000_commands(game_factory):
    fuzz(game_factory(), game_factory(), 5)


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
