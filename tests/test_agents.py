import json
import os
import shutil
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
STANDARD_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "missing frontmatter"
    keys = {}
    for line in m.group(1).splitlines():
        if line and not line.startswith(" "):
            k, _, v = line.partition(":")
            keys[k.strip()] = v.strip()
    return keys


class TestSkills(unittest.TestCase):
    def test_skills_use_only_standard_fields(self):
        dirs = sorted(d for d in SKILLS.iterdir() if d.is_dir())
        self.assertGreaterEqual(len(dirs), 6)
        for d in dirs:
            fm = frontmatter((d / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual(fm["name"], d.name)
            self.assertTrue(re.fullmatch(r"[a-z0-9-]{1,64}", fm["name"]))
            self.assertTrue(0 < len(fm["description"]) <= 1024)
            self.assertLessEqual(set(fm) - STANDARD_FIELDS, set(), d.name)

    def test_referenced_files_exist(self):
        for skill in SKILLS.glob("*/SKILL.md"):
            for ref in re.findall(r"`(references/[\w./-]+)`", skill.read_text(encoding="utf-8")):
                self.assertTrue((skill.parent / ref).exists(), f"{skill}: {ref}")

    def test_claude_skills_symlink(self):
        link = ROOT / ".claude" / "skills"
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), SKILLS.resolve())


class TestRoster(unittest.TestCase):
    def test_generated_agents_are_fresh(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_harnesses.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_roster_roles_have_prompts_and_valid_delegates(self):
        roster = json.loads((ROOT / "agents" / "roster.json").read_text())
        roles = roster["roles"]
        for role, spec in roles.items():
            self.assertTrue((ROOT / "agents" / f"{role}.md").exists(), role)
            for d in spec.get("delegates", []):
                self.assertIn(d, roles)
                self.assertNotIn("agent", roles[d]["tools"], "flat topology: workers must not spawn agents")
            for s in spec.get("skills", []):
                self.assertTrue((SKILLS / s / "SKILL.md").exists(), s)
        self.assertEqual([r for r, s in roles.items() if s.get("main")], ["orchestrator"])


if __name__ == "__main__":
    unittest.main()


class TestHarnessFiles(unittest.TestCase):
    def test_codex_toml_parses_with_required_fields(self):
        import tomllib
        files = sorted((ROOT / ".codex" / "agents").glob("*.toml"))
        self.assertTrue(files)
        for f in files:
            d = tomllib.loads(f.read_text(encoding="utf-8"))
            for k in ("name", "description", "developer_instructions"):
                self.assertTrue(d.get(k), f"{f.name}: {k}")

    def test_every_target_has_every_worker(self):
        roster = json.loads((ROOT / "agents" / "roster.json").read_text())
        workers = [r for r, s in roster["roles"].items() if not s.get("main")]
        for d, ext in ((".claude/agents", ".md"), (".codex/agents", ".toml"), (".gemini/agents", ".md"),
                       (".opencode/agents", ".md"), (".github/agents", ".agent.md")):
            for w in workers:
                self.assertTrue((ROOT / d / f"{w}{ext}").exists(), f"{d}/{w}{ext}")
        self.assertEqual(json.loads((ROOT / ".gemini" / "settings.json").read_text())["context"]["fileName"],
                         ["AGENTS.md"])


@unittest.skipUnless(shutil.which("uv") and os.environ.get("GT_TEST_MCP", "1") == "1", "uv not available")
class TestMcpServer(unittest.TestCase):
    def test_tools_prompts_and_a_call(self):
        import tempfile
        client = '''
# /// script
# dependencies = ["mcp>=1.2,<2"]
# ///
import asyncio, json, os, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
    p = StdioServerParameters(command="uv", args=["run", "--quiet", sys.argv[1]], env=dict(os.environ))
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = [t.name for t in (await s.list_tools()).tools]
            prompts = [p.name for p in (await s.list_prompts()).prompts]
            st = json.loads((await s.call_tool("get_state", {})).content[0].text)
            print(json.dumps({"tools": tools, "prompts": prompts, "state_ok": st["ok"]}))
asyncio.run(main())
'''
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            subprocess.run([str(ROOT / "bin" / "gt"), "init", "--no-git"], env=dict(os.environ, GT_HOME=str(home)),
                           capture_output=True, check=True)
            script = Path(tmp) / "client.py"
            script.write_text(client)
            r = subprocess.run(["uv", "run", "--quiet", str(script), str(ROOT / "gt_mcp.py")], capture_output=True,
                               text=True, timeout=240, env=dict(os.environ, GT_HOME=str(home)))
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertGreaterEqual(len(out["tools"]), 25)
        self.assertEqual(sorted(out["prompts"]), ["mentor", "new_path", "placement", "practice", "retro"])
        self.assertTrue(out["state_ok"])
