#!/usr/bin/env python3
from __future__ import annotations

import atexit
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
WEB_PORT = os.environ.get('PLAYWRIGHT_WEB_PORT', '3100')
API_PORT = os.environ.get('PLAYWRIGHT_API_PORT', '8100')
WEB_URL = f'http://localhost:{WEB_PORT}'
API_URL = f'http://localhost:{API_PORT}'
TMP_DIR = Path(tempfile.mkdtemp(prefix='tispetta-e2e.'))
API_LOG = TMP_DIR / 'api.log'
WEB_LOG = TMP_DIR / 'web.log'
PROCS: list[subprocess.Popen[bytes]] = []


def print_phase(label: str) -> None:
    print(f'\n==> {label}', flush=True)


def port_is_free(port: str) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(('127.0.0.1', int(port))) != 0


def wait_for_url(url: str, name: str, timeout: int = 120, proc: subprocess.Popen[bytes] | None = None) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError(f'{name} exited before becoming ready at {url}.')
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if 200 <= response.status < 500:
                    return
        except Exception:
            time.sleep(1)
    raise RuntimeError(f'{name} did not become ready at {url} within {timeout}s.')


def cleanup() -> None:
    for proc in reversed(PROCS):
        if proc.poll() is None:
            proc.terminate()
    for proc in reversed(PROCS):
        if proc.poll() is None:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


def print_logs() -> None:
    print(f'\nAPI log: {API_LOG}')
    if API_LOG.exists():
        print(API_LOG.read_text()[:6000])
    print(f'\nWeb log: {WEB_LOG}')
    if WEB_LOG.exists():
        print(WEB_LOG.read_text()[:6000])


def run_sync(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def start_process(command: list[str], cwd: Path, env: dict[str, str], log_path: Path) -> subprocess.Popen[bytes]:
    log_file = log_path.open('wb')
    proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=log_file, stderr=subprocess.STDOUT)
    PROCS.append(proc)
    return proc


def main() -> int:
    atexit.register(cleanup)
    try:
        if not port_is_free(WEB_PORT):
            print(f'Port {WEB_PORT} is already serving traffic. Stop the existing process before running E2E.', file=sys.stderr)
            return 1
        if not port_is_free(API_PORT):
            print(f'Port {API_PORT} is already serving traffic. Stop the existing process before running E2E.', file=sys.stderr)
            return 1

        common_env = os.environ.copy()
        common_env.setdefault('PLAYWRIGHT_APP_BASE_URL', WEB_URL)

        print_phase('Prepare seeded API')
        run_sync(['python3', 'qa/scripts/prepare_seeded_api.py'], env=common_env)

        print_phase('Start API')
        api_env = common_env | {
            'DATABASE_URL': f'sqlite:///{ROOT / "services" / "api" / "benefits_engine.db"}',
            'APP_BASE_URL': WEB_URL,
            'CORS_ALLOWED_ORIGINS': WEB_URL,
            'ENVIRONMENT': 'development',
            'SESSION_COOKIE_SECURE': 'false',
        }
        start_process(
            ['python3', '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', API_PORT, '--log-level', 'warning'],
            cwd=ROOT / 'services' / 'api',
            env=api_env,
            log_path=API_LOG,
        )
        wait_for_url(f'{API_URL}/health', 'API', proc=PROCS[-1])

        print_phase('Start web app')
        web_env = common_env | {
            'NEXT_PUBLIC_APP_URL': WEB_URL,
            'NEXT_PUBLIC_API_URL': API_URL,
            'INTERNAL_API_URL': API_URL,
            'SESSION_COOKIE_SECURE': 'false',
            'SESSION_COOKIE_DOMAIN': '',
            'NEXT_PUBLIC_GA_MEASUREMENT_ID': '',
            'NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION': '',
        }
        start_process(
            ['pnpm', 'exec', 'next', 'dev', '-p', WEB_PORT, '--hostname', 'localhost'],
            cwd=ROOT / 'apps' / 'web',
            env=web_env,
            log_path=WEB_LOG,
        )
        wait_for_url(WEB_URL, 'Web app', proc=PROCS[-1])

        print_phase('Critical E2E')
        test_env = common_env | {
            'PLAYWRIGHT_SKIP_WEBSERVER': '1',
            'PLAYWRIGHT_API_URL': API_URL,
            'PLAYWRIGHT_BASE_URL': WEB_URL,
        }
        result = subprocess.run(
            ['./node_modules/.bin/playwright', 'test', '--config=playwright.config.ts'],
            cwd=ROOT,
            env=test_env,
            check=False,
        )
        if result.returncode != 0:
            print_logs()
        return result.returncode
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        print_logs()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
