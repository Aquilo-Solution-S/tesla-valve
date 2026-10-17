"""Independent, small executable reading of the observable rules for golden authoring.

Tests use committed literal goldens, not this model or the reference implementations.
"""
from copy import deepcopy

NAMES = ['sprig','prong','ramp','arch','reed','pulse']
SHAPES = [ [(0,0),(0,1),(1,1)], [(0,0),(1,0),(2,0),(1,1),(1,2)],
           [(0,0),(0,1),(1,1),(1,2),(2,2)], [(0,0),(2,0),(0,1),(1,1),(2,1)],
           [(0,0),(0,1),(0,2),(0,3),(1,3)], [(0,0),(0,1),(0,2)] ]

class Model:
    def __init__(self, step):
        self.step = step
        self.board = set()
        self.phase = 'idle'
        self.active = None
        self.score = self.lines = self.credit = self.elapsed = 0
        self.rng = 0
        self.held = None
        self.preview = []
        self.available = False
        self.mode = 'endless'

    def draw(self):
        self.rng ^= (self.rng << 13) & 0xffffffff
        self.rng ^= self.rng >> 17
        self.rng ^= (self.rng << 5) & 0xffffffff
        return 5 if self.step >= 4 and self.rng % 16 == 15 else self.rng % 5

    def spawn(self, kind):
        self.active = [kind, list(SHAPES[kind]), 4, 0]
        if not self.fits(self.active):
            self.active = None
            self.phase = 'over'
            self.available = False

    def take(self):
        if self.step < 3:
            return self.draw()
        kind = self.preview.pop(0)
        self.preview.append(self.draw())
        return kind

    def new(self, seed, mode='endless'):
        step = self.step
        self.__init__(step)
        self.phase, self.mode = 'playing', mode
        self.rng = seed or 2463534242
        kind = self.draw()
        if step >= 3:
            self.preview = [self.draw() for _ in range(3)]
            self.available = True
        self.spawn(kind)

    def cells(self, p):
        return {(x+p[2],y+p[3]) for x,y in p[1]}

    def fits(self, p):
        c = self.cells(p)
        return all(0<=x<10 and 0<=y<18 for x,y in c) and not c & self.board

    def move(self, dx=0, dy=0):
        p = deepcopy(self.active)
        p[2] += dx
        p[3] += dy
        if not self.fits(p): return False
        self.active = p
        return True

    def lock(self):
        kind, shape, x, y = self.active
        if kind == 5:
            erased = {(a,b) for a,b in self.board if x-1<=a<=x+1 and y+1<=b<=y+3}
            self.board -= erased
            self.score += 11 + 3*len(erased)
        else:
            self.board |= self.cells(self.active)
            self.score += 7
        full = [b for b in range(18) if all((a,b) in self.board for a in range(10))]
        self.board = {(a,b+sum(c>b for c in full)) for a,b in self.board if b not in full}
        self.score += 80*len(full)**2*(1+self.lines//4)
        self.lines += len(full)
        self.credit = 0
        self.active = None
        if self.step>=5 and self.mode=='rush' and self.lines>=4:
            self.phase='won'
            self.available=False
        else:
            self.available=True
            self.spawn(self.take())

    def input(self, key):
        if self.phase!='playing': return
        if key=='left': self.move(dx=-1)
        elif key=='right': self.move(dx=1)
        elif key=='rotate':
            if self.active[0]==5: return
            p=deepcopy(self.active)
            h=1+max(y for x,y in p[1])
            s=[(h-1-y,x) for x,y in p[1]]
            mx,my=min(x for x,y in s),min(y for x,y in s)
            p[1]=[(x-mx,y-my) for x,y in s]
            if self.fits(p): self.active=p
        elif key=='soft':
            if self.move(dy=1): self.score+=1
            else: self.lock()
        elif key=='hard':
            while self.move(dy=1): self.score+=2
            self.lock()
        elif key=='hold' and self.available:
            outgoing=self.active[0]
            incoming=self.held if self.held is not None else self.take()
            self.held=outgoing
            self.credit=0
            self.available=False
            self.spawn(incoming)

    def tick(self, ms):
        if self.phase!='playing': return
        self.elapsed+=ms
        self.credit+=ms
        while self.phase=='playing' and self.credit>=max(90,600-45*(self.lines//4)):
            self.credit-=max(90,600-45*(self.lines//4))
            if not self.move(dy=1): self.lock()

    def command(self, c):
        if c['cmd']=='new': self.new(c['seed'],c.get('mode','endless'))
        elif c['cmd']=='input': self.input(c['key'])
        elif c['cmd']=='tick': self.tick(c['ms'])
        elif c['cmd']=='pause' and self.phase in ('playing','paused'): self.phase='paused'
        elif c['cmd']=='resume' and self.phase in ('playing','paused'): self.phase='playing'
        elif c['cmd']=='replay':
            d=c['document']; self.new(d['seed'],d['mode']); prev=0
            for e in d['events']:
                self.tick(e['at_ms']-prev)
                self.command({'cmd':e['key']} if e['key'] in ('pause','resume') else {'cmd':'input','key':e['key']})
                prev=e['at_ms']
            self.tick(d['end_ms']-prev)

    def snapshot(self):
        s=dict(phase=self.phase,board=[''.join('#' if (x,y) in self.board else '.' for x in range(10)) for y in range(18)],
               active=None if self.active is None else dict(kind=NAMES[self.active[0]],cells=[list(c) for c in sorted(self.cells(self.active),key=lambda c:(c[1],c[0]))]),
               score=self.score,lines=self.lines,level=1+self.lines//4)
        if self.step>=3: s.update(held=None if self.held is None else NAMES[self.held],preview=[NAMES[k] for k in self.preview],hold_available=self.available)
        if self.step>=5: s.update(mode=self.mode,elapsed_ms=self.elapsed)
        return s
