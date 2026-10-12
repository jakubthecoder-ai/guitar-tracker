# Cross-harness standards for shipping one skill set (and a multi-agent setup) to many AI coding-agent harnesses (as of 2026-10-12)

Scope: a harness-agnostic personal "guitar practice tracker" (skills, helper scripts, persistent state, persona). The primary harness is Claude Code. Secondary harnesses are Codex CLI, Gemini CLI, OpenCode, Cursor, GitHub Copilot and Claude Desktop/claude.ai via MCP. A scope addition covers the multi-agent design (orchestrator plus path subagents).

Source-quality note: most findings come from official vendor docs fetched on 2026-10-12. The Codex docs have moved from developers.openai.com/codex/* to learn.chatgpt.com/docs/* (HTTP 308 redirects), so older links in blogs are stale. Third-party "N agents support SKILL.md" counts disagree with each other and should be treated as approximate.

## 1. Agent Skills open standard (SKILL.md / agentskills.io): spec and native harness support

### Takeaway
SKILL.md is a stable, very small standard. Two fields are required (`name`, `description`), four are optional (`license`, `compatibility`, `metadata`, and the experimental `allowed-tools`). The suggested layout is `scripts/`, `references/` and `assets/`, loaded through three-level progressive disclosure. Every target harness reads it natively. The project-level directory that all of them read, except Claude Code, is `.agents/skills/`. Claude Code reads only `.claude/skills/`, and OpenCode, Cursor and Copilot also read `.claude/skills/`. So **`.claude/skills/` as the real directory plus a `.agents/skills` symlink** (or the reverse) covers everyone.

### Cited Findings
**Spec**
- A skill is a directory with a required `SKILL.md` and optional `scripts/` (executable code), `references/` (docs loaded on demand) and `assets/` (templates, images, data files). Any other files are also allowed. — [agentskills.io spec](https://agentskills.io/specification)
- Frontmatter rules: `name` is required, at most 64 characters, lowercase a-z, 0-9 and hyphens, with no leading, trailing or double hyphen, and it **must match the parent directory name**. `description` is required, 1-1024 characters, and should say what the skill does and when to use it. Optional fields are `license`, `compatibility` (at most 500 characters, environment requirements, e.g. "Requires Python 3.14+ and uv"), `metadata` (a string-to-string map) and `allowed-tools` (a space-separated string, "Experimental. Support ... may vary"). — [agentskills.io spec](https://agentskills.io/specification)
- Progressive disclosure has three levels: (1) name and description, about 100 tokens per skill, loaded at startup; (2) the SKILL.md body, recommended under 5000 tokens and under 500 lines, loaded on activation; (3) files in scripts/, references/ and assets/, loaded only when needed. File references should be relative to the skill root and only one level deep. — [agentskills.io spec](https://agentskills.io/specification)
- The `skills-ref validate ./my-skill` reference validator checks frontmatter and naming. — [agentskills.io spec](https://agentskills.io/specification)
- Scripts: "Supported languages depend on the agent implementation. Common options include Python, Bash, and JavaScript". Scripts should be self-contained or document their dependencies. — [agentskills.io spec](https://agentskills.io/specification)

**Claude Code** (primary)
- Locations: managed (enterprise), personal `~/.claude/skills/<name>/SKILL.md`, project `.claude/skills/`, nested `<subdir>/.claude/skills/`, `--add-dir` directories, plugin `<plugin>/skills/` (invoked as `/plugin-name:skill-name`), and claude.ai account skills synced to `~/.claude/skills/synced/`. **`.agents/skills/` is not listed.** — [Claude Code skills docs](https://code.claude.com/docs/en/skills)
- The memory docs state explicitly that Claude Code does not read "anything under a `.agents/` directory" for instructions. — [Claude Code memory docs](https://code.claude.com/docs/en/memory)
- Claude Code "follow[s] the open Agent Skills standard and extend[s] it". Extension fields:
  - invocation and arguments: `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`
  - tools: `allowed-tools`, `disallowed-tools`
  - model and execution: `model`, `effort`, `context: fork`, `agent`, `background`
  - other: `hooks`, `paths`, `shell`
  Unknown fields are ignored silently. — [Claude Code skills docs](https://code.claude.com/docs/en/skills)
- **Portability trap:** outside Claude Code (claude.ai uploads and the Skills API), only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools` are accepted. "Other fields cause an upload error." — [Claude Code skills docs](https://code.claude.com/docs/en/skills)
- Skills and slash commands are merged: `.claude/commands/x.md` and `.claude/skills/x/SKILL.md` both create `/x`, and the skill wins if both exist. — [Claude Code skills docs](https://code.claude.com/docs/en/skills)
- Substitutions: `$ARGUMENTS`, `$N`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`. `${CLAUDE_SKILL_DIR}` in `allowed-tools` lets bundled scripts run without permission prompts. Dynamic context injection with `` !`cmd` `` runs a shell command before the skill content reaches the model. — [Claude Code skills docs](https://code.claude.com/docs/en/skills)

**Codex (CLI, IDE, app)**
- Skill locations:
  - repo: `$CWD/.agents/skills`, plus the same path in each parent up to the repo root
  - user: `$HOME/.agents/skills`
  - admin: `/etc/codex/skills`
  - system: bundled skills
  Symlinked skill folders are followed. — [Codex "Build skills" docs](https://learn.chatgpt.com/docs/build-skills)
- `name` and `description` are required. Optional folders are `scripts/`, `references/`, `assets/` and `agents/`. An optional `agents/openai.yaml` holds `interface` (UI display), `policy.allow_implicit_invocation` (default true) and `dependencies.tools` (e.g. MCP servers). — [Codex "Build skills" docs](https://learn.chatgpt.com/docs/build-skills)
- Invocation: explicit with `$skill` or `/skills` in the CLI, or implicit by description match. The initial skill list is capped at 2% of the context window (or 8,000 characters); descriptions are shortened first and skills may be omitted. `$skill-installer` installs curated skills. Plugins are the recommended way to distribute bundles. — [Codex "Build skills" docs](https://learn.chatgpt.com/docs/build-skills)

**Gemini CLI**
- Skill tiers, lowest precedence first: built-in, then extension skills, then user (`~/.gemini/skills/` or the `~/.agents/skills/` alias), then workspace (`.gemini/skills/` or `.agents/skills/`). Within a tier, `.agents/skills/` beats `.gemini/skills/`. — [Gemini CLI skills docs](https://geminicli.com/docs/cli/skills/)
- Activation: the model calls the `activate_skill` tool. A **consent prompt** shows the skill name and the directory it will access, and on approval the body and folder structure are added and the directory becomes an allowed path. Management uses `/skills list|link|enable|disable|reload` and `gemini skills install <git-url|path> --scope user|workspace`. — [Gemini CLI skills docs](https://geminicli.com/docs/cli/skills/)

**OpenCode**
- Project: `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` (walking up to the git worktree root). Global: `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/`. — [OpenCode skills docs](https://opencode.ai/docs/skills/)
- Recognized fields: `name`, `description`, `license`, `compatibility`, `metadata`. OpenCode-specific options go under `metadata`: `opencode/slash` exposes the skill as a `/name` command, and `opencode/autoinvoke: "false"` hides it from auto-selection. The `name` and directory-match rules are enforced. Loading goes through a `skill({name})` tool, and `permission.skill` in opencode.json sets allow, ask or deny. — [OpenCode skills docs](https://opencode.ai/docs/skills/)

**Cursor**
- Project: `.agents/skills/` and `.cursor/skills/`. User: `~/.agents/skills/` and `~/.cursor/skills/`. **Compatibility paths:** `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, `~/.codex/skills/`. Nested folders are discovered. — [Cursor skills docs](https://cursor.com/docs/context/skills)
- Fields: `name`, `description`, `paths`, `disable-model-invocation`, `icon`, `color`, `metadata`. Invocation can be automatic, manual with `/` (one message only), or session-long as a "Custom Mode". — [Cursor skills docs](https://cursor.com/docs/context/skills)
- Conflict: one third-party guide claims Cursor has "partial, project-only" support — [agensi.io](https://www.agensi.io/learn/every-ai-agent-that-supports-skill-md-2026). The official Cursor docs list user-level paths, so the third-party claim looks outdated.

**GitHub Copilot**
- Project skills: `.github/skills`, `.claude/skills`, `.agents/skills`. Personal skills: `~/.copilot/skills`, `~/.agents/skills`. The page does not say which surface (cloud coding agent, CLI, VS Code) reads which path. — [GitHub Docs: About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)

**Ecosystem**
- Third-party reports say Anthropic published the format as an open spec in Dec 2025, and that about 32 tools read SKILL.md by March 2026 (about 40 on the agentskills.io showcase by June 2026). — [paperclipped.de](https://www.paperclipped.de/en/blog/agent-skills-open-standard-interoperability/), [agentman.ai](https://agentman.ai/blog/agent-skills-ecosystem-report-2026). These are secondary sources and the numbers are approximate.

### Inferences
- **Portable SKILL.md profile for this project:** use only `name`, `description`, `license`, `compatibility` and `metadata`. That set is accepted everywhere, including claude.ai upload. Put Claude-only behavior in the body as prose rather than in frontmatter, or accept that claude.ai uploads need a stripped copy.
- Avoid `allowed-tools` and `${CLAUDE_SKILL_DIR}` in shared skills, or use them knowing other harnesses ignore them or show them literally. Reference scripts as `scripts/foo.py` relative to the skill directory. All harnesses tell the model where the skill lives (Codex passes the file path, Gemini adds the directory to allowed paths).
- **Directory recipe:** keep canonical skills in `.agents/skills/<name>/` (read by Codex, Gemini, OpenCode, Cursor and Copilot) and symlink `.claude/skills -> ../.agents/skills` for Claude Code. The reverse also works, since OpenCode, Cursor and Copilot read `.claude/skills` directly. The `.agents` direction is needed for Codex and Gemini. Codex follows symlinked skill folders.
- For a personal tool that should work in every project, install at user level: `~/.agents/skills` plus a `~/.claude/skills/<name>` symlink.

### Gaps
- Whether Copilot's cloud coding agent, as opposed to Copilot CLI or VS Code, reads `.claude/skills` and `.agents/skills`: the docs do not distinguish surfaces.
- No official statement found on Claude Code adding `.agents/skills` support or planning to. The current docs list only `.claude/skills`.
- Exact Gemini CLI frontmatter validation: the skills page does not list fields.

## 2. AGENTS.md: scope, adoption, interaction with CLAUDE.md and GEMINI.md

### Takeaway
AGENTS.md is the de facto cross-tool instruction file, now stewarded by the Agentic AI Foundation under the Linux Foundation. **Claude Code v2.1.277+ reads AGENTS.md natively** when no CLAUDE.md exists. That is new and makes many 2025 "symlink CLAUDE.md" guides outdated. For mixed setups, the official pattern is a CLAUDE.md that contains `@AGENTS.md` followed by Claude-specific additions.

### Cited Findings
- AGENTS.md is a plain Markdown file at the repo root with no required headings. The nearest AGENTS.md in the directory tree wins, which supports nested files per subproject, and explicit user prompts override it. — [agents.md](https://agents.md/)
- Listed supporters include Codex, Jules, Aider, goose, opencode, Zed, Warp, VS Code, Devin, Junie, Amp, Cursor, RooCode, Gemini CLI, Kilo Code, the GitHub Copilot coding agent, Windsurf and Augment. The site claims "over 60k open-source projects". Governance: Agentic AI Foundation / LF Projects. — [agents.md](https://agents.md/)
- Gemini CLI needs `context.fileName` set to AGENTS.md in `.gemini/settings.json`; by default it reads GEMINI.md. Aider needs `read: AGENTS.md`. — [agents.md](https://agents.md/)
- Claude Code behavior:
  - It reads AGENTS.md "in place of CLAUDE.md" when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or above it.
  - `~/.claude/CLAUDE.md` and `.claude/rules/` still load alongside.
  - It does not read `AGENTS.local.md`, `AGENTS.override.md` or `.agents/`.
  - Requires v2.1.277+.

  — [Claude Code memory docs](https://code.claude.com/docs/en/memory)
- The **Project instructions** setting takes `claude-md-or-agents-md` (default), `claude-md-and-agents-md`, `claude-md` or `managed-only`. It is set through `pluginConfigs["cc-plugin-agents-md@builtin"].options.instructionFiles` in user settings only, because project settings are ignored for it. — [Claude Code memory docs](https://code.claude.com/docs/en/memory)
- Recommended sharing pattern: a CLAUDE.md that contains `@AGENTS.md` and then Claude-specific sections. A symlink `ln -s AGENTS.md CLAUDE.md` also works, with two caveats. Edit and Write refuse to write through the symlink, and on Windows a committed symlink checks out as a plain text file unless `core.symlinks` is set. `@` imports recurse up to 4 hops, and imports outside the project need one-time approval. — [Claude Code memory docs](https://code.claude.com/docs/en/memory)
- Hook difference: `InstructionsLoaded` hooks do not fire for an AGENTS.md read through the setting. They do fire when CLAUDE.md imports or symlinks it. — [Claude Code memory docs](https://code.claude.com/docs/en/memory)
- Gemini keeps GEMINI.md (always-on context) separate from skills (on demand). — [Gemini CLI skills docs](https://geminicli.com/docs/cli/skills/)

### Inferences
- Put the persona summary, the state-file locations and the "always run scripts, never edit state JSON by hand" rules in one AGENTS.md. Add `CLAUDE.md` with `@AGENTS.md` plus Claude-only notes, such as orchestrator and subagent usage. Add `GEMINI.md` with Gemini's own import syntax, or set `context.fileName: ["AGENTS.md","GEMINI.md"]`.
- Keep AGENTS.md short (Claude docs suggest under 200 lines for memory files). Detailed workflows belong in skills.

### Gaps
- GEMINI.md `@file` import syntax was not re-verified in this session. It was known in 2025 and should be checked against current Gemini CLI docs.
- Whether Copilot reads AGENTS.md as custom instructions in every surface (agents.md lists only "GitHub Copilot coding agent").

## 3. MCP as a portable tool/state layer vs plain CLI scripts

### Takeaway
MCP is the only option that reaches **Claude Desktop and claude.ai**, which cannot run local shell scripts from a repo. It also gives typed tools and prompts (user-invoked, slash-command-like) that work across clients. CLI scripts called via shell are simpler, work in every coding harness with zero configuration, and fit skills naturally. Recommended: put the core logic in one Python module, expose it both as a CLI (for skills) and as a thin MCP server (for Desktop/claude.ai and for clients that prefer typed tools).

### Cited Findings
- MCP prompts are "user-controlled", "typically ... triggered through user-initiated commands", for example **as slash commands**. They support `prompts/list` and `prompts/get` with typed `arguments`, may embed resources, and send `listChanged` notifications. The spec version is 2025-11-25. — [MCP spec: Prompts](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts)
- The MCP site's docs index now points to a `2026-07-28` docs version, so a newer spec revision may exist than the 2025-11-25 prompts page. It names Claude, ChatGPT, VS Code, Cursor and others as clients, and mentions "MCP Apps" (interactive apps inside AI clients). — [modelcontextprotocol.io](https://modelcontextprotocol.io/clients)
- Codex skills can declare MCP dependencies in `agents/openai.yaml` (`dependencies.tools`). — [Codex "Build skills" docs](https://learn.chatgpt.com/docs/build-skills)
- Claude Code and Gemini subagents can scope MCP servers per agent (`mcpServers`). — [Claude Code subagents](https://code.claude.com/docs/en/sub-agents), [Gemini subagents](https://geminicli.com/docs/core/subagents/)
- Copilot custom agents accept `mcp-servers`, but it is "not used in VS Code or other IDE custom agents", and Claude Code `stdio` maps to `local`. — [GitHub Docs: custom agents config](https://docs.github.com/en/copilot/reference/custom-agents-configuration)

### Inferences
- **MCP pros:**
  - Typed schemas, so there is no shell-quoting fragility.
  - Works in Claude Desktop and claude.ai through connectors, plus every CLI harness.
  - No permission prompt for each bash command.
  - State access is centralized, which prevents concurrent-write corruption when several subagents run.
  - Prompts give pseudo-slash-commands such as `/log-session` in clients that surface them.
- **MCP cons:**
  - Each harness needs its own config file (`.mcp.json`, `~/.codex/config.toml`, `.gemini/settings.json`, `opencode.json`, `.cursor/mcp.json`, `.vscode/mcp.json`), which a sync tool like rulesync can generate.
  - A process to run.
  - Tool descriptions consume context in every session even when unused, whereas skills load progressively.
  - Remote use from claude.ai needs a hosted HTTPS server; it cannot reach local files.
- **CLI pros:**
  - Zero configuration; works anywhere bash works.
  - Easy for the user to run by hand and to test.
  - Plays perfectly with SKILL.md `scripts/`.
- **CLI cons:**
  - Permission prompts.
  - Quoting issues.
  - Not available in claude.ai or Desktop chat.
- Good split: a `tracker` CLI (`tracker log`, `tracker due`, `tracker goal set`) as the single source of truth, plus an optional `tracker mcp` subcommand (e.g. the Python `mcp` SDK in a uv script) that wraps the same functions.

### Gaps
- An authoritative per-client matrix of MCP feature support (prompts and resources in Codex, Gemini CLI, OpenCode, Cursor, Copilot) was not retrievable. The clients page fetched gave only a general overview. Verify per harness before relying on MCP prompts as slash commands. From memory and unverified: Claude Code shows MCP prompts as `/mcp__server__prompt`, and Gemini CLI also exposes them as slash commands.

## 4. How real projects ship one skill set to many harnesses

### Takeaway
Two working patterns exist. (a) **One canonical `skills/` directory plus thin per-harness plugin manifests** (obra/superpowers ships to about 16 harnesses this way). (b) **One `.rulesync/` source plus a generator** that writes each harness's native files (rulesync, about 70 targets). For a personal project, the simplest robust choice is (a) without marketplace publishing: canonical `.agents/skills`, symlinks, and optionally a rulesync step for subagents and MCP configs.

### Cited Findings
- **obra/superpowers layout:**
  - shared content: `skills/`, `hooks/`, `scripts/`, `tests/`, `docs/`, `assets/`
  - per-harness folders: `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.opencode/`, `.agents/plugins/`, `.pi/extensions/`, and others
  - root files: `gemini-extension.json`, `GEMINI.md`, `AGENTS.md`
  - `scripts/bump-version.sh` with `.version-bump.json` keeps versions in sync

  Installs per harness: Claude Code `/plugin install superpowers@claude-plugins-official`; Codex CLI `/plugins`; Cursor `/add-plugin superpowers`; Gemini `gemini extensions install https://github.com/obra/superpowers`; Copilot CLI `copilot plugin marketplace add obra/superpowers-marketplace`; OpenCode by following `.opencode/INSTALL.md`. — [obra/superpowers](https://github.com/obra/superpowers)
- **rulesync:**
  - A Node CLI that generates rules, commands, MCP, ignore/permissions, subagents and skills for about 70 tools from `.rulesync/`, configured in `rulesync.jsonc`.
  - Commands: `rulesync init`, `rulesync generate --targets "*" --features "*"`, `rulesync import --targets claudecode`, `rulesync convert --from cursor --to copilot,claudecode`.
  - Version 14.x as of 2026.
  - The per-target feature matrix is in the [supported-tools reference](https://rulesync.dyoshikawa.com/reference/supported-tools).

  — [dyoshikawa/rulesync](https://github.com/dyoshikawa/rulesync)
- **Vercel `skills` CLI / skills.sh:** `npx skills add owner/repo [--skill name] [-a agent] [-g]` installs SKILL.md folders into agent-specific directories. The official docs say 18+ agents; third-party pages say 40+. — [Vercel docs](https://vercel.com/docs/agent-resources/skills), [skills.sh](https://skills.sh/agent/claude-code)
- Gemini `gemini skills install <git-url>` and Codex `$skill-installer` can install straight from a git repo. — [Gemini skills](https://geminicli.com/docs/cli/skills/), [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- Example of a harness-neutral repo of skills plus subagents for Claude Code, Copilot CLI, opencode, pi, Codex and Cursor: [barnuri/harness-skills](https://github.com/barnuri/harness-skills). Not inspected in detail.

### Inferences
Suggested repo layout:
```
guitar-tracker/
  AGENTS.md                      # canonical always-on instructions + persona summary
  CLAUDE.md                      # "@AGENTS.md" + Claude-only orchestration notes
  GEMINI.md                      # import of AGENTS.md (or context.fileName setting)
  .agents/skills/<skill>/SKILL.md, scripts/, references/, assets/
  .claude/skills -> ../.agents/skills   (symlink)
  agents/                        # canonical persona/subagent prompts (harness-neutral md)
  .claude/agents/*.md            # generated (Claude/Cursor read these)
  .codex/agents/*.toml           # generated
  .gemini/agents/*.md            # generated
  .opencode/agents/*.md          # generated
  .github/agents/*.agent.md      # generated
  tracker/ (core python package / uv script) + mcp server entry
  data/  (state: JSON/SQLite/markdown)
  tools/sync_agents.py           # tiny generator (or use rulesync)
```

### Gaps
- The exact rulesync source subfolder names and its subagent/skills support per target were not read. See its supported-tools page.
- Claude Code plugin marketplace manifest details (`.claude-plugin/plugin.json`, `marketplace.json`) were not re-fetched in this session.

## 5. Persona handling (portable persistent persona)

### Takeaway
No single agent-definition format exists. Every harness uses "Markdown body = system prompt + YAML/TOML frontmatter", but field names and directories differ, and Codex uses TOML. The portable approach is to keep the persona as plain Markdown, include a short version in AGENTS.md (always on), and generate per-harness agent files from it. Cursor reads `.claude/agents` and `.codex/agents` directly, which reduces the work.

### Cited Findings
- **Claude Code** can run the whole session as an agent persona with `claude --agent <name>` or `"agent": "<name>"` in `.claude/settings.json`. A non-empty custom prompt replaces the default system prompt, CLAUDE.md still loads, and `initialPrompt` runs as the first turn. — [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- **OpenCode** primary agents (`mode: primary`) are switchable with Tab, which suits a persona. — [OpenCode agents](https://opencode.ai/docs/agents/)
- **Cursor:** a skill can be used as a session-long "Custom Mode". — [Cursor skills](https://cursor.com/docs/context/skills)
- **Copilot:** custom agents have a prompt body of up to 30,000 characters, `user-invocable` and `disable-model-invocation` fields, and a `target` of vscode or github-copilot. — [GitHub Docs](https://docs.github.com/en/copilot/reference/custom-agents-configuration)

### Inferences
- Persona = `agents/mentor.md` (canonical) → generated as the Claude main-thread agent (`settings.json "agent": "mentor"`), the OpenCode primary agent, the Copilot custom agent and the Codex custom agent. Also keep a 5-10 line "voice" block in AGENTS.md so harnesses without agent support (or claude.ai through an MCP prompt) still get the persona.
- In claude.ai and Desktop, deliver the persona as an MCP prompt (`/mentor`) or as a Project instruction.

### Gaps
- Codex has no documented "main-thread persona" equivalent to `--agent`. AGENTS.md is the fallback.

## 6. Script language choice for portability

### Takeaway
Use **Python stdlib-only scripts** as the baseline: Python is near-universal and all harnesses can run it, with no install step. If dependencies are needed (e.g. the MCP SDK), use **uv single-file scripts with PEP 723 inline metadata** and the `#!/usr/bin/env -S uv run --script` shebang. Avoid bash for logic (Windows and quoting problems). Node only makes sense if the user already lives in JS.

### Cited Findings
- The spec lists Python, Bash and JavaScript as common script languages, and scripts should be self-contained or document dependencies. — [agentskills.io spec](https://agentskills.io/specification)
- uv inline metadata:
  - The `# /// script` TOML block holds `requires-python` and `dependencies`.
  - `uv add --script`; the shebang `#!/usr/bin/env -S uv run --script`.
  - `uv lock --script` writes `script.py.lock`.
  - `[tool.uv] exclude-newer` gives reproducibility.
  - uv downloads a matching Python if one is missing.

  — [uv scripts guide](https://docs.astral.sh/uv/guides/scripts/)
- The `compatibility` frontmatter field is the intended place to declare "Requires Python 3.x and uv". — [agentskills.io spec](https://agentskills.io/specification)

### Inferences
- Tracker core: stdlib (json/sqlite3/argparse/datetime). An MCP wrapper as a separate uv script that depends on `mcp`. Emit JSON on stdout for agents and use clear exit codes. Use atomic file writes (write to a temp file, then rename) so parallel subagents cannot corrupt state.

### Gaps
- None material.

## 7. Multi-agent architecture (scope addition): orchestrator plus path subagents across harnesses

### Takeaway
Every target harness except Claude Desktop/claude.ai now has file-defined subagents with **per-agent model selection**. Formats diverge:
- Markdown + YAML: Claude, Gemini, OpenCode, Cursor, Copilot
- TOML: Codex

Nesting rules also diverge:
- Claude allows nesting 3 levels deep by default
- Cursor allows 1 extra level
- Gemini allows none
- Codex is undocumented

Codex only spawns subagents when explicitly asked or when an instruction says to. A flat "orchestrator → workers" topology with **file-based state and explicit JSON handoff contracts** is the portable design. Workers re-read state from disk and return a structured summary.

### (a) Subagent definitions per harness — Cited Findings
- **Claude Code**:
  - Locations: `.claude/agents/*.md` and `~/.claude/agents/` (recursive), plugin `agents/`, and session-only JSON through `--agents`.
  - Required fields: `name`, `description`.
  - Optional fields: `tools`, `disallowedTools`, `model` (sonnet, opus, haiku, fable, a full ID, or inherit), `permissionMode`, `maxTurns`, `skills` (full content preloaded, up to 32), `mcpServers`, `hooks`, `memory` (user, project or local → `~/.claude/agent-memory/<name>/`, `.claude/agent-memory/<name>/`, `.claude/agent-memory-local/<name>/`; MEMORY.md injected, first 200 lines or 25KB), `background`, `effort`, `isolation: worktree`, `omitClaudeMd`, `initialPrompt`, `color`.
  - Unknown fields are ignored.

  — [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- **Codex**:
  - One TOML file per agent in `.codex/agents/` or `~/.codex/agents/`.
  - Required fields: `name`, `description`, `developer_instructions`.
  - Optional: any config.toml key, e.g. `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`.
  - Built-in agents: `default`, `worker`, `explorer`.
  - `[agents]` config keys: `enabled`, `max_concurrent_threads_per_session` (`max_threads` is a legacy alias), `default_subagent_model`, `default_subagent_reasoning_effort`.

  — [Codex subagents docs](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)
- **Gemini CLI**:
  - Locations: `.gemini/agents/*.md` and `~/.gemini/agents/*.md`.
  - Fields: `name`, `description`, `kind` (local or remote via A2A), `tools` (wildcards such as `mcp_*`), `mcpServers`, `model` (default inherit), `temperature`, `max_turns` (30), `timeout_mins` (10).
  - Enabled by default; disable with `experimental.enableAgents: false`.
  - Force a subagent with `@name`; manage with `/agents`.

  — [Gemini CLI subagents](https://geminicli.com/docs/core/subagents/)
- **OpenCode**:
  - Locations: `.opencode/agents/*.md` and `~/.config/opencode/agents/`, or the `agent` key in opencode.json. The filename is the agent name.
  - Fields: `description` (required), `mode: primary|subagent|all`, `model: provider/model-id`, `temperature`, `permission` (`tools` is deprecated), `prompt` (path to a file), `steps`, `hidden`.
  - `permission.task` with globs controls which subagents an agent may call through the Task tool.
  - Subagents use the caller's model unless they set their own.

  — [OpenCode agents](https://opencode.ai/docs/agents/)
- **Cursor**:
  - Locations: `.cursor/agents/` **plus `.claude/agents/` and `.codex/agents/` compatibility** (user-level equivalents too).
  - Fields: `name`, `description`, `model` (default inherit, with bracket parameters like `effort=high`), `readonly`, `is_background`.
  - Admins or plan limits may override the model.

  — [Cursor subagents](https://cursor.com/docs/context/subagents)
- **GitHub Copilot**:
  - Custom agent profiles are Markdown with frontmatter.
  - Fields: `name`, `description` (required), `target`, `tools` (aliases such as `execute`, `read`, `edit`, `search`, `agent`, `web`, `todo`, and `server/*` for MCP), `model`, `disable-model-invocation`, `user-invocable`, `mcp-servers`. `infer` is retired.
  - The `agent` tool alias lets one custom agent invoke another.
  - Whether `model` is honored per surface is not documented.

  — [GitHub Docs: custom agents config](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- **Common format / sync:** no formal standard. rulesync generates "subagents" for many targets from `.rulesync/`. — [rulesync](https://github.com/dyoshikawa/rulesync). The superpowers repo has no top-level `agents/` dir in its current layout; it focuses on skills. — [obra/superpowers](https://github.com/obra/superpowers)

### (b) Model tiering and harness limits — Cited Findings
- **Claude:**
  - Model resolution: per-invocation `model`, then frontmatter, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main model. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` forces it.
  - **Subagents can spawn subagents up to depth 3 by default** (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`; 1 disables). This changed from 2025, when subagents could not nest, so older advice is outdated.
  - Context isolation: a fresh context with its own system prompt and no parent history; CLAUDE.md and preloaded skills load; only the final summary returns.
  - Background subagents run concurrently with a reduced toolset (no Agent tool). `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` defaults to 20.
  - Resume a subagent with `SendMessage`.
  - The `Agent(worker, researcher)` tools syntax restricts which subagents a main-thread agent may spawn.
  - "Fork" subagents inherit the full context.

  — [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- **Codex:**
  - Resolution: explicit spawn value, then the `[agents]` default, then the parent.
  - Setting only `model` keeps the previously resolved effort, so set `model_reasoning_effort` as well.
  - Codex spawns locally only "after a direct request or an applicable project or skill instruction", waits for all results and returns one consolidated response.
  - Subagents inherit the sandbox and approvals.

  — [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)
- **Codex community claims (unverified):** "agents can't be spawned by name" and `max_depth`/`job_max_runtime_seconds` exist. — [danielvaughan.com](https://codex.danielvaughan.com/2026/04/27/codex-cli-custom-agent-definitions-toml-specialised-subagents/). These conflict with or are not covered by the official docs; treat as unverified.
- **Gemini:** "Subagents cannot call other subagents", even with the `*` tool wildcard. — [Gemini subagents](https://geminicli.com/docs/core/subagents/)
- **Cursor:**
  - Nesting since 2.5, but only the main agent and its direct children can launch subagents.
  - Several Task calls in one message run in parallel.
  - Subagents share the checkout unless isolated (worktree or cloud VM).

  — [Cursor subagents](https://cursor.com/docs/context/subagents)

### (c) Orchestrator-worker with file-based state — Inferences (design synthesis, no single source)
- **Topology:** orchestrator (main thread, Opus, high effort; in Claude it is the `--agent orchestrator` main-thread agent with `tools: Agent(tracker, planner, exercise-gen, retro, interviewer, song-recommender), Read, Bash`) → flat workers (`model: sonnet` or `haiku`). Do not depend on nesting, because Gemini forbids it and Cursor limits it.
- **State layout:**
  - `data/paths/<path-id>/` holds `goal.json`, `plan.json`, `log.jsonl` and `notes.md`.
  - `data/profile.json` holds skill level and genre.
  - `data/schedule.json` holds the orchestrator's interleaving and spaced-repetition queue.
  - Only the `tracker` CLI writes these, atomically. Workers never hand-edit JSON.
- **Handoff contract (orchestrator → worker), in the delegation prompt as JSON:** `{task, path_id, as_of_date, inputs:{...}, constraints:{time_budget_min, focus}, output_schema_ref}`.
- **Worker → orchestrator:** a single fenced JSON block, e.g. `{status: ok|needs_input|error, path_id, actions_taken:[cli commands run], state_changes:[...], summary_for_user, next_suggested:[...]}`. Define these schemas in `references/contracts.md` inside a shared skill. Each worker's prompt starts with "Re-read `data/paths/<id>/*` via `tracker show <id> --json` before acting; assume no memory of prior runs."
- **Stateless workers:** do not rely on Claude-only `memory:` frontmatter for core state, because it is not portable. State lives in `data/`. Optionally use `memory: project` only for mentor style learnings.
- **Concurrency:** parallel workers should touch disjoint paths. The CLI uses file locks or atomic rename, or the MCP server serializes writes.
- **Codex quirk:** state in AGENTS.md or the orchestrator skill that "for each practice path, spawn the `<name>` agent". Codex spawns only on an explicit instruction.

### (d) Fallback for harnesses without (usable) subagents
- **Cited:**
  - Claude Code headless: `claude -p` with `--agents <json-or-file>` (file form in v2.1.281+) and `--agent <name>` for the main thread. — [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
  - `codex exec` (alias `codex e`) is non-interactive, streams to stdout or JSONL, can resume sessions, starts read-only by default, and `--full-auto` allows writes. — [Codex CLI reference](https://developers.openai.com/codex/cli/reference), [danielvaughan.com](https://codex.danielvaughan.com/2026/04/18/codex-cli-headless-batch-mode-automation/)
  - Gemini headless: `gemini -p "..." -m <model> --output-format json -y`. — [smithery.ai skill page](https://smithery.ai/skills/melodic-software/gemini-cli-execution) (secondary source)
  - A cross-harness wrapper, `agents run` (agents-cli), drives Claude, Codex, Gemini, Cursor and OpenCode. — [skillsmp.com](https://skillsmp.com/creators/phnx-labs/agents-cli/skills-run) (secondary source)
- **Inferences:**
  - Keep each worker's prompt as plain Markdown (`agents/<name>.md`) so it can be (1) generated into native subagent files, (2) inlined as "act as <role> now; follow agents/<name>.md" in a single-agent harness or claude.ai, or (3) run as a shell subprocess, e.g.
    - `claude -p --model haiku --append-system-prompt "$(cat agents/tracker.md)" "<task JSON>"`
    - `codex exec -m <model> "<prompt>"`
    - `gemini -p ... -m <model>`
  - The worker returns the same JSON contract on stdout. A small `tools/run_worker.py` can pick the CLI by detecting which one is installed.
  - claude.ai and Desktop have no subagents. The orchestrator runs inline and calls the MCP tools directly.

### Gaps
- The exact `codex exec` model flag (`-m`) and `opencode run --agent/--model` syntax were not verified against official docs in this session. They are believed to exist but should be confirmed.
- Whether Codex subagents can nest, and how a named custom agent is chosen at spawn time, is not documented officially.
- Copilot: whether `model` in custom agents is honored on the cloud coding agent, and whether Copilot reads `.claude/agents`.
- Cost and latency comparisons of tiering, such as real savings of Haiku workers versus an Opus orchestrator, were not researched.
