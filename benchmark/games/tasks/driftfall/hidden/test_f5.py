import pytest
from checks import exact_scenarios, fuzz, refusal


def test_scripted_exact_snapshots(game):
    exact_scenarios(game,5)


@pytest.mark.parametrize('mode',[None,True,0,'Rush','sprint',{},[]])
def test_bad_mode_is_atomic(game,mode):
    game.send({'cmd':'new','seed':742,'mode':'rush'})
    game.send({'cmd':'tick','ms':599})
    refusal(game,{'cmd':'new','seed':42,'mode':mode},'bad_request')
    game.send({'cmd':'tick','ms':1})
    s=game.state()
    assert s['mode']=='rush' and s['elapsed_ms']==600 and s['active']['cells'][0][1]==1


def test_default_mode_and_idle_time(game):
    s=game.state()
    assert s['mode']=='endless' and s['elapsed_ms']==0
    refusal(game,{'cmd':'tick','ms':0},'not_started')
    game.send({'cmd':'new','seed':742,'mode':'rush'})
    game.send({'cmd':'tick','ms':1000000})
    assert game.state()['elapsed_ms']==1000000
    game.send({'cmd':'new','seed':742})
    assert game.state()['mode']=='endless' and game.state()['elapsed_ms']==0


def test_seeded_fuzz_2000(game):
    fuzz(game,5)
