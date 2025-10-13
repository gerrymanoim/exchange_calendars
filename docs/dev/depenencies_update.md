## **Workflow to update dependencies using uv**

- Set up new local 'deps' branch.
- Update `uv.lock` file and sync local environment to reflect latest dependencies:
    ```
    uv lock --upgrade
    uv sync
    ```
- Make sure tests passing locally with new dependencies.
- Export uv.lock to a requirements.txt file (to provide reference for non-uv clients).
    ```
    uv export --format requirements-txt --no-emit-project --no-hashes --no-dev -o requirements.txt
    ```
- Commit changes.
- Make PR to main branch.
