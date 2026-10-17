from copy import deepcopy
import random

import pytest
from checks import exact_scenarios, fuzz, live, replay, refusal


def test_scripted_exact_snapshots(game):
    exact_scenarios(game,6)


def invalid_documents():
    d=replay()['document']
    bad=[None,[],42,{},True]
    for field in d:
        x=deepcopy(d); del x[field]; bad.append(x)
    for field,values in [('seed',[-1,4294967296,True,1.0,'1']),('mode',[None,'other',1]),
                         ('end_ms',[-1,1000001,False,1.0]),('events',[None,{},'events',[None],[]])]:
        for value in values:
            x=deepcopy(d); x[field]=value
            if field=='events' and value==[]: continue # This one is valid.
            bad.append(x)
    x=deepcopy(d); x['extra']=0; bad.append(x)
    for event in [{},{'at_ms':0},{'key':'hard'},{'at_ms':0,'key':'other'},
                  {'at_ms':-1,'key':'hard'},{'at_ms':1000001,'key':'hard'},
                  {'at_ms':True,'key':'hard'},{'at_ms':1.0,'key':'hard'},
                  {'at_ms':0,'key':None},{'at_ms':0,'key':1},
                  {'at_ms':0,'key':'hard','extra':0}]:
        x=deepcopy(d); x['events']=[event]; bad.append(x)
    # Late invalid events ensure validation finishes before mutating any game.
    for event in [{'at_ms':599,'key':'left'},{'at_ms':600,'key':'other'},{'at_ms':1201,'key':'left'}]:
        x=deepcopy(d); x['events'].append(event); bad.append(x)
    x=deepcopy(d); x['events']=[{'at_ms':0,'key':'left'}]*4097; bad.append(x)
    return bad


@pytest.mark.parametrize('document',invalid_documents())
def test_invalid_replay_preserves_game_and_future(game_factory,document):
    a,b=game_factory(),game_factory()
    prefix=[{'cmd':'new','seed':742,'mode':'rush'},{'cmd':'tick','ms':599},{'cmd':'input','key':'hold'},
            {'cmd':'tick','ms':599},{'cmd':'pause'}]
    for c in prefix:
        assert a.send(c)==b.send(c)
    refusal(a,{'cmd':'replay','document':document},'bad_replay')
    for c in [{'cmd':'resume'},{'cmd':'tick','ms':1}]+[{'cmd':'input','key':'hard'}]*6:
        assert a.send(c)==b.send(c)
        assert a.state()==b.state() # Includes hidden credit and future random draws.


def test_top_level_replay_errors(game):
    game.send({'cmd':'new','seed':742})
    refusal(game,{'cmd':'replay'},'bad_request')
    refusal(game,dict(replay(),extra=0),'bad_request')
    refusal(game,'{"cmd":"replay","document":{"seed":1e0,"mode":"endless","events":[],"end_ms":0}}','bad_replay')


def test_replay_matches_live_and_future(game_factory):
    a,b=game_factory(),game_factory()
    rng=random.Random(6606)
    for trial in range(32):
        keys=['left','right','rotate','soft','hard','hold','pause','resume']
        times=sorted(rng.randrange(10000) for _ in range(50))
        doc=replay(seed=rng.randrange(2**32),mode='rush' if trial%2 else 'endless',
                   events=[{'at_ms':t,'key':rng.choice(keys)} for t in times],end_ms=10000)['document']
        expected=live(b,doc)
        assert a.send({'cmd':'replay','document':doc})=={'ok':True}
        assert a.state()==expected
        for c in [{'cmd':'resume'},{'cmd':'tick','ms':600},{'cmd':'input','key':'hard'},{'cmd':'input','key':'hold'}]:
            assert a.send(c)==b.send(c)
            assert a.state()==b.state()


def test_maximum_valid_event_count_and_time(game_factory):
    a,b=game_factory(),game_factory()
    doc=replay(events=[{'at_ms':0,'key':'rotate'}]*4096,end_ms=1000000)['document']
    expected=live(b,doc)
    assert a.send({'cmd':'replay','document':doc})=={'ok':True}
    assert a.state()==expected


def test_seeded_fuzz_2000(game):
    fuzz(game,6)
