"""Author committed protocol scenarios from an independent rule model."""
import json
from copy import deepcopy
from pathlib import Path
from hidden.model import Model

ROOT=Path(__file__).resolve().parent

def inp(key): return {'cmd':'input','key':key}
def tick(ms): return {'cmd':'tick','ms':ms}

def reply(model,c):
    phase=model.phase
    if c['cmd'] in ('input','tick'):
        error = {'idle':'not_started','paused':'paused','over':'finished','won':'finished'}.get(phase)
        if not error and c.get('key')=='hold' and not model.available: error='hold_used'
        if error: return {'ok':False,'error':error}
    if c['cmd'] in ('pause','resume') and phase in ('idle','over','won'):
        return {'ok':False,'error':'not_started' if phase=='idle' else 'finished'}
    return {'ok':True}


def scenario(step,name,commands):
    m=Model(step)
    events=[]
    for c in commands:
        r=reply(m,c)
        if r['ok']: m.command(c)
        events.append({'command':c,'reply':r,'state':m.snapshot()})
    return {'name':name,'events':events}


def safe(seed,count=90):
    m=Model(4); m.rng=seed or 2463534242
    return all(m.draw()!=5 for _ in range(count))


def placements(m):
    choices=[]
    for rotation in range(4):
        for x in range(10):
            g=deepcopy(m); commands=[]
            for _ in range(rotation): g.input('rotate'); commands.append(inp('rotate'))
            delta=x-g.active[2]
            key='right' if delta>=0 else 'left'
            for _ in range(abs(delta)): g.input(key); commands.append(inp(key))
            if g.active[2]!=x: continue
            before=g.lines
            g.input('hard'); commands.append(inp('hard'))
            if g.phase=='over': continue
            heights=[]; holes=0
            for a in range(10):
                ys=[b for xx,b in g.board if xx==a]
                h=18-min(ys) if ys else 0
                heights.append(h)
                if ys: holes+=sum((a,b) not in g.board for b in range(min(ys),18))
            cost=.55*sum(heights)+4*holes+.4*sum(abs(a-b) for a,b in zip(heights,heights[1:]))+.5*max(heights)-8*(g.lines-before)
            choices.append((cost,commands,g))
    return choices


def solve(step,seed,target=4,limit=70,mode='endless'):
    m=Model(step); m.new(seed,mode)
    commands=[{'cmd':'new','seed':seed,**({'mode':mode} if step>=5 else {})}]
    for _ in range(limit):
        choices=placements(m)
        if not choices: return None
        _, moves, m=min(choices,key=lambda c:c[0])
        if step>=5: commands.append(tick(7))
        commands.extend(moves)
        if m.lines>=target: return commands
    return None


def main():
    cases={k:[] for k in range(1,7)}
    seed=next(s for s in range(1,10000) if safe(s))
    # The same sequence remains a base-game sequence when pulse is introduced.
    for s in range(seed,20000):
        if not safe(s): continue
        clear=solve(1,s)
        if clear:
            seed=s; break
    else: raise RuntimeError('no row-clear scenario')
    (ROOT/'hidden/clear_commands.json').write_text(json.dumps(clear,indent=2)+'\n')
    multiple=json.loads((ROOT/'hidden/multiple_commands.json').read_text())
    cases[1].append(scenario(1,'simultaneous three-row clear and higher-level scoring',multiple))
    for kind in range(5):
        s=next(s for s in range(1,1000) if safe(s,5) and base_first(s)==kind)
        commands=[{'cmd':'new','seed':s}]+[inp('rotate') for _ in range(4)]+[inp('soft'),inp('hard')]
        cases[1].append(scenario(1,f'four rotations return kind {kind} to initial orientation',commands))
    soft_seed=next(s for s in range(1,1000) if safe(s,5) and base_first(s)==0)
    cases[1].append(scenario(1,'soft landing locks without a drop point',[{'cmd':'new','seed':soft_seed}]+[inp('soft') for _ in range(17)]))
    cases[1].append(scenario(1,'four rows and a level increase',clear+[tick(554),tick(1)]))
    cases[1].append(scenario(1,'movement rotation drop and accumulator',[
        {'cmd':'new','seed':seed},inp('left'),inp('rotate'),inp('right'),tick(599),tick(1),inp('soft'),inp('hard'),tick(1000000),tick(599),tick(1)]))
    cases[1].append(scenario(1,'blocked spawn and finished commands',[
        {'cmd':'new','seed':seed}]+[inp('hard') for _ in range(12)]+[tick(1),inp('left')]))
    cases[1].append(scenario(1,'blocked rotation at right edge',[
        {'cmd':'new','seed':0},inp('rotate')]+[inp('right') for _ in range(10)]+[inp('rotate') for _ in range(4)]+[inp('hard')]))
    reed_seed=next(s for s in range(1,1000) if safe(s,5) and base_first(s)==4)
    cases[1].append(scenario(1,'four-wide rotation blocked at wall',[{'cmd':'new','seed':reed_seed}]+[inp('right') for _ in range(4)]+[inp('rotate'),inp('left'),inp('left'),inp('rotate'),inp('hard')]))
    # Explicit seed-zero and upper-bound first draws, which are unchanged by pulse.
    for s in [0,4294967295]:
        if ModelFirst(s)!=5:
            cases[1].append(scenario(1,f'seed {s}',[{'cmd':'new','seed':s}]))
    cases[2].append(scenario(2,'pause preserves partial gravity and refuses play',[
        {'cmd':'pause'},{'cmd':'resume'},{'cmd':'new','seed':seed},tick(599),{'cmd':'pause'},
        {'cmd':'pause'},tick(1000000),inp('left'),{'cmd':'resume'},{'cmd':'resume'},tick(1),inp('hard')]))
    cases[2].append(scenario(2,'finished pause and resume',[
        {'cmd':'new','seed':seed}]+[inp('hard') for _ in range(12)]+[{'cmd':'pause'},{'cmd':'resume'}]))
    cases[3].append(scenario(3,'empty hold then occupied hold with fresh orientation',[
        {'cmd':'new','seed':seed},tick(599),inp('rotate'),inp('left'),inp('hold'),inp('hold'),tick(1),
        inp('hard'),inp('rotate'),inp('right'),inp('hold'),inp('hold'),inp('hard')]))
    cases[3].append(scenario(3,'hold while paused and after finish',[
        {'cmd':'new','seed':seed},{'cmd':'pause'},inp('hold'),{'cmd':'resume'},inp('hold')]+
        [inp('hard') for _ in range(15)]+[inp('hold')]))
    pulse_seed=next(s for s in range(1,1000) if ModelFirst(s)==5)
    m=Model(4)
    second_seed=None
    for s in range(1,1000):
        m.rng=s
        if m.draw()!=5 and m.draw()==5:
            second_seed=s; break
    cases[4].append(scenario(4,'pulse survives storage and retrieval',[
        {'cmd':'new','seed':pulse_seed},inp('rotate'),inp('hold'),inp('left'),inp('hard'),inp('hold'),inp('rotate'),inp('hard')]))
    cases[4].append(scenario(4,'pulse erases occupied cells',[
        {'cmd':'new','seed':second_seed},inp('hard'),inp('hard')]))
    cases[4].append(scenario(4,'pulse clipped at edges',[
        {'cmd':'new','seed':pulse_seed}]+[inp('left') for _ in range(7)]+[inp('rotate'),inp('hard')]))
    rush=None
    for s in range(1,100):
        rush=solve(5,s,mode='rush')
        if rush: break
    assert rush
    (ROOT/'hidden/rush_commands.json').write_text(json.dumps(rush,indent=2)+'\n')
    cases[5].append(scenario(5,'rush wins and refuses further play',rush+[tick(999),inp('hold'),{'cmd':'pause'},{'cmd':'resume'}]))
    endless=deepcopy(rush); endless[0]['mode']='endless'
    cases[5].append(scenario(5,'endless continues past four rows',endless+[tick(555)]))
    cases[5].append(scenario(5,'whole tick and paused time',[
        {'cmd':'new','seed':seed,'mode':'rush'},tick(599),{'cmd':'pause'},tick(50),{'cmd':'resume'},tick(1),inp('hard'),tick(1000000),{'cmd':'new','seed':seed}]))
    doc=dict(seed=pulse_seed,mode='endless',events=[
        dict(at_ms=100,key='hold'),dict(at_ms=100,key='hold'),dict(at_ms=600,key='hard'),
        dict(at_ms=600,key='pause'),dict(at_ms=700,key='left'),dict(at_ms=900,key='resume'),
        dict(at_ms=1000,key='hold'),dict(at_ms=1200,key='hard')],end_ms=1800)
    cases[6].append(scenario(6,'timed replay with equal times pauses and refusals',[
        {'cmd':'new','seed':seed},inp('hard'),{'cmd':'replay','document':doc}]))
    events=[]; at=0
    for command in rush[1:]:
        if command['cmd']=='tick': at+=command['ms']
        else: events.append(dict(at_ms=at,key=command['key']))
    events += [dict(at_ms=at,key='hold'),dict(at_ms=at+1,key='pause')]
    won_document=dict(seed=rush[0]['seed'],mode='rush',events=events,end_ms=at+100)
    cases[6].append(scenario(6,'replay wins and ignores finished actions',[{'cmd':'new','seed':15},{'cmd':'pause'},{'cmd':'replay','document':won_document}]))
    cases[6].append(scenario(6,'empty replay and zero endpoint',[
        {'cmd':'replay','document':dict(seed=0,mode='rush',events=[],end_ms=0)}]))
    for k,values in cases.items():
        (ROOT/f'hidden/scenarios_f{k}.json').write_text(json.dumps(values,indent=2)+'\n')
    print(f'goldens: base seed={seed}; pulse seed={pulse_seed}; clear inputs={len(clear)}; rush inputs={len(rush)}')


def base_first(seed):
    m=Model(1); m.rng=seed or 2463534242
    return m.draw()


def ModelFirst(seed):
    m=Model(4); m.rng=seed or 2463534242
    return m.draw()

if __name__=='__main__': main()
