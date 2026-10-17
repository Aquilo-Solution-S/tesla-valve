import pytest
from checks import exact_scenarios, fuzz, refusal


def test_scripted_exact_snapshots(game):
    exact_scenarios(game,2)


@pytest.mark.parametrize('command',[
    {'cmd':'pause','extra':0},{'cmd':'resume','extra':0},
    {'cmd':'pause','ms':1},{'cmd':'resume','key':'left'},
])
def test_pause_request_validation(game,command):
    game.send({'cmd':'new','seed':742})
    refusal(game,command,'bad_request')


def test_pause_errors_and_validation_precedence(game):
    refusal(game,{'cmd':'pause'},'not_started')
    refusal(game,{'cmd':'resume'},'not_started')
    game.send({'cmd':'new','seed':742})
    assert game.send({'cmd':'pause'})=={'ok':True}
    for c in [{'cmd':'tick','ms':0},{'cmd':'input','key':'hard'}]: refusal(game,c,'paused')
    refusal(game,{'cmd':'tick','ms':-1},'bad_request')
    refusal(game,{'cmd':'input','key':'other'},'bad_request')
    assert game.send({'cmd':'new','seed':742})=={'ok':True}
    assert game.state()['phase']=='playing'


def test_seeded_fuzz_2000(game):
    fuzz(game,2)
