"""One bounded cached-MLX round in the research environment; exclusive raw logs."""
import argparse
import contextlib
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

from src.arena.live import MODEL, REVISION, input_hash, run_round, verify_round

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / 'results/arena_runs'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_new(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write('\n')


def validate_request(request):
    if not isinstance(request, dict) or set(request) != {'question', 'documents', 'run_id'}:
        raise ValueError('Request accepts only question, documents and run_id')
    if not isinstance(request['run_id'], str) or not re.fullmatch('[a-f0-9]{32}', request['run_id']):
        raise ValueError('Invalid run ID')
    input_hash(request['question'], request['documents'])


def verify_saved_run(directory):
    directory = Path(directory)
    result = json.loads((directory / 'result.json').read_text())
    manifest = json.loads((directory / 'manifest.json').read_text())
    complete = json.loads((directory / 'complete.json').read_text())
    for name in ('result.json', 'calls.jsonl', 'manifest.json'):
        if sha(directory / name) != complete['sha256'][name]:
            raise ValueError(f'Saved round hash mismatch: {name}')
    calls = [json.loads(line) for line in (directory / 'calls.jsonl').read_text().splitlines()]
    if calls != list(result['calls'].values()):
        raise ValueError('Raw call log differs from result')
    if manifest['input_hash'] != result['input_hash']:
        raise ValueError('Manifest input differs')
    verify_round(result, manifest['request']['question'], manifest['request']['documents'])
    return result


def execute(request):
    validate_request(request)
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / '.inference.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another local round is running; wait for it to finish.') from exc
        directory = RUNS / request['run_id']
        directory.mkdir(exist_ok=False)
        try:
            from importlib.metadata import version
            sources = [Path(__file__), ROOT / 'src/arena/live.py',
                       ROOT / 'experiments/exp040_generated_answers.py',
                       ROOT / 'src/models/pinned_mistral.py', ROOT / 'src/models/mistral.py',
                       ROOT / 'requirements-mlx-macos.lock',
                       *sorted((ROOT / 'src/verification').glob('*.py'))]
            manifest = {
                'artifact_type': 'arena_demonstration_manifest', 'run_id': request['run_id'],
                'started_utc': datetime.now(timezone.utc).isoformat(), 'request': request,
                'input_hash': input_hash(request['question'], request['documents']),
                'model': MODEL, 'model_revision': REVISION, 'temperature': 0,
                'max_tokens': {'S1': 128, 'S2': 128, 'V3': 1024},
                'runtime_versions': {name: version(name) for name in ('mlx', 'mlx-lm', 'transformers')},
                'python': platform.python_version(), 'platform': platform.platform(),
                'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
                'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'scope': 'Engineering demonstration; no efficacy or generalization claim.',
            }
            save_new(directory / 'manifest.json', manifest)
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
            with contextlib.redirect_stdout(sys.stderr):
                from mlx_lm import stream_generate
                from mlx_lm.sample_utils import make_sampler
                from src.models.pinned_mistral import PinnedMistralModel
                started = time.perf_counter()
                model = PinnedMistralModel(MODEL, REVISION)
                load_seconds = time.perf_counter() - started
                with (directory / 'calls.jsonl').open('x', encoding='utf-8') as handle:
                    def generate(stage, user_prompt, max_tokens):
                        chat = model.tokenizer.apply_chat_template(
                            [{'role': 'user', 'content': user_prompt}], tokenize=False,
                            add_generation_prompt=True)
                        start = time.perf_counter()
                        chunks, last = [], None
                        for chunk in stream_generate(model.model, model.tokenizer, prompt=chat,
                                                     max_tokens=max_tokens, sampler=make_sampler(temp=0.0)):
                            chunks.append(chunk.text)
                            last = chunk
                        if last is None:
                            raise RuntimeError('Model produced no output event')
                        call = {'stage': stage, 'prompt': user_prompt, 'chat_prompt': chat,
                                'output': ''.join(chunks), 'max_tokens': max_tokens,
                                'latency_seconds': time.perf_counter() - start,
                                'input_tokens': last.prompt_tokens, 'output_tokens': last.generation_tokens,
                                'finish_reason': last.finish_reason, 'peak_memory_GB': last.peak_memory,
                                'model_load_seconds': load_seconds}
                        handle.write(json.dumps(call, ensure_ascii=False) + '\n')
                        handle.flush()
                        os.fsync(handle.fileno())
                        return call
                    result = run_round(request['question'], request['documents'], generate)
            verify_round(result, request['question'], request['documents'])
            save_new(directory / 'result.json', result)
            save_new(directory / 'complete.json', {
                'status': 'completed', 'completed_utc': datetime.now(timezone.utc).isoformat(),
                'sha256': {name: sha(directory / name) for name in ('manifest.json', 'calls.jsonl', 'result.json')},
            })
            return {'run_id': request['run_id'], 'result': verify_saved_run(directory),
                    'saved_directory': str(directory.relative_to(ROOT))}
        except Exception as exc:
            save_new(directory / 'error.json', {'status': 'failed', 'error': str(exc),
                                               'failed_utc': datetime.now(timezone.utc).isoformat()})
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    if args.replay:
        verify_saved_run(args.replay)
        print('Saved Arena round and raw calls replay verified.')
        return
    try:
        payload = sys.stdin.read(100001)
        if len(payload) > 100000:
            raise ValueError('Request is too large')
        result = execute(json.loads(payload))
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
