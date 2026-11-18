"""Turn a claude -p stream-json log into <name>_final.md and <name>_toolcalls.txt."""
import json, sys
from pathlib import Path

log = Path(sys.argv[1])
calls, final = [], ""
for line in log.read_text(encoding="utf-8").splitlines():
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    if ev.get("type") == "assistant":
        for block in ev["message"].get("content", []):
            if block.get("type") == "tool_use":
                calls.append(f"{block['name']}: {json.dumps(block['input'])[:300]}")
    if ev.get("type") == "result":
        final = ev.get("result", "")
        calls.append(f"# result: turns={ev.get('num_turns')} cost_usd={ev.get('total_cost_usd')} duration_ms={ev.get('duration_ms')}")
stem = str(log)[: -len(".jsonl")]
Path(stem + "_final.md").write_text(final, encoding="utf-8")
Path(stem + "_toolcalls.txt").write_text("\n".join(calls) + "\n", encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8"); print(final)
