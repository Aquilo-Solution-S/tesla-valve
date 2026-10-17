import json

import pytest
from checks import exact_scenarios, fuzz, refusal


def test_scripted_exact_snapshots(game):
    exact_scenarios(game,1)


@pytest.mark.parametrize('command,error',[
    ('','bad_json'),('{','bad_json'),('{"cmd":"state"} false','bad_json'),
    ('{"cmd":"new","seed":NaN}','bad_json'),([], 'bad_request'),(None,'bad_request'),
    ({},'bad_request'),({'cmd':False},'bad_request'),({'cmd':'unknown'},'unknown_command'),
    ({'cmd':'new'},'bad_request'),({'cmd':'new','seed':-1},'bad_request'),
    ({'cmd':'new','seed':4294967296},'bad_request'),({'cmd':'new','seed':True},'bad_request'),
    ('{"cmd":"new","seed":1.0}','bad_request'),('{"cmd":"new","seed":1e0}','bad_request'),
    ({'cmd':'new','seed':'42'},'bad_request'),({'cmd':'tick','ms':-1},'bad_request'),
    ({'cmd':'tick','ms':1000001},'bad_request'),({'cmd':'tick','ms':None},'bad_request'),
    ({'cmd':'input','key':'LEFT'},'bad_request'),({'cmd':'input'},'bad_request'),
    ({'cmd':'state','extra':0},'bad_request'),
])
def test_malformed_lines_are_atomic(game,game_factory,command,error):
    control=game_factory()
    for g in [game,control]:
        g.send({'cmd':'new','seed':742})
        g.send({'cmd':'tick','ms':599})
    refusal(game,command,error)
    future=[{'cmd':'tick','ms':1}]+[{'cmd':'input','key':'hard'}]*6
    for c in future:
        assert game.send(c)==control.send(c)
        assert game.state()==control.state()


def test_unstarted_and_finished(game):
    refusal(game,{'cmd':'tick','ms':0},'not_started')
    refusal(game,{'cmd':'input','key':'hard'},'not_started')
    game.send({'cmd':'new','seed':742})
    for _ in range(40):
        if game.state()['phase']=='over': break
        game.send({'cmd':'input','key':'hard'})
    assert game.state()['phase']=='over'
    refusal(game,{'cmd':'tick','ms':0},'finished')
    refusal(game,{'cmd':'input','key':'rotate'},'finished')
    assert game.send({'cmd':'new','seed':42})=={'ok':True}
    assert game.state()['score']==0


def test_eof_final_line_and_no_extra_stdout(game):
    game.proc.stdin.write(b'{"cmd":"new","seed":742}\n{"cmd":"state"}')
    game.proc.stdin.close()
    game.proc.stdin=None
    out,_=game.proc.communicate(timeout=3)
    replies=[json.loads(line) for line in out.splitlines()]
    assert len(replies)==2 and replies[0]=={'ok':True} and replies[1]['ok'] is True
    assert replies[1]['state']['phase']=='playing'
    assert game.proc.returncode==0


def test_seeded_fuzz_2000(game):
    fuzz(game,1)


def test_seed_bounds_duplicate_members_and_zero_tick(game):
    for seed in [0,4294967295]:
        assert game.send({'cmd':'new','seed':seed})=={'ok':True}
        before=game.state()
        assert before['phase']=='playing' and before['score']==0
        assert game.send({'cmd':'tick','ms':0})=={'ok':True}
        assert game.state()==before
    game.send('{"cmd":"new","seed":1,"seed":742}')
    duplicate=game.state()
    game.send({'cmd':'new','seed':742})
    assert game.state()==duplicate
