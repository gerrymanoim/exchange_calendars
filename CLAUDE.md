# Claude guide for `exchange-calendars` package

This file provides Claude (including Claude Code) with working context for this repository.

Read @AGENTS.md for all tool-agnostic knowledge of the repository (such as project architecture and conventions).

The remaining content of this file is intended only for Claude (including Claude Code).

Find skills under the @.agents/skills directory which serves as the directory you would have expected to find at `.claude/skills`.

Your name is Claude. Anywhere in the context that asks you to use your 'name' or 'colloquial name' or 'vernacular name' then you should use 'Claude'.

## Editing files with pre-granted permissions

`.claude/settings.json` pre-grants `Edit(...)` permission for a specific set of
files (e.g. `.pre-commit-config.yaml` and github workflows/*.yml` files). These
permissions only apply to the built-in`Edit` tool — they do not extend to the
`Bash` tool.

Some routines (e.g. the `dependencies-management` routine) are configured to run
automatically and unattended and in these cases a permission prompt would stall
the run. Therefore, when modifying any file covered by the `Edit(...)` permissions in
`.claude/settings.json`, **always use the `Edit` tool** (not `Bash`/`sed`/etc.) so
that the pre-granted permission applies and no prompt is raised.
