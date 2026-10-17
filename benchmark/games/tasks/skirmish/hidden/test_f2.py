from copy import deepcopy
import pytest
from checks import exact_scenarios, fuzz, paired, refusal, order, visible, check_view

def test_committed_literal_scenarios(game):
    exact_scenarios(game, 2)

def test_seeded_fuzz_at_least_2000_commands(game_factory):
    fuzz(game_factory(), game_factory(), 2)


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
