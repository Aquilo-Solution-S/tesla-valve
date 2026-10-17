from checks import exact_scenarios, fuzz, refusal


def test_scripted_exact_snapshots(game):
    exact_scenarios(game,3)


def test_hold_refusals_and_precise_members(game):
    refusal(game,{'cmd':'input','key':'hold'},'not_started')
    game.send({'cmd':'new','seed':742})
    assert game.send({'cmd':'input','key':'hold'})=={'ok':True}
    refusal(game,{'cmd':'input','key':'hold'},'hold_used')
    game.send({'cmd':'pause'})
    refusal(game,{'cmd':'input','key':'hold'},'paused')
    refusal(game,{'cmd':'input','key':'hold','extra':0},'bad_request')
    refusal(game,{'cmd':'input','key':['hold']},'bad_request')


def test_preview_and_generator_repeatability(game_factory):
    a,b=game_factory(),game_factory()
    for g in [a,b]: g.send({'cmd':'new','seed':742})
    for key in ['hold','hold','hard','hold','hard','hard']:
        assert a.send({'cmd':'input','key':key})==b.send({'cmd':'input','key':key})
        assert a.state()==b.state()


def test_seeded_fuzz_2000(game):
    fuzz(game,3)
