"""Generate additional function implementations for frozen P5b decompositions.

P5c preregistration: reuse the exact decompositions produced by the frozen P5b
run and only increase the number of implementations per function (k: 2 -> 8).
The decompositions are NOT regenerated, so the number of implementations is the
single manipulated variable.

Also applies the preregistered protocol repairs:
* ``repair_v1`` implementation prompt (hard output checklist),
* one retry for implementations that fail to parse, using a shifted seed so the
  retry is not a deterministic repeat.

Usage:
    python scripts/generate_extra_implementations.py \
        --decompositions data/processed/p5b_medium20_m2a_skeleton_..._decompositions.jsonl \
        --implementations data/processed/p5b_medium20_m2a_skeleton_..._implementations.jsonl \
        --output data/processed/p5c_medium_k8_repairv1_seed42_v1_implementations.jsonl \
        --k 8 --retries 1
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.decomposition import decomposition_from_dict, validate_decomposition  # noqa: E402
from src.modular import ImplementationGenerator  # noqa: E402

RETRY_SEED_SHIFT = 1000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/apps_stratified60_20260918.json")
    parser.add_argument("--decompositions", required=True)
    parser.add_argument("--implementations", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--prompt-variant", default="repair_v1", choices=["baseline", "repair_v1"])
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N problems (smoke testing); 0 means all")
    args = parser.parse_args()

    data_path = _resolve(args.data)
    problems = {str(item["problem_id"]): item for item in load_problems(data_path)}

    # 已有实现：决定从哪个序号开始补
    existing: dict[tuple[str, int, str], set[int]] = defaultdict(set)
    for line in _resolve(args.implementations).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("code"):
            existing[(str(r.get("problem_id")), int(r.get("decomposition_index", 0)), str(r.get("function_name")))].add(
                int(r.get("implementation_index", 0))
            )

    decompositions: list[tuple[str, int, object]] = []
    for line in _resolve(args.decompositions).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        pid = str(r.get("problem_id"))
        parsed = r.get("decomposition")
        if not parsed or pid not in problems:
            continue
        d = decomposition_from_dict(parsed, str(r.get("raw_response", "")))
        if validate_decomposition(d, problems[pid])["valid"]:
            decompositions.append((pid, int(r.get("candidate_index", 0)), d))

    if args.limit:
        seen: list[str] = []
        for pid, _di, _d in decompositions:
            if pid not in seen:
                seen.append(pid)
        keep = set(seen[: args.limit])
        decompositions = [item for item in decompositions if item[0] in keep]

    output_path = _resolve(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path = Path(str(output_path).replace(".jsonl", "") + "_progress.log")
    progress = progress_path.open("w", encoding="utf-8")
    done_keys: set[tuple[str, int, str, int]] = set()
    if output_path.exists():
        for line in output_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done_keys.add((str(r.get("problem_id")), int(r.get("decomposition_index", 0)), str(r.get("function_name")), int(r.get("implementation_index", 0))))

    generator = ImplementationGenerator(model=args.model, seed=args.seed)
    retry_generator = ImplementationGenerator(model=args.model, seed=args.seed + RETRY_SEED_SHIFT)

    stats = Counter()
    prompt_tokens = output_tokens = 0
    started = time.perf_counter()
    todo = sum(
        1
        for pid, di, d in decompositions
        for f in d.functions
        for idx in range(args.k)
        if idx not in existing.get((pid, di, f.name), set())
    )

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        progress.write(line + "\n")
        progress.flush()

    log(f"start model={args.model} k={args.k} variant={args.prompt_variant} decompositions={len(decompositions)} todo={todo}")

    with output_path.open("a", encoding="utf-8") as handle:
        for pid, di, d in decompositions:
            problem = problems[pid]
            for target in d.functions:
                have = existing.get((pid, di, target.name), set())
                for idx in range(args.k):
                    if idx in have:
                        continue
                    key = (pid, di, target.name, idx)
                    if key in done_keys:
                        continue
                    record = None
                    for attempt in range(args.retries + 1):
                        gen = generator if attempt == 0 else retry_generator
                        try:
                            record = gen.generate(problem, d, target, idx, args.prompt_variant)
                        except Exception as exc:  # 网络/服务异常：计一次失败，继续
                            stats["request_error"] += 1
                            record = {
                                "problem_id": pid,
                                "function_name": target.name,
                                "implementation_index": idx,
                                "error": f"request_failed:{type(exc).__name__}",
                            }
                        record["decomposition_index"] = di
                        record["attempt"] = attempt
                        usage = record.get("usage") or {}
                        prompt_tokens += int(usage.get("prompt_eval_count") or 0)
                        output_tokens += int(usage.get("eval_count") or 0)
                        stats["requests"] += 1
                        if record.get("code"):
                            stats["valid"] += 1
                            if attempt:
                                stats["valid_after_retry"] += 1
                            break
                        stats["invalid"] += 1
                        if attempt < args.retries:
                            stats["retry"] += 1
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    handle.flush()
                    done_keys.add(key)
                    if stats["requests"] % 50 == 0:
                        log(
                            f"progress requests={stats['requests']}/{todo} valid={stats['valid']} "
                            f"invalid={stats['invalid']} retried_ok={stats['valid_after_retry']} "
                            f"out_tokens={output_tokens} elapsed={time.perf_counter() - started:.0f}s"
                        )
            log(f"problem {pid} done; requests={stats['requests']} elapsed={time.perf_counter() - started:.0f}s")

    summary = {
        "stage": "p5c_generate_extra_implementations",
        "model": args.model,
        "seed": args.seed,
        "k": args.k,
        "prompt_variant": args.prompt_variant,
        "retries": args.retries,
        "data": str(data_path),
        "decompositions": str(_resolve(args.decompositions)),
        "source_implementations": str(_resolve(args.implementations)),
        "output": str(output_path),
        "todo": todo,
        "requests": stats["requests"],
        "valid": stats["valid"],
        "invalid": stats["invalid"],
        "retry_attempts": stats["retry"],
        "valid_after_retry": stats["valid_after_retry"],
        "request_errors": stats["request_error"],
        "model_prompt_tokens": prompt_tokens,
        "model_output_tokens": output_tokens,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    Path(str(output_path).replace(".jsonl", "") + "_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"finished requests={stats['requests']} valid={stats['valid']} invalid={stats['invalid']} "
        f"valid_after_retry={stats['valid_after_retry']} out_tokens={output_tokens}")
    progress.close()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
