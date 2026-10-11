"""Check explicit plausible defects, not a claim of exhaustive mutation testing."""
import argparse
import json
from pathlib import Path
from bounded_execution import evaluate


MUTATIONS = {
    "D1_B03": [
        ("ignore_csi_parameters", 'if j < len(text) and "@" <= text[j] <= "~":', 'if j == i + 2 and j < len(text) and "@" <= text[j] <= "~":'),
        ("drop_incomplete_escape", 'out.append(text[i]); i += 1', 'out.append(text[i] if text[i] != "\\x1b" else ""); i += 1'),
    ],
    "D1_B04": [
        ("blank_is_empty_string", 'unquote(value.replace("+", " ")) if value else None', 'unquote(value.replace("+", " ")) if value else ""'),
        ("set_appends", 'if op["op"] in ("set", "delete"):', 'if op["op"] == "delete":'),
    ],
    "D1_B05": [
        ("bool_is_numeric", 'type(value) in (int, float)', 'isinstance(value, (int, float))'),
        ("strict_threshold", 'value >= p["threshold"]', 'value > p["threshold"]'),
    ],
    "D1_B06": [
        ("ignore_query_default", 'value = query["default"] if "default" in query else {"error": "missing"}', 'value = {"error": "missing"}'),
        ("reject_numeric_string_index", 'segment = int(segment)', 'raise ValueError("string index")'),
    ],
    "D1_M03": [
        ("peek_consumes", 'if name == "next":', 'if name in ("next", "peek"):'),
        ("seek_shrinks_cache", 'seen = max(seen, position); result = None', 'seen = position; result = None'),
    ],
    "D1_M04": [
        ("contains_consumes", 'result = offset < len(values)', 'result = offset < len(values)\n            if result: offsets[key] = offset + 1'),
        ("ignore_validator", 'if p.get("allowed_keys") is None or item["key"] in p["allowed_keys"]:', 'if True:'),
    ],
    "D1_M05": [
        ("reverse_ties_reverse_rows", 'tuple(columns[k][index] for k in p.get("keys", [0]))', 'tuple(columns[k][index] for k in p.get("keys", [0])) + (index,)'),
        ("ignore_strict_lengths", 'if p.get("strict", False) and len(set(lengths)) > 1:', 'if False and len(set(lengths)) > 1:'),
    ],
    "D1_C03": [
        ("fifo_hit", 'pair = records.pop(indexes[0]); result = pair[1]; records.append(pair)', 'pair = records[indexes[0]]; result = pair[1]'),
        ("clear_resets_count", 'records.clear(); result = None', 'records.clear(); count = 0; result = None'),
    ],
    "D1_C04": [
        ("shared_instance_state", 'state = states[op["instance"]]', 'state = next(iter(states.values()))'),
        ("clear_resets_instance_count", 'state["keys"].clear(); result = None', 'state["keys"].clear(); state["count"] = 0; result = None'),
    ],
    "D1_C05": [
        ("ignore_types", 'if same and p.get("typed", False):', 'if False and same and p.get("typed", False):'),
        ("ignore_keyword_names", 'kw1 == kw2', 'sorted(kw1.values()) == sorted(kw2.values())'),
    ],
    "D1_F03": [
        ("last_source_wins", 'copy.deepcopy(values[0])', 'copy.deepcopy(values[-1])'),
        ("merge_when_first_is_mapping", 'all(isinstance(value, dict) for value in values)', 'isinstance(values[0], dict)'),
    ],
    "D1_F04": [
        ("round_float", 'int(item) if isinstance(item, float)', 'round(item) if isinstance(item, float)'),
        ("null_retries_use_default", 'if "retries" in value else', 'if value.get("retries") is not None else'),
    ],
    "D1_B01": [
        ("deduplicate", "sorted(value for group in expanded for value in group)", "sorted(set(value for group in expanded for value in group))"),
        ("exclude_endpoint", "max(bounds) + 1", "max(bounds)"),
    ],
    "D1_B02": [
        ("get_first", "pairs[indexes[-1]][1]", "pairs[indexes[0]][1]"),
        ("getall_last_only", "[pairs[i][1] for i in indexes]", "[pairs[i][1] for i in indexes[-1:]]"),
    ],
    "D1_M01": [
        ("omit_tail_windows", "stop = length if step >= n else length - n + step", "stop = length - n + 1"),
        ("omit_padding", "[fill] * max(0, i+n-length)", "[]"),
    ],
    "D1_M02": [
        ("split_equal", "items[index-1] > items[index]", "items[index-1] >= items[index]"),
        ("ignore_limit", "(limit < 0 or splits < limit)", "True"),
    ],
    "D1_C01": [
        ("fifo_get", "result = state[key]; state.move_to_end(key)", "result = state[key]"),
        ("contains_touches", "result = key in state", "result = key in state\n            if result: state.move_to_end(key)"),
    ],
    "D1_C02": [
        ("expiry_strict", "now >= expires[key]", "now > expires[key]"),
        ("get_extends_ttl", "result = state[key]; state.move_to_end(key)", "result = state[key]; state.move_to_end(key)\n                expires[key] = now + p['ttl']"),
    ],
    "D1_F01": [
        ("resplit_list", "return value[:]", "return [word for item in value for word in item.split()]"),
        ("omit_empty_unsplit", "else [value]", "else ([value] if value else [])"),
    ],
    "D1_F02": [
        ("deduplicate_keys", "return output", "return [list(pair) for pair in dict(output).items()]"),
        ("consume_mapping", "key = next(iter(item)); output.append([key, item[key]])", "key, val = item.popitem(); output.append([key, val])"),
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    for task_id, changes in MUTATIONS.items():
        directory = args.dataset / "private" / task_id
        source = (directory / "alternate.py").read_text(encoding="utf-8")
        for name, old, new in changes:
            assert old in source, (task_id, name)
            mutated = source.replace(old, new)
            compile(mutated, name, "exec")
            candidate = args.output / f"{task_id}_{name}.py"
            candidate.write_text(mutated, encoding="utf-8")
            result = evaluate(candidate, directory / "all_tests.json")
            rows.append({"task_id": task_id, "mutation": name,
                         "killed": not result["all_pass"], "result": result})
    summary = {"mutation_count": len(rows), "killed_count": sum(r["killed"] for r in rows),
               "scope": "每题手工设计2个具体语义缺陷；不是自动变异框架覆盖率", "rows": rows}
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"mutation_count": len(rows), "killed_count": summary["killed_count"],
                      "survivors": [{"task_id": r["task_id"], "mutation": r["mutation"]}
                                    for r in rows if not r["killed"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
