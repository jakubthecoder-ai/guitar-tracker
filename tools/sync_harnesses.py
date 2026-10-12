#!/usr/bin/env python3
"""Generate harness-native agent files from canonical prompts (agents/*.md + agents/roster.json).

Usage: python3 tools/sync_harnesses.py [--target claude] [--check]
Generated files must not be edited by hand. --check exits 1 when generated files are stale (for CI/tests).
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents"
HEADER = "<!-- GENEROWANE przez tools/sync_harnesses.py z agents/{role}.md – nie edytuj ręcznie. -->"

CONTRACT_NOTE = """
## Kontrakt
Wejście i wyjście: `.agents/skills/gt-core/references/contracts.md`. Odpowiedź kończ **jednym** blokiem
```json {"status": "ok|needs_input|error", ...}``` – orkiestrator parsuje tylko ten blok.
"""


def body_for(role: str, spec: dict) -> str:
    parts = [(AGENTS / "mentor.md").read_text(encoding="utf-8").strip(),
             (AGENTS / f"{role}.md").read_text(encoding="utf-8").strip()]
    if not spec.get("main"):
        parts.append(CONTRACT_NOTE.strip())
    return "\n\n".join(parts) + "\n"


def claude_tools(spec: dict) -> str:
    out = []
    for t in spec["tools"]:
        if t == "agent":
            out.append(f"Agent({', '.join(spec.get('delegates', []))})")
        elif t == "shell":
            out.append("Bash")
        elif t == "read":
            out += ["Read", "Glob", "Grep"]
        elif t == "ask":
            out.append("AskUserQuestion")
        elif t == "web":
            out += ["WebFetch", "WebSearch"]
    return ", ".join(out)


def render_claude(role: str, spec: dict, tiers: dict) -> str:
    fm = [
        "---",
        f"name: {role}",
        f"description: {json.dumps(spec['description'], ensure_ascii=False)}",
        f"tools: {claude_tools(spec)}",
        f"model: {tiers[spec['tier']]}",
    ]
    if spec.get("skills"):
        fm.append("skills:")
        fm += [f"  - {s}" for s in spec["skills"]]
    fm.append("---")
    return "\n".join(fm) + "\n" + HEADER.format(role=role) + "\n\n" + body_for(role, spec)


def _yaml_str(v: str) -> str:
    return json.dumps(v, ensure_ascii=False)


def render_codex(role: str, spec: dict, tiers: dict) -> str:
    body = body_for(role, spec).replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    lines = [f"# {HEADER.format(role=role)[5:-4]}", f"name = {_yaml_str(role)}",
             f"description = {_yaml_str(spec['description'])}"]
    for k, v in (tiers[spec["tier"]] or {}).items():
        lines.append(f"{k} = {_yaml_str(v)}")
    lines.append(f'developer_instructions = """\n{body}"""')
    return "\n".join(lines) + "\n"


def render_gemini(role: str, spec: dict, tiers: dict) -> str:
    fm = ["---", f"name: {role}", f"description: {_yaml_str(spec['description'])}", "kind: local"]
    if tiers.get(spec["tier"]):
        fm.append(f"model: {tiers[spec['tier']]}")
    fm += ["max_turns: 30", "---"]
    return "\n".join(fm) + "\n" + HEADER.format(role=role) + "\n\n" + body_for(role, spec)


def render_opencode(role: str, spec: dict, tiers: dict) -> str:
    fm = ["---", f"description: {_yaml_str(spec['description'])}",
          f"mode: {'primary' if spec.get('main') else 'subagent'}"]
    if tiers.get(spec["tier"]):
        fm.append(f"model: {tiers[spec['tier']]}")
    fm += ["permission:", "  task:", '    "*": deny']
    fm += [f"    {d}: allow" for d in spec.get("delegates", [])]
    fm.append("---")
    return "\n".join(fm) + "\n" + HEADER.format(role=role) + "\n\n" + body_for(role, spec)


def render_copilot(role: str, spec: dict, tiers: dict) -> str:
    tools = ["execute", "read", "search"] + (["agent"] if "agent" in spec["tools"] else [])
    fm = ["---", f"name: {role}", f"description: {_yaml_str(spec['description'])}",
          f"tools: [{', '.join(repr(t) for t in tools)}]"]
    if tiers.get(spec["tier"]):
        fm.append(f"model: {tiers[spec['tier']]}")
    if not spec.get("main"):
        fm.append("user-invocable: false")
    fm.append("---")
    return "\n".join(fm) + "\n" + HEADER.format(role=role) + "\n\n" + body_for(role, spec)


GEMINI_SETTINGS = {"context": {"fileName": ["AGENTS.md"]}}

# target -> (dir, ext, renderer, include main-thread role?)
TARGETS = {
    "claude": (ROOT / ".claude" / "agents", ".md", render_claude, True),
    "codex": (ROOT / ".codex" / "agents", ".toml", render_codex, True),
    "gemini": (ROOT / ".gemini" / "agents", ".md", render_gemini, False),  # main thread = AGENTS.md
    "opencode": (ROOT / ".opencode" / "agents", ".md", render_opencode, True),
    "copilot": (ROOT / ".github" / "agents", ".agent.md", render_copilot, True),
}


def generate(target: str) -> dict:
    roster = json.loads((AGENTS / "roster.json").read_text(encoding="utf-8"))
    out_dir, ext, render, with_main = TARGETS[target]
    tiers = roster["tiers"][target]
    files = {out_dir / f"{role}{ext}": render(role, spec, tiers) for role, spec in roster["roles"].items()
             if with_main or not spec.get("main")}
    if target == "gemini":
        files[ROOT / ".gemini" / "settings.json"] = json.dumps(GEMINI_SETTINGS, indent=2) + "\n"
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=sorted(TARGETS), action="append")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stale = []
    for target in args.target or sorted(TARGETS):
        for path, text in generate(target).items():
            if path.exists() and path.read_text(encoding="utf-8") == text:
                continue
            if args.check:
                stale.append(str(path.relative_to(ROOT)))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        print("stale: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
