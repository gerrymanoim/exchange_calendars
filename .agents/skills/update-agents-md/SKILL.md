---
  name: update-agents-md
  description: Instructions for updating @AGENT.md file, including: updating the 'Repository Layout' section following the adding or removal of files or folders; updating the 'Technology Stack' section on changes to the pinned python version as defined in @.python-version.
---
# Update agents.md file

## Repository Layout
Update the 'Repository Layout' section to reflect the current layout. Remove all files and folders that are no longer present and add all new files and folders with the following IMPORTANT EXCEPTIONS:
- exclude all files and folders ignored by @.gitignore
- do not include the following files or folders:
    - @.gitignore
    - @.git
    - @.benchmarks
    - all files named `__init__.py`
- do not include files under the following directories (but do include the folders listed here and any folders under them):
    - @tests
    - @tests/resources
- represent all files in the @exchange_calendars directory that match the pattern `exchange_calendar_.{4}.py` with a single entry `exchange_calendar_<code>.py` and a comment that reads '# calendars for each exchange'.
- represent all files in @tests that match the pattern `test_.{4}_calendar.py` with a single entry `test_<code>_calendar.py` and a comment that reads '# test file for each calendar'.
List all folders before any files for any given hierarchal level.
If the purpose of a file or directory is not reasonably evident from its name then include a minimalist comment offering a top-line explanation.
The comment should:
- be placed alongside the file/directory name
- not cause the length of the full line (including folder/directory name and all whitespace) to exceed 100 characters.

## Pinned Python version
Update, if necessary, the 'python' field of the 'Technology Stack' table so that it indicates the pinned python version as defined in @.python-version.
