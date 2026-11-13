"""Run paired model comparisons; human rubric scores deliberately remain blank."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import uuid

from backend.companion import AppError, Companion, Config, ROOT, TEMPERATURE, MAX_TOKENS, HISTORY_MESSAGES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--character", choices=("mira", "feiyu"), default="feiyu")
    parser.add_argument("--scenario", help="Run one scenario, for example F07 (feiyu) or M01 (mira)")
    parser.add_argument("--dry-run", action="store_true", help="Show counts without model calls")
    args = parser.parse_args()
    if not 1 <= args.repeats <= 10:
        parser.error("--repeats must be between 1 and 10")
    scenario_file = f"evaluation/scenarios/{args.character}.json"
    content_dir = f"content/{args.character}"
    cases = json.loads((ROOT / scenario_file).read_text(encoding="utf-8"))
    if args.scenario:
        cases = [case for case in cases if case["id"] == args.scenario]
        if not cases:
            parser.error("Unknown scenario")
    calls = sum(1 + len(c.get("setup", [])) for c in cases) * 2 * args.repeats
    print(f"{len(cases)} scenarios x 2 modes x {args.repeats} repeats; {calls} model calls including setup.")
    if args.dry_run:
        return
    config = Config.load()
    if config.provider == "deepseek" and not config.api_key:
        parser.error("Connect DeepSeek in the app first, or set DEEPSEEK_API_KEY in .env.")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
    output = ROOT / "evaluation/results" / run_id
    output.mkdir(parents=True)
    manifest = {"created_at": run_id, "character": args.character, "provider": config.provider, "model": config.model,
                "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "history_messages": HISTORY_MESSAGES,
                "repeats": args.repeats, "scenario_ids": [c["id"] for c in cases],
                "sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in [content_dir + "/character.json", content_dir + "/world.json", scenario_file, "backend/companion.py", "tools/evaluate.py"]}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    fields = ["scenario", "category", "repeat", "mode", "question", "expected", "answer", "latency_seconds",
              "retrieved_ids", "retrieval_hit", "model", "finish_reason", "lore_accuracy_0_2", "memory_accuracy_0_2", "character_consistency_0_2", "unknown_handling_0_2", "notes", "error"]
    failures = 0
    with tempfile.TemporaryDirectory(prefix=f"{args.character}-evaluation-") as temp, (output / "scores.csv").open("w", encoding="utf-8-sig", newline="") as csv_file, (output / "responses.jsonl").open("w", encoding="utf-8") as log:
        app = Companion(config, Path(temp) / "evaluation.sqlite", character_id=args.character)
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        for repeat in range(1, args.repeats + 1):
            for case in cases:
                # Alternate order to reduce a systematic mode/order effect.
                modes = ("baseline", "enhanced") if repeat % 2 else ("enhanced", "baseline")
                for mode in modes:
                    visitor = str(uuid.uuid4())
                    session = app.store.new_session(visitor, mode)
                    row = {"scenario": case["id"], "category": case["category"], "repeat": repeat, "mode": mode, "question": case["question"], "expected": case["expected"]}
                    setup_responses = []
                    try:
                        for message in case.get("setup", []):
                            setup_responses.append(app.chat(visitor, session["id"], message))
                        if case.get("new_session"):
                            session = app.store.new_session(visitor, mode)
                        result = app.chat(visitor, session["id"], case["question"])
                        meta = result["metadata"]
                        retrieved = [d["id"] for d in meta["retrieved"]]
                        expected_ids = set(case.get("lore_ids", []))
                        row.update(answer=result["answer"], latency_seconds=meta["latency_seconds"], retrieved_ids=";".join(retrieved),
                                   retrieval_hit=int(expected_ids.issubset(retrieved)) if expected_ids and mode == "enhanced" else "",
                                   model=meta["model"], finish_reason=meta["finish_reason"])
                        log.write(json.dumps({"scenario": case["id"], "repeat": repeat, "mode": mode, "setup": setup_responses,
                                              "result": result, "session": app.store.session(session["id"], visitor)}, ensure_ascii=False) + "\n")
                    except AppError as error:
                        row["error"] = str(error)
                        log.write(json.dumps({"scenario": case["id"], "repeat": repeat, "mode": mode, "error": str(error)}) + "\n")
                        failures += 1
                    writer.writerow(row); csv_file.flush(); log.flush()
                    print(f"{case['id']} repeat {repeat} {mode}: {'ERROR: ' + row['error'] if row.get('error') else 'saved'}", flush=True)
                    app.store.forget(visitor)
                    if failures >= 3:
                        print("Stopped after 3 failed requests. Fix the model connection before retrying.")
                        print(output)
                        return 1
    print(f"Saved to {output}. Human scores are blank; apply evaluation/RUBRIC.md.")
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
