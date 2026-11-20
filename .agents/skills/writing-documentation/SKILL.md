---
name: writing-documentation
description: Style and grammatical structure of all documentation - docstrings (tests' docstrings included), comments and markdown files. Use whenever writing or revising any documentation, including the docstrings and comments of code being added or changed.
---
# Writing documentation

## The aim

Documentation is written to be understood on a single reading. The failure
to avoid is compression: prose that reads as polished but leaves the reader
to infer a missing verb, which of several things a word refers to, or how
one part of a sentence bears on another. Compression is an agent's strong
default. This skill exists to counter it.

The skill has two parts:
- the core rules, which always apply. Each core rule forbids a construction
  that leaves the reader to rebuild a sentence or that admits a second
  reading.
- the guidance, which describes what usually reads best.

The aim overrides the guidance. If following a guide would make a sentence
harder to read, write the sentence that reads best and that still admits
only one reading. A departure from the guidance makes prose more explicit,
never more compressed.

This skill concerns how a thing is said. For what to document, and for how
to format documentation (docstring convention, line lengths), see the
project's AGENTS.md. A rule against bloat concerns what is documented and
does not license compression: where making the structure of a sentence
explicit takes more words, use more words.

## Applying the skill

- Apply both the core rules and the guidance to new text, including new
  text that is added to existing documentation.
- When revising existing text, apply only the core rules, and change only
  the passages that are being revised for another reason.

## Core rules

To keep each core rule from being applied more widely than it is meant to
be, the rule is followed by what it still allows. In the examples, the
version that follows the rule is one rewrite of the version that breaks it.
Any rewrite that follows the rule is acceptable, and the guidance describes
which usually reads best.

### 1. Give every claim its own verb

Do not leave a second claim to borrow its verb from a neighbouring clause.
This applies equally to a list item that makes a claim.

```text
Breaks the rule:
    The key is the user ID, the value the session token.
Follows the rule:
    The key is the user ID. The value is the session token.
```

```text
Breaks the rule:
    The file is overwritten if `force` is True and, if False, left
    unchanged.
Follows the rule:
    If `force` is True, the file is overwritten. If `force` is False, the
    file is left unchanged.
```

The rule allows a verbless phrase that only qualifies the sentence's one
claim. It also allows the two constructions that docstring convention
exempts: the summary line (for example "Cache of the parsed rows.") and the
noun phrase that opens the description of a parameter or attribute.

```text
Allowed:
    The price and the volume are both stored, the former in pence.
```

### 2. Carry no reason or fact in an absolute construction or in a participial phrase whose subject is not the subject of the main clause

An absolute construction is a noun with a participle of its own, for
example "the file having been closed" or "with the value being None".
Write the reason or the fact as a clause with its own verb.

```text
Breaks the rule:
    No retry is attempted for a 4xx response, a repeated request
    receiving the same response.
Follows the rule:
    No retry is attempted for a 4xx response (as a repeated request
    would receive the same response).
```

```text
Breaks the rule:
    The method returns the rows in order, the header row being excluded.
Follows the rule:
    The method returns the rows in order. The header row is excluded.
```

```text
Breaks the rule:
    The state is restored from the snapshot that precedes the last
    checkpoint, being the latest state known to be complete.
Follows the rule:
    The state is restored from the snapshot that precedes the last
    checkpoint. That snapshot is the latest state known to be complete.
```

The rule allows a participial phrase whose subject is the subject of the
main clause.

```text
Allowed:
    The function parses the file, returning None if the file is empty.
```

### 3. Write no reference that a reader could take two ways

Every pronoun, demonstrative ("this", "that") and "which" refers to exactly
one thing. The test is whether a reader could take the word to refer to
something else, not whether grammar alone permits another reading. If a
reader could, repeat the noun or restructure the sentence.

```text
Breaks the rule:
    The client sends the request to the server once it is ready.
Follows the rule:
    Once the server is ready, the client sends it the request.
```

```text
Breaks the rule:
    The writer flushes the buffer and compresses the file. This reduces
    the space that the file takes on disk.
Follows the rule:
    The writer flushes the buffer and compresses the file. Compressing
    the file reduces the space that the file takes on disk.
```

The rule allows a pronoun whose referent is clear from the sense.

```text
Allowed:
    When the parser reads a token it checks whether it matches the
    pattern.
```

### 4. Never introduce a purpose with ", such that"

A purpose is the aim that an act or a choice serves. A consequence is what
follows from a statement, regardless of whether anyone aims at it. To tell
the two apart, ask whether the outcome is why the act is done or why the
choice is made. If it is, the outcome is a purpose. Introduce a purpose
with "so that" or "to".

```text
Breaks the rule:
    A copy of the file is kept, such that the edit can be undone.
Follows the rule:
    A copy of the file is kept so that the edit can be undone.
```

```text
Breaks the rule:
    Each record is keyed by its timestamp, such that records from
    different files can be merged.
Follows the rule:
    Each record is keyed by its timestamp to allow records from different
    files to be merged.
```

The rule allows ", such that" to introduce a consequence.

```text
Allowed:
    Periods are measured in calendar days, such that a period of seven
    days holds only five working days.
```

### 5. Never introduce a condition on a particular thing with "where"

Introduce such a condition with "if".

```text
Breaks the rule:
    Where the connection is closed, the request is retried.
Follows the rule:
    If the connection is closed, the request is retried.
```

```text
Breaks the rule:
    The entry is refetched where it is older than `max_age`.
Follows the rule:
    The entry is refetched if it is older than `max_age`.
```

The rule allows "Where" to open a sentence that states what holds for any
member of a class.

```text
Allowed:
    Where a column holds no values, the column is dropped.
```

### 6. Never split the main clause with an aside that holds a clause

Keep the subject, verb and complement of the main clause together. Put the
aside after the main clause, where the reader can skip the aside. The main
clause should read as complete if the aside is removed.

```text
Breaks the rule:
    The file is, as several processes write to it and no process may
    overwrite what another has written, opened in append mode.
Follows the rule:
    The file is opened in append mode (as several processes write to the
    file, and no process may overwrite what another has written).
```

```text
Breaks the rule:
    The first argument, the path, which must be relative, is resolved
    against the root, the directory that holds the config file.
Follows the rule:
    The first argument is the path, which must be relative. The path is
    resolved against the root (i.e. the directory that holds the config
    file).
```

The rule concerns only an aside that holds a clause of its own.

### 7. Never introduce a reason with ", as"

After a comma, "as" leads the reader to expect something new rather than
an explanation of what came before. Introduce a reason with "because", or
put the reason in a parenthesis that opens with "as". A parenthesis shows
that what it holds clarifies what came before.

```text
Breaks the rule:
    Each request is given a new connection, as connections are not
    thread-safe.
Follows the rule:
    Each request is given a new connection (as connections are not
    thread-safe).
```

```text
Breaks the rule:
    The configuration must be loaded before the server starts, as the
    server reads the configuration only once.
Follows the rule:
    The configuration must be loaded before the server starts because
    the server reads the configuration only once.
```

The rule allows "as" in its other senses.

```text
Allowed:
    The report gives each account's balance, as at the close of business.
```

## Guidance

### Name how the parts of a sentence relate

If one part of a sentence bears on another, introduce that part with a
connective that names the relationship. Do not leave the relationship to be
inferred from a comma or from a bare parenthesis.

| Relationship | Connectives |
|---|---|
| reason | because; "as" opening a parenthesis |
| purpose | so that, to |
| consequence | such that; therefore or hence, within a parenthesis |
| condition | if, otherwise |
| concession | although |
| indifference | regardless of whether, whether or not |
| contrast | whilst, whereas |

A dash, written as a spaced hyphen (" - "), may instead introduce a clause
that explains why the statement before the dash holds.

```text
Rather than:
    The file is read in binary mode (its encoding is not known in
    advance).
Prefer:
    The file is read in binary mode (as its encoding is not known in
    advance).
```

"In order that" also introduces a purpose, although "so that" or "to"
usually reads better.

```text
Rather than:
    The cache could also store the response headers in order that a
    request that fails validation can be retried without querying the
    origin again.
Prefer:
    The cache could also store the response headers so that a request
    that fails validation could be retried without querying the origin
    again.
```

### Keep a consequence with the statement it follows from

Keep a consequence in the same sentence as the statement that it follows
from. Either join the consequence with ", such that" or put it in a
parenthesis with "therefore" or "hence". A new sentence that carries
"hence" usually reads worse.

```text
Rather than:
    The timeout is measured from the first attempt. Each retry hence has
    less time than the attempt before it.
Prefer:
    The timeout is measured from the first attempt (each retry therefore
    has less time than the attempt before it).
```

If something follows from what has been stated, mark it as an inference
("hence") rather than present it as a description.

```text
Rather than:
    The worker exits on the shutdown message, which must be the last
    message in the queue.
Prefer:
    The worker exits on the shutdown message (hence the shutdown message
    must be the last message in the queue).
```

### Keep a pronoun that can refer to only one thing

If a reader could not take a pronoun or a demonstrative another way
(rule 3), keep the pronoun or the demonstrative rather than repeat the
noun, because needless repetition reads badly.

```text
Rather than:
    The writer compresses the file. Compressing the file reduces the
    space that the file takes on disk.
Prefer:
    The writer compresses the file. This reduces the space that the file
    takes on disk.
```

### Refer to a whole clause with a new sentence, not with "which"

A "which" that refers to a whole clause usually reads worse than a new
sentence. Open the new sentence with "This" if "This" can refer to only one
thing (rule 3). Otherwise, open the new sentence with a subject that names
what is referred to.

```text
Rather than:
    The handler logs the error and re-raises the exception, which allows
    the caller to decide whether to retry.
Prefer:
    The handler logs the error and re-raises the exception. Re-raising
    the exception allows the caller to decide whether to retry.
```

### Give each independent claim its own sentence

Two independent claims usually read better as two sentences than as one
sentence joined by "and".

```text
Rather than:
    The key is the user ID and the value is the session token.
Prefer:
    The key is the user ID. The value is the session token.
```

### Place asides and definitions after the main clause

Put an aside that qualifies a sentence's statement after the main clause.
A short definition may follow the term in a parenthesis that opens with
"i.e.".

```text
Rather than:
    As at the close of business, the report gives each account's
    balance.
Prefer:
    The report gives each account's balance (as at the close of business).
```

```text
Rather than:
    A cache entry is refetched once it is older than `max_age` (the age
    beyond which an entry is stale).
Prefer:
    A cache entry is refetched once it is stale (i.e. older than
    `max_age`).
```

### List three or more cases as bullets

If a statement depends on three or more cases, list the cases as bullets.
Two cases may be stated in prose or as bullets. Open the list with a
lead-in that says what the cases depend on. Write each bullet as the case,
a colon and a full clause.

```text
Rather than:
    If `verbosity` is 0, only errors are logged. If `verbosity` is 1,
    errors and warnings are logged. If `verbosity` is 2, every message is
    logged.
Prefer:
    The messages logged depend on `verbosity`:
        - 0: only errors are logged.
        - 1: errors and warnings are logged.
        - 2: every message is logged.
```

```text
Rather than:
    The value returned depends on whether the cache entry is fresh. If
    the entry is:
        - fresh, the value returned is the stored value.
        - stale, the value returned is the value fetched from the source.
Prefer:
    The value returned depends on whether the cache entry is:
        - fresh: the stored value is returned.
        - stale: the value is fetched from the source and returned.
```

### Orient the reader before the detail

- Open a docstring with a summary of what the documented object does or,
  for a test, of what the test verifies. Describe the mechanism afterwards.
- State a qualification that applies to a whole passage (for example its
  scope or a condition) before the passage.
- State a general rule before an exception to it. A sentence that states a
  caveat or a corollary of what has just been said may open with "Note
  that".
- Put separate concerns in separate paragraphs.

```text
Rather than:
    """Search each directory from the working directory up to the root for
    a configuration file, read the first file found and return its
    settings."""
Prefer:
    """Return the settings of the configuration file.

    Each directory from the working directory up to the root is searched
    for the file, and the first file found is read.
    """
```

```text
Rather than:
    """The parser skips each comment line and returns the other rows in
    order. Verified for every supported encoding."""
Prefer:
    """Verify the parser skips comment lines.

    The following is verified for every supported encoding: the parser
    skips each comment line and returns the other rows in order.
    """
```

```text
Rather than:
    The method returns the rows in order and skips each comment line. A
    blank line ends the input. All of this applies only if `strict` is
    False.
Prefer:
    If `strict` is False:
        - the method returns the rows in order.
        - the method skips each comment line.
        - a blank line ends the input.
```

```text
Rather than:
    A request that fails with a 4xx response is not retried (as a
    repeated request would receive the same response). Any other request
    is retried up to three times.
Prefer:
    A request is retried up to three times. A request that fails with a
    4xx response is not retried (as a repeated request would receive the
    same response).
```

### State both sides of a restriction

If a statement holds only in some cases, also state what holds in the
other cases.

```text
Rather than:
    Calling the method concurrently is safe only if the cache is
    read-only.
Prefer:
    Calling the method concurrently is safe only if the cache is
    read-only. If the cache is writable, calls to the method must be
    serialised.
```

### Choose words that admit one reading

- Use "except", not "but", for an exclusion.
- Use a negative modal ("cannot hold a") rather than a negative quantifier
  ("can hold no").

```text
Rather than:
    Every field but the ID is copied, whether or not the field is empty.
Prefer:
    Every field except the ID is copied, whether or not the field is
    empty.
```

```text
Rather than:
    The list can hold no duplicate.
Prefer:
    The list cannot hold a duplicate.
```

### Use defined terms, in their defined form

If the project defines a term (for example in a glossary), use the term
rather than re-describe what it means. Keep the form of a term consistent:
if a qualified noun is written "the returned value", do not elsewhere write
"the value returned".

```text
Rather than (if the project defines a 'stale entry' as an entry older
than `max_age`):
    Where an entry has been held for longer than `max_age`, it is
    refetched.
Prefer:
    A stale entry is refetched.
```

## Checking a draft

Reread the draft. The following questions check the core rules. Ask them
of each sentence that is new or revised:
- Does each claim have its own verb?
- Does any participial phrase have a subject other than the subject of the
  main clause?
- Could a reader take a pronoun, a demonstrative or a "which" to refer to
  something other than what is meant?
- Does a ", such that" introduce a purpose? Does a ", as" introduce a
  reason? Does a "where" introduce a condition on a particular thing?
- Does an aside that holds a clause split the main clause?

Ask also of each sentence of new text:
- Is any relationship between the parts of the sentence left for the
  reader to infer?
- Is the sentence true on its literal reading, and not only on the reading
  intended?
- Does the sentence read worse for following a guide? If it does, write the
  sentence that reads best and still admits only one reading.

Ask of each new docstring and each new paragraph:
- Does the opening sentence tell the reader what follows?
