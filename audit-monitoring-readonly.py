"""Read-only monitoring inventory. No installs, edits, service changes or load tests."""
import argparse
import ast
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def command(args):
    if not shutil.which(args[0]):
        return {'status': 'NOT_IN_PATH'}
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=8)
        # Avoid returning command errors that might contain credentials or config details.
        return {'status': 'OK' if result.returncode == 0 else 'UNAVAILABLE',
                'exit_code': result.returncode,
                'output': result.stdout[:12000] if result.returncode == 0 else ''}
    except subprocess.TimeoutExpired:
        return {'status': 'TIMEOUT'}
    except OSError as error:
        return {'status': 'OS_ERROR', 'error_type': type(error).__name__}


def inventory(project):
    files, metrics = [], []
    ignored = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.cache',
               'data', 'benchmark_outputs', 'models', 'work', 'logs'}
    visited = 0
    for directory, folders, names in os.walk(project, followlinks=False):
        folders[:] = sorted(d for d in folders if d not in ignored and not d.startswith('.')
                            and not (Path(directory) / d).is_symlink())
        relative = Path(directory).relative_to(project)
        if len(relative.parts) >= 4:
            folders[:] = []
        for name in sorted(names):
            visited += 1
            if visited > 2000:
                return {'files': files, 'instrumentation': metrics, 'truncated': True}
            path = Path(directory) / name
            if path.is_symlink() or name.startswith('.env') or re.search(r'secret|credential|token|password', name, re.I):
                continue
            rel = str(path.relative_to(project))
            is_code = path.suffix == '.py'
            relevant = is_code or bool(re.search(r'docker|compose|prometheus|grafana|dashboard|monitor|requirements|pyproject|helm|chart', rel, re.I))
            if relevant and len(files) < 200:
                files.append(rel)
            # Report only instrumentation locations and metric identifiers, never file contents.
            if is_code and path.stat().st_size <= 300000:
                try:
                    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
                except (OSError, UnicodeError, SyntaxError):
                    continue
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    func = node.func
                    label = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ''
                    if label in {'Counter', 'Gauge', 'Histogram', 'Summary', 'Instrumentator', 'make_asgi_app', 'start_http_server'}:
                        row = {'file': rel, 'line': node.lineno, 'call': label}
                        if label in {'Counter', 'Gauge', 'Histogram', 'Summary'} and node.args:
                            first = node.args[0]
                            if isinstance(first, ast.Constant) and isinstance(first.value, str) and re.fullmatch(r'[a-zA-Z_:][a-zA-Z0-9_:]*', first.value):
                                row['metric_name'] = first.value
                        if len(metrics) < 100:
                            metrics.append(row)
    return {'files': files, 'instrumentation': metrics, 'truncated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    args = parser.parse_args()
    project = args.project.resolve()
    if sys.platform != 'linux' or not project.is_dir():
        raise RuntimeError('Run on the new Linux server with an existing project directory.')
    os_release = {}
    path = Path('/etc/os-release')
    if path.is_file():
        for line in path.read_text().splitlines():
            key, _, value = line.partition('=')
            if key in {'PRETTY_NAME', 'VERSION_ID'}:
                os_release[key] = value.strip('"')
    packages = {}
    for name in ['vllm', 'torch', 'fastapi', 'uvicorn', 'prometheus-client', 'prometheus-fastapi-instrumentator']:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = 'NOT_IN_THIS_PYTHON'
    report = {'mode': 'READ_ONLY_INVENTORY', 'project': str(project),
        'os': os_release, 'python': sys.version.split()[0], 'python_executable': sys.executable,
        'uid': os.getuid(), 'docker_container_marker': Path('/.dockerenv').exists(),
        'pid_1': Path('/proc/1/comm').read_text().strip() if Path('/proc/1/comm').is_file() else None,
        'commands': {name: shutil.which(name) for name in ['docker', 'kubectl', 'helm', 'prometheus', 'grafana', 'grafana-server', 'nvidia-smi']},
        'packages': packages, 'repository': inventory(project),
        'git_status': command(['git', '--no-optional-locks', '-C', str(project), 'status', '--short']),
        'listening_tcp_ports': command(['ss', '-lnt']),
        'containers': command(['docker', 'ps', '--format', '{{.Names}}\t{{.Image}}\t{{.Ports}}']),
        'gpu': command(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,driver_version', '--format=csv,noheader']),
        'limitations': ['No live metrics, Grafana datasource or Prometheus targets queried yet.',
            'No Kubernetes cluster queried; existing context and access need confirmation.',
            'Unavailable commands do not prove that host services are absent.',
            'Python package versions describe only this interpreter.',
            'No environment values, config contents, process arguments, secrets or document text emitted.',
            'No installs, modifications, restarts, port changes, model downloads or inference requests.']}
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
