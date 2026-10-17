"""Write committed goldens from explicit scenario expectations, never from a reference."""
from copy import deepcopy
import heapq
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MAP=['.........','..ss..#..','.s.#..#..','...#ss...','.##...##.',
     '...ss#...','..#..#.s.','..#..ss..','.........']
HP={'lancer':8,'bolt':6,'glider':5,'mender':7}
SIGHT={'lancer':3,'bolt':4,'glider':2,'mender':5}
OK={'ok':True}
IDLE={'turn':0,'phase':'idle','winner':None,'ended':[],'units':[]}

def unit(i,p,k,x,y,hp=None):
    return dict(id=i,owner=p,kind=k,x=x,y=y,hp=HP[k] if hp is None else hp,order=None)

def initial(us): return dict(turn=1,phase='planning',winner=None,ended=[],units=sorted(deepcopy(us),key=lambda u:u['id']))
def new(us): return dict(cmd='new',units=[{k:u[k] for k in ['id','owner','kind','x','y']} for u in us])
def order(i,p,o): return dict(cmd='order',player=p,unit=i,order=o)
def attack(i): return dict(type='attack',target=i)
def move(x,y): return dict(type='move',to=[x,y])
def forecast(i,p,t): return dict(cmd='forecast',player=p,unit=i,target=t)
def reach(i,p): return dict(cmd='reachable',player=p,unit=i)

class Scenario:
    def __init__(self,name): self.name=name;self.s=deepcopy(IDLE);self.events=[]
    def event(self,c,r=OK,s=None):
        if s is not None:self.s=deepcopy(s)
        self.events.append(dict(command=c,reply=deepcopy(r),state=deepcopy(self.s)))
    def start(self,us): self.event(new(us),s=initial(us))
    def put(self,i,p,o):
        s=deepcopy(self.s);next(u for u in s['units'] if u['id']==i)['order']=o
        self.event(order(i,p,o),s=s)
    def end(self,p,s=None):
        if s is None:s=deepcopy(self.s);s['ended']=[p]
        self.event(dict(cmd='end_turn',player=p),s=s)
    def refuse(self,c,e): self.event(c,dict(ok=False,error=e))
    def dump(self):return dict(name=self.name,events=self.events)

def turn(s,changes=None,removed=(),winner=None):
    s=deepcopy(s);s['turn']+=1;s['ended']=[]
    s['units']=[u for u in s['units'] if u['id'] not in removed]
    for u in s['units']:u['order']=None;u.update((changes or {}).get(u['id'],{}))
    if winner is not None:s['phase']='finished';s['winner']=winner
    return s

def view(s,p):
    v=deepcopy(s);own=[u for u in s['units'] if u['owner']==p]
    cells=[[x,y] for y in range(9) for x in range(9) if any(abs(x-u['x'])+abs(y-u['y'])<=SIGHT[u['kind']] for u in own)]
    v['units']=[u for u in v['units'] if u['owner']==p or [u['x'],u['y']] in cells]
    for u in v['units']:
        if u['owner']!=p:u['order']=None
    v['visible']=cells
    return dict(ok=True,view=v)

def routes(u,us):
    # Independent shortest-path calculation used only while authoring the literal.
    dist={(u['x'],u['y']):0};queue=[(0,u['x'],u['y'])];budget={'lancer':3,'bolt':2,'glider':4,'mender':3}[u['kind']]
    while queue:
        d,x,y=heapq.heappop(queue)
        if d!=dist[(x,y)]:continue
        for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if not (0<=nx<9 and 0<=ny<9):continue
            t=MAP[ny][nx]
            if t=='#' and u['kind']!='glider':continue
            nd=d+{'.':1,'s':2,'#':3}[t]
            if nd<=budget and nd<dist.get((nx,ny),1000):dist[(nx,ny)]=nd;heapq.heappush(queue,(nd,nx,ny))
    occupied={(v['x'],v['y']) for v in us}
    return [list(c) for c in sorted(dist,key=lambda c:(c[1],c[0])) if c not in occupied]

def main():
    cases={k:[] for k in range(1,7)}
    a=Scenario('idle, replacement, exact range and simultaneous damage')
    a.event({'cmd':'state'},dict(ok=True,state=IDLE))
    a.refuse({'cmd':'end_turn','player':1},'not_started')
    a.event({'cmd':'new'},s=initial([unit(1,1,'lancer',1,0),unit(2,1,'bolt',4,0),unit(3,1,'glider',7,0),unit(11,2,'lancer',1,8),unit(12,2,'bolt',4,8),unit(13,2,'glider',7,8)]))
    us=[unit(1,1,'bolt',8,0),unit(2,2,'lancer',7,0)]
    a.start(us)
    a.event(reach(1,1),dict(ok=True,cells=[[6,0],[7,1],[8,1],[8,2]]))
    a.put(1,1,move(8,1));a.put(1,1,{'type':'hold'});a.put(1,1,attack(2))
    a.event(forecast(1,1,2),dict(ok=True,effect='damage',amount=2))
    a.put(2,2,attack(1));a.event(forecast(2,2,1),dict(ok=True,effect='damage',amount=3))
    a.end(2);a.refuse(order(2,2,{'type':'hold'}),'turn_ended')
    a.event(forecast(2,2,1),dict(ok=True,effect='damage',amount=3))
    a.end(1,turn(a.s,{1:{'hp':3},2:{'hp':6}}))
    a.put(1,1,attack(2));a.put(2,2,attack(1));a.end(1)
    a.end(2,turn(a.s,{2:{'hp':4}},removed=[1],winner=2))
    a.refuse(reach(2,2),'finished');a.refuse(order(2,2,{'type':'hold'}),'finished')
    cases[1].append(a.dump())
    a=Scenario('shared destination cancels both moves')
    a.start([unit(1,1,'bolt',8,0),unit(2,2,'lancer',8,2)])
    a.put(1,1,move(8,1));a.put(2,2,move(8,1));a.end(1);a.end(2,turn(a.s))
    cases[1].append(a.dump())
    a=Scenario('simultaneous elimination is a draw')
    a.start([unit(1,1,'glider',8,0),unit(2,2,'glider',7,0)])
    for hp in [3,1]:
        a.put(1,1,attack(2));a.put(2,2,attack(1));a.end(1);a.end(2,turn(a.s,{1:{'hp':hp},2:{'hp':hp}}))
    a.put(1,1,attack(2));a.put(2,2,attack(1));a.end(1);a.end(2,turn(a.s,removed=[1,2],winner=0))
    cases[1].append(a.dump())
    a=Scenario('attack uses destination range and all attackers fire')
    a.start([unit(1,1,'lancer',8,0),unit(2,2,'bolt',7,0)])
    a.put(1,1,attack(2));a.put(2,2,move(7,2));a.end(1);a.end(2,turn(a.s,{2:{'x':7,'y':2}}))
    cases[1].append(a.dump())
    a=Scenario('thicket route costs replace the radius')
    us=[unit(1,1,'lancer',1,1),unit(2,2,'bolt',8,8)];a.start(us)
    a.event(reach(1,1),dict(ok=True,cells=routes(us[0],us)))
    a.refuse(order(1,1,move(3,1)),'invalid_order');a.put(1,1,move(2,1));a.end(1)
    a.end(2,turn(a.s,{1:{'x':2,'y':1}}));cases[2].append(a.dump())
    a=Scenario('glider enters crag within its cost budget')
    us=[unit(1,1,'glider',5,1),unit(2,2,'lancer',8,8)];a.start(us)
    a.event(reach(1,1),dict(ok=True,cells=routes(us[0],us)))
    a.put(1,1,move(6,1));a.end(2);a.end(1,turn(a.s,{1:{'x':6,'y':1}}));cases[2].append(a.dump())
    a=Scenario('routes ignore intermediate units')
    a.start([unit(1,1,'bolt',0,0),unit(3,1,'lancer',1,0),unit(2,2,'bolt',8,8)])
    a.put(1,1,move(2,0));a.end(1);a.end(2,turn(a.s,{1:{'x':2,'y':0}}));cases[2].append(a.dump())
    a=Scenario('unseen occupancy, hidden orders and swap cancellation')
    a.event({'cmd':'view','player':1},view(a.s,1))
    a.start([unit(1,1,'glider',0,0),unit(2,2,'glider',3,0)])
    a.put(2,2,{'type':'hold'});a.event({'cmd':'view','player':1},view(a.s,1))
    a.refuse(forecast(1,1,2),'unavailable');a.refuse(forecast(1,1,99),'unavailable')
    a.put(1,1,move(3,0));a.end(1);a.end(2,turn(a.s))
    a.put(1,1,move(3,0));a.put(2,2,move(0,0));a.end(2);a.end(1,turn(a.s))
    a.event({'cmd':'view','player':1},view(a.s,1));cases[3].append(a.dump())
    a=Scenario('blocked unseen chain cancels to a fixed point')
    a.start([unit(1,1,'glider',0,0),unit(2,2,'glider',3,0),unit(3,1,'glider',6,0)])
    a.put(1,1,move(3,0));a.put(2,2,move(6,0));a.end(1);a.end(2,turn(a.s))
    cases[3].append(a.dump())
    a=Scenario('four-unit cycle moves together')
    a.start([unit(1,1,'glider',5,0),unit(2,2,'glider',8,0),unit(3,1,'glider',8,3),unit(4,2,'glider',5,3)])
    for i,p,x,y in [(1,1,8,0),(2,2,8,3),(3,1,5,3),(4,2,5,0)]:a.put(i,p,move(x,y))
    a.end(1);a.end(2,turn(a.s,{1:{'x':8,'y':0},2:{'x':8,'y':3},3:{'x':5,'y':3},4:{'x':5,'y':0}}))
    cases[3].append(a.dump())
    a=Scenario('visible enemies conceal orders; terrain never blocks sight')
    a.start([unit(1,1,'bolt',4,0),unit(2,2,'bolt',7,0)])
    a.put(2,2,attack(1));a.event({'cmd':'view','player':1},view(a.s,1))
    a.put(1,1,move(4,1));a.end(1);a.end(2,turn(a.s,{1:{'x':4,'y':1}}))
    a.event({'cmd':'view','player':2},view(a.s,2));cases[3].append(a.dump())
    a=Scenario('repair precedes damage, caps hp and predicts actual restoration')
    a.start([unit(1,1,'mender',0,0),unit(3,1,'bolt',1,0),unit(2,2,'bolt',2,0)])
    a.event({'cmd':'view','player':1},view(a.s,1))
    a.event(forecast(1,1,3),dict(ok=True,effect='repair',amount=0))
    a.refuse(order(1,1,attack(2)),'invalid_order')
    a.put(2,2,attack(3));a.end(1);a.end(2,turn(a.s,{3:{'hp':4}}))
    a.event(forecast(1,1,3),dict(ok=True,effect='repair',amount=2))
    a.put(1,1,attack(3));a.put(2,2,attack(3));a.put(3,1,attack(2));a.end(1)
    a.end(2,turn(a.s,{3:{'hp':4},2:{'hp':4}}))
    a.put(1,1,attack(3));a.end(1);a.end(2,turn(a.s,{3:{'hp':6}}))
    cases[4].append(a.dump())
    a=Scenario('menders alone remain in play')
    a.start([unit(1,1,'mender',0,0),unit(2,2,'mender',8,8)])
    a.end(1);a.end(2,turn(a.s));a.event(reach(1,1),dict(ok=True,cells=routes(a.s['units'][0],a.s['units'])))
    cases[4].append(a.dump())
    a=Scenario('thicket replaces damage and forecast follows it')
    a.start([unit(1,1,'lancer',1,1),unit(2,2,'bolt',2,1)])
    a.event(forecast(1,1,2),dict(ok=True,effect='damage',amount=1))
    a.put(1,1,attack(2));a.end(1);a.end(2,turn(a.s,{2:{'hp':5}}));cases[5].append(a.dump())
    a=Scenario('post-move shelter can reduce damage to zero')
    a.start([unit(1,1,'bolt',1,0),unit(2,2,'lancer',1,1)])
    a.event(forecast(1,1,2),dict(ok=True,effect='damage',amount=2))
    a.put(1,1,attack(2));a.put(2,2,move(2,1));a.end(1)
    a.end(2,turn(a.s,{2:{'x':2,'y':1}}))
    a.event(forecast(1,1,2),dict(ok=True,effect='damage',amount=0))
    a.put(1,1,attack(2));a.end(1);a.end(2,turn(a.s));cases[5].append(a.dump())
    a=Scenario('crag provides no defence')
    a.start([unit(1,1,'lancer',5,1),unit(2,2,'glider',6,1)])
    a.event(forecast(1,1,2),dict(ok=True,effect='damage',amount=3))
    a.put(1,1,attack(2));a.end(1);a.end(2,turn(a.s,{2:{'hp':2}}));cases[5].append(a.dump())
    a=Scenario('idle and half-ended documents preserve the entire battle')
    a.event({'cmd':'export'},dict(ok=True,document=IDLE))
    a.event({'cmd':'import','document':IDLE},s=IDLE)
    a.start([unit(1,1,'mender',0,0),unit(3,1,'bolt',1,0),unit(2,2,'bolt',2,0)])
    a.put(2,2,attack(3));a.end(2)
    doc=deepcopy(a.s);a.event({'cmd':'export'},dict(ok=True,document=doc))
    a.event({'cmd':'new'},s=initial([unit(1,1,'lancer',1,0),unit(2,1,'bolt',4,0),unit(3,1,'glider',7,0),unit(11,2,'lancer',1,8),unit(12,2,'bolt',4,8),unit(13,2,'glider',7,8)]))
    a.event({'cmd':'import','document':doc},s=doc)
    a.end(1,turn(a.s,{3:{'hp':4}}));cases[6].append(a.dump())
    for k,cs in cases.items():
        (ROOT/'hidden'/f'scenarios_f{k}.json').write_text(json.dumps(cs,indent=2)+'\n')

if __name__=='__main__':main()
