from copy import deepcopy
import pytest
from checks import exact_scenarios, fuzz, paired, refusal, order, visible, check_view

def test_committed_literal_scenarios(game):
    exact_scenarios(game, 4)

def test_seeded_fuzz_at_least_2000_commands(game_factory):
    fuzz(game_factory(), game_factory(), 4)


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
