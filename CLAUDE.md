<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## OpenSpec Apply Workflow

When running `openspec apply`:
1. **Check for uncommitted changes** - Refuse to apply if the plan has uncommitted changes.
2. **Assess context needs** - Check remaining context window and read the plan complexity (tasks.md). If context is low (<50% remaining) or the plan is complex, recommend the user run `/clear` first and re-run the command.
3. Create a new git worktree with a branch named after the change-id (e.g., `git worktree add ../cardputer-<change-id> -b <change-id>`)
4. Change to the new worktree directory
5. Run `uv sync` to create the venv
6. Run `direnv allow` to enable the environment
7. Implement the changes there