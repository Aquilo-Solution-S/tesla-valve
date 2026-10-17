#!/usr/bin/env python3
"""Validate the complete instrument; all build artifacts are temporary and removed."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
PYTHON=sys.executable   # the Python running the selftest needs pytest


def run(args, cwd, env, timeout=180):
    try:
        p=subprocess.run(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                         text=True,timeout=timeout)
        return p.returncode,p.stdout
    except (subprocess.TimeoutExpired,OSError) as e:
        return 99,str(e)


class Audit:
    def __init__(self):
        self.failures=0

    def check(self, label, passed, detail=''):
        print(('ok ' if passed else 'XX ')+label,flush=True)
        if not passed:
            self.failures+=1
            # Success emits only ok lines. Failures include actionable diagnostics.
            if detail:
                print(detail[-6000:],flush=True)


def main():
    audit=Audit()
    with tempfile.TemporaryDirectory(prefix='.selftest-',dir=ROOT) as tmp:
        tmp=Path(tmp)
        env=os.environ.copy()
        env.update(RUSTC_WRAPPER='',CARGO_TARGET_DIR=str(tmp/'cargo-build'),PYTHONDONTWRITEBYTECODE='1',
                   GOCACHE=str(tmp/'go-cache'), GOENV='off', TMPDIR=str(tmp))
        bins={}

        def project_env(project):
            local=env.copy()
            label=str(project.relative_to(ROOT)).replace('/', '-')
            local['CARGO_TARGET_DIR']=str(tmp/(label+'-cargo-build'))
            return local

        def build(project,lang,label):
            exe=tmp/(label.replace('/','-')+'-bin')
            buildenv=project_env(project)
            if lang=='rust':
                code,out=run(['cargo','build','--offline'],project,buildenv)
                if code==0: shutil.copy2(Path(buildenv['CARGO_TARGET_DIR'])/'debug/skirmish',exe)
            else:
                code,out=run(['go','build','-o',str(exe),'.'],project,env)
            return (exe if code==0 else None),out

        def ci(project,lang):
            cienv=project_env(project)
            if lang=='rust':
                commands=[['cargo','fmt','--check'],['cargo','clippy','--offline','--','-D','warnings'],['cargo','test','--offline']]
            else:
                code,out=run(['gofmt','-l','.'],project,env)
                if code or out.strip(): return False,out
                commands=[['go','vet','./...'],['go','test','./...']]
            for command in commands:
                code,out=run(command,project,cienv)
                if code: return False,out
            return True,''

        def hidden(exe,first,last,negative=False):
            if exe is None: return 99,'binary did not build'
            gameenv=env.copy(); gameenv['GAME_BIN']=str(exe)
            files=[str(ROOT/f'hidden/test_f{k}.py') for k in range(first,last+1)]
            args=[PYTHON,'-m','pytest','-q','-p','no:cacheprovider']
            if negative: args.append('-x')
            return run(args+files,ROOT,gameenv,timeout=180)

        for lang in ['rust','go']:
            for step in range(1,7):
                label=f'ref/{lang}/f{step}'
                project=ROOT/label
                passed,detail=ci(project,lang)
                audit.check(f'{label} CI',passed,detail)
                exe,detail=build(project,lang,label)
                bins[lang,step]=exe
                code,out=hidden(exe,1,step)
                audit.check(f'{label} hidden f1..f{step}',code==0,detail+out)
            for step in range(2,7):
                code,out=hidden(bins[lang,step-1],step,step,negative=True)
                audit.check(f'test_f{step} rejects ref/{lang}/f{step-1}',code==1,out if code!=1 else '')
            project=ROOT/'fixture'/lang
            passed,detail=ci(project,lang)
            audit.check(f'fixture/{lang} CI',passed,detail)
            exe,detail=build(project,lang,f'fixture/{lang}')
            code,out=hidden(exe,1,1,negative=True)
            audit.check(f'test_f1 rejects fixture/{lang}',code==1,detail+out if code!=1 else '')

        for step in [2,3,5,6]:
            label=f'ref_missed/rust/f{step}'
            project=ROOT/label
            passed,detail=ci(project,'rust')
            audit.check(f'{label} CI',passed,detail)
            exe,detail=build(project,'rust',label)
            code,out=hidden(exe,1,step-1)
            audit.check(f'{label} passes earlier hidden tests',code==0,detail+out)
            code,out=hidden(exe,step,step,negative=True)
            audit.check(f'test_f{step} rejects {label}',code==1,out if code!=1 else '')
    if audit.failures:
        raise SystemExit(f'{audit.failures} invalid checks')
    print('instrument valid')


if __name__=='__main__':
    main()
