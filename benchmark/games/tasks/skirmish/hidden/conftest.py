"""Black-box JSON-lines driver. GAME_BIN is the only implementation interface."""
import json
import os
import selectors
import subprocess
import tempfile
import time
from pathlib import Path

import pytest


class GameDriver:
    def __init__(self):
        binary = os.environ.get('GAME_BIN')
        if not binary:
            pytest.fail('GAME_BIN must name a built executable')
        self.stderr = tempfile.TemporaryFile(dir=Path(__file__).resolve().parents[1])
        self.proc = subprocess.Popen([str(Path(binary).resolve())], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=self.stderr, bufsize=0)
        self.buffer = bytearray()
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)
        self.timeout = float(os.environ.get('GAME_REPLY_TIMEOUT', '2'))

    def diagnostics(self):
        self.stderr.seek(0)
        return self.stderr.read().decode(errors='replace')[-3000:]

    def send(self, value):
        line = value if isinstance(value, str) else json.dumps(value, separators=(',',':'))
        assert '\n' not in line, 'driver sends one line at a time'
        try:
            self.proc.stdin.write((line+'\n').encode())
        except (BrokenPipeError, OSError) as e:
            pytest.fail(f'process stopped before reply: {e}; {self.diagnostics()}')
        deadline = time.monotonic()+self.timeout
        while b'\n' not in self.buffer:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not self.selector.select(remaining):
                pytest.fail(f'per-reply timeout for {line[:200]}; {self.diagnostics()}')
            chunk=os.read(self.proc.stdout.fileno(),65536)
            if not chunk:
                pytest.fail(f'EOF before reply for {line[:200]}; {self.diagnostics()}')
            self.buffer.extend(chunk)
        raw, _, tail = self.buffer.partition(b'\n')
        self.buffer=bytearray(tail)
        try:
            result=json.loads(raw)
        except (ValueError, UnicodeError):
            pytest.fail(f'non-JSON reply: {raw[:300]!r}')
        assert isinstance(result,dict) and type(result.get('ok')) is bool, result
        if not result['ok']:
            assert set(result)=={'ok','error'}
        else:
            assert set(result) in [set(['ok']), set(['ok','state']), set(['ok','view']),
                                  set(['ok','cells']), set(['ok','effect','amount']),
                                  set(['ok','document'])], result
        assert self.proc.poll() is None, 'process exited while stdin is still open'
        return result

    def state(self):
        reply=self.send({'cmd':'state'})
        assert reply['ok'] is True and 'state' in reply
        return reply['state']

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=2)
        self.selector.close()
        if self.proc.stdin is not None:
            self.proc.stdin.close()
        self.proc.stdout.close()
        self.stderr.close()

    def finish(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=2)
        assert self.proc.returncode == 0, self.diagnostics()
        assert not self.buffer and self.proc.stdout.read() == b'', 'unsolicited output at EOF'


@pytest.fixture
def game_factory():
    games=[]
    def make():
        g=GameDriver()
        games.append(g)
        return g
    yield make
    for g in games:
        g.close()


@pytest.fixture
def game(game_factory):
    return game_factory()
