from copy import deepcopy
import pytest
from checks import exact_scenarios, fuzz, paired, refusal, order, visible, check_view

def test_committed_literal_scenarios(game):
    exact_scenarios(game, 3)

def test_seeded_fuzz_at_least_2000_commands(game_factory):
    fuzz(game_factory(), game_factory(), 3)


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
