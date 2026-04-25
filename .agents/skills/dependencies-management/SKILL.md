---
  name: dependencies-management
  description: instructions for updating and managing project dependencies (including Github actions).
---
# Dependencies Management

## Update Dependencies

Instructions to update project dependencies (including Github actions used by CI workflows).

### 1. Prepare the branch

Create a new branch (following the naming convention in @AGENTS.md).

### 2. Update the lock file and environment

Update `uv`:
```bash
uv self update --token $GITHUB_TOKEN
```

**IMPORTANT: updating `uv` MUST NOT be skipped.** If the above command fails (e.g. due to a GitHub API rate limit), try the following fallbacks in order until `uv --version` confirms the latest version is active on PATH:

**Fallback 1 — official install script** (preferred; replaces PATH binary directly):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env  # refresh current shell session
uv --version                 # verify PATH binary is now updated
```

**Fallback 2 — pip** (use only if `curl` is unavailable):

```bash
pip install --user --upgrade uv
uv --version   # check if PATH binary was updated
```

Once `uv` is up to date, run:

```bash
uv lock --upgrade  # update the lock file
uv export --format requirements-txt --no-emit-project --no-hashes --no-dev -o requirements.txt  # sync @requirements.txt with @uv.lock
uv sync --inexact  # update environment to match @uv.lock
```

### 3. Update GitHub Actions versions

For each `uses: <owner>/<repo>@<version>` entry across all files in `.github/workflows/`, retrieve the latest release tag by fetching the releases page with WebFetch:

```
url:    https://github.com/<owner>/<repo>/releases/latest
prompt: What is the latest release tag for this GitHub action?
```

In each case update the version pin to any more recent release. **Preserve the existing pinning style**, so if the current pin is a specific version such as `@v3.0.1`, update to the full latest version string, whilst if it's a major-version tag such as `@v4`, update to any new major-version tag (if the project no longer publishes a major-version tag then switch to the full semver).

### 4. Update pre-commit hook versions

For each `repo:` entry in `.pre-commit-config.yaml`, retrieve the latest release tag by fetching the releases page with WebFetch:

```
url:    https://github.com/<owner>/<repo>/releases/latest
prompt: What is the latest release tag for this pre-commit hook?
```

In each case update the `rev:` pin to any more recent release. **Preserve the existing pinning style**, so if the current pin is a specific version such as `v6.0.0`, update to the full latest version string, whilst if it's a major-version tag such as `@v4`, update to any new major-version tag (if the project no longer publishes a major-version tag then switch to the full semver).

### 5. Test

Run the test suite:
```bash
uv run pytest -v
```

**Interpret local test results:**
- All tests pass and no raised warning is fixable (see *Fixable warnings* section below) → go to step 7 to raise PR.
- Any test failure or a fixable warning raised → proceed to step 6 to fix.

### 6. Fix
Any failing tests and fixable warnings will likely have their origin in changes to the dependencies. To provide support for the latest dependencies MAKE REVISIONS to the code base to fix:
- code causing tests to fail.
- all fixable warnings (see *Fixable warnings* section below).

As a general RULE, **change the package code to get the tests passing, not the test code!** You may make changes to the test code only with good reason and only when this does not impair the test's efficacy.

To facilitate identifying the cause of test failures consider researching the changelogs of updated dependencies for versions released since the previously locked version.

Iterate on this process until:
- all tests are passing with the exception of any requiring unreachable services.
- all fixable warnings have been fixed.

IMPORTANT: in this step you should not run the full test suite, rather validate fixes by re-running only the previously failing tests. Example to run a specific test:

```bash
pytest tests/test_module.py::test_name
```

### 7. Raise PR

Once local tests pass, commit all changes to the branch and raise a PR.

- **PR title**: Title the PR as `Update Dependencies <MM> <DD> (auto)` where:
  - `<MM>` should be replaced with the first three letters of the current month, the first of which should be capitalized.
  - `<DD>` should be replaced with the current day of the month as represented by two digits.
  Example title: `Update Dependencies Apr 07 (auto)`
- **label**: Add the 'dependencies' label to the PR.

### 8. Subscribe to PR activity

By raising the PR a GitHub CI workflow will be triggered. Subscribe to the raised PR's activity.

Proceed to step 9 when you receive an event indicating that the triggered workflow has completed.

### 9. Inspect CI results

The CI workflow will have run the full test suite against a matrix of OS and Python versions. Use `mcp__github__pull_request_read` with the `get_check_runs` method to read check statuses for all matrix jobs.

**Interpret CI test results:**
- All checks green → proceed to step 12.
- Any check red → proceed to step 10.

### 10. Fix tests for specific OS/Python configuration

Use the information read from `get_check_runs` to identify any OS/python version configurations for which the test suite has failed.

If the tests failed on specific matrix combinations (e.g. Windows / Python 3.10) then simulate a local matching environment.
- If necessary use a Docker container with the target OS. (To specify different Python versions you will be able to run commands with `uv run` and pass the --python option.)
- create a new branch against the repository's master branch.
- update the `uv` package with `uv self update`.
- overwrite `uv.lock` with the version previously created by step 2.
- synchronise the environment by running `uv sync`.

Run the test suite to identify failing tests. For example:

```bash
uv run --isolated --python 3.11 python pytest --ignore=tests/test_yahoo.py -v
```

Then find fixes for the failing tests by following step 6.

Finally commit the necessary changes to your *original* branch (to which previous commits were made). This will trigger the CI on the PR re-run. Return to step 9 (inspect CI results).

### 11. Fallback: raise an issue

ONLY if any test failures cannot be resolved, raise an issue that references the PR and details:
- the failing tests
- any fixes already attempted
- any suggested next steps.

### 12. Tidy up

Perform the following 'tidy up' actions:
- Call `mcp__github__unsubscribe_pr_activity` to unscubscribe from the PR activity.
- Review and if necessary update the PR body to reflect the final circumstances.

---

**Fixable warnings**
The following warnings are considered UNFIXABLE and you should not attempt to fix them.
- warnings that have their origin in a dependency's code.
- `PricesMissingWarning`.

All other warnings are considered fixable.

## Adding dependencies
```bash
# Add a dependency
uv add <package>
```
