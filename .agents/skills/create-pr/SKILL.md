---
  name: create-pr
  description: Create a Pull Request, or write or update the body of one.
---
# Create a Pull Request

On creating any pull request, or on updating the body of one, do the following:
- **PR body**:
    - avoid minutiae.
    - lay the body out as the `pr-body-layout` skill defines.
    - if, and only if, the PR adds a new calendar or modifies an existing calendar, include the 'Workflows' section of the PR template (@.github/pull_request_template.md), without the template's comment; place the section immediately after the title and summary checkboxes, before the 'Agent autonomy' section.
    - tick a box of any 'Workflows' section only if the session saw every step of that box's workflow done; otherwise, leave the box unticked for the contributor to tick.
    - do not otherwise use the PR template, including within the folded detail.
