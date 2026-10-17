from checks import exact_scenarios, fuzz, refusal


def test_scripted_exact_snapshots(game):
    exact_scenarios(game,4)


def test_pulse_is_a_kind_not_an_input(game):
    game.send({'cmd':'new','seed':15})
    assert game.state()['active']['kind']=='pulse'
    refusal(game,{'cmd':'input','key':'pulse'},'bad_request')
    refusal(game,{'cmd':'new','seed':15,'piece':'pulse'},'bad_request')
    refusal(game,{'cmd':'input','key':'rotate','direction':'clockwise'},'bad_request')


def test_preview_pulse_is_not_filtered(game):
    game.send({'cmd':'new','seed':14})
    # The exact seed is selected independently below; at least one of these
    # first four draws has the designated pulse residue.
    found=False
    for seed in range(1,50):
        game.send({'cmd':'new','seed':seed})
        s=game.state()
        if 'pulse' in s['preview']:
            index=s['preview'].index('pulse')
            for _ in range(index+1): game.send({'cmd':'input','key':'hard'})
            assert game.state()['active']['kind']=='pulse'
            found=True
            break
    assert found


def test_seeded_fuzz_2000(game):
    fuzz(game,4)
