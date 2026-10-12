import json
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
