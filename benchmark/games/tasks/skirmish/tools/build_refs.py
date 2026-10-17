"""Materialize cumulative sources, without dormant future rules in earlier projects."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def source(language, step):
    stack = [True]
    out = []
    for line in (ROOT / 'tools' / (language + '.in')).read_text().splitlines():
        marker = line.strip()
        if marker.startswith('// @if '):
            stack.append(stack[-1] and step >= int(marker.split()[-1]))
        elif marker == '// @else':
            stack[-1] = stack[-2] and not stack[-1]
        elif marker == '// @end':
            stack.pop()
        elif stack[-1]:
            out.append(line)
    assert len(stack) == 1
    return '\n'.join(out) + '\n'

def project(path, language, text):
    path.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, RUSTC_WRAPPER='', GOENV='off')
    if language == 'rust':
        (path/'src').mkdir(exist_ok=True)
        (path/'Cargo.toml').write_text('[package]\nname = "skirmish"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\nserde = { version = "1", features = ["derive"] }\nserde_json = "1"\n')
        (path/'src/main.rs').write_text(text)
        subprocess.run(['cargo','fmt'],cwd=path,env=env,check=True)
        (path/'README.md').write_text('Run CI from this directory:\n\n```sh\nRUSTC_WRAPPER= cargo fmt --check\nRUSTC_WRAPPER= cargo clippy --offline -- -D warnings\nRUSTC_WRAPPER= cargo test --offline\n```\n\nBuild: `RUSTC_WRAPPER= cargo build --release --offline`. The executable is `target/release/skirmish`.\n')
    else:
        (path/'go.mod').write_text('module skirmish\n\ngo 1.22\n')
        (path/'main.go').write_text(text)
        subprocess.run(['gofmt','-w','main.go'],cwd=path,env=env,check=True)
        (path/'README.md').write_text('Run CI from this directory:\n\n```sh\ntest -z "$(gofmt -l .)"\ngo vet ./...\ngo test ./...\n```\n\nBuild: `go build -o game .` from the project root.\n')

def main():
    for language in ['rust','go']:
        for step in range(1,7):
            project(ROOT/'ref'/language/f'f{step}',language,source(language,step))
        empty = 'fn main() {}\n' if language=='rust' else 'package main\n\nfunc main() {}\n'
        project(ROOT/'fixture'/language,language,empty)
    for step in [2,3,5,6]:
        text=source('rust',step)
        if step==2:
            # Movement validation has routes; the destination listing retains a radius.
            text=text.replace('if self.move_allowed(u,x,y) {cells.push([x,y]);}',
                'if (x,y)!=(u.x,u.y) && stand(&u.kind,x,y) && distance((u.x,u.y),(x,y))<=facts(&u.kind).unwrap().movement && !self.units.iter().any(|v| v.id!=u.id && (v.x,v.y)==(x,y)) {cells.push([x,y]);}')
        elif step==3:
            # The sight filter is omitted from the otherwise correct player's view.
            text=text.replace('view.units.retain(|u| self.visible(player,u));','// The observer unit list was reused for the player view.')
        elif step==5:
            text=text.replace('let (effect,amount)=self.interaction(u,r["target"].as_i64().unwrap())?;',
                'let (effect,mut amount)=self.interaction(u,r["target"].as_i64().unwrap())?; if effect=="damage" {amount=facts(&u.kind).unwrap().attack;}')
        elif step==6:
            text=text.replace('|| g.units[..i].iter().any(|p| (p.x,p.y)==(u.x,u.y))','')
        assert text!=source('rust',step)
        project(ROOT/'ref_missed'/'rust'/f'f{step}','rust',text)

if __name__=='__main__': main()
