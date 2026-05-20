# `TagifiedTag` and `TagifiedTagList` are immutable classes, siblings of `Tag` / `TagList`

- **Date:** 2026-05-20
- **Context:** Issue posit-dev/py-htmltools#116. Several earlier attempts (the alias form on `main`, the subclass-overrides form in PR #118, and a generic-`TagChild[TagNodeT]` spike preserved on branch `schloerke/spike-tagnodeT-append-narrowing`) each had blocking flaws. This decision records the final design and explains why each alternative was rejected.
- **Status:** Accepted

This decision supersedes two earlier accepted decisions from 2026-05-18 (`tag-mutation-wide-tagchild.md` and `tagify-returns-tagified.md`), both of which were framed around `TagNodeT` generics on `Tag`/`TagList`. Those generics are removed by this refactor; their conclusions no longer apply.

## Decision

`TagifiedTag` and `TagifiedTagList` are **immutable runtime classes**, modeled as **siblings of**, not subclasses of, `Tag` / `TagList`. `Tag` and `TagList` are no longer generic in an element type — `TagNodeT` is removed.

```
        UserList[TagNode]                Sequence[TagifiedNode]
              │                                 │
              ▼                                 ▼
          TagList                       TagifiedTagList
       (mutable, mutators take          (immutable, no mutators,
        TagChild)                        tuple storage)
       .tagify() ─────▶ TagifiedTagList

                   _TagBase (shared render plumbing)
                  ┌─────────────┴──────────────┐
                  ▼                            ▼
                Tag                       TagifiedTag
             (mutable, mutators           (immutable, no mutators,
              take TagChild,               no add_class, no
              has add_class, ctx-mgr)      __enter__/__exit__)
             .tagify() ──────▶ TagifiedTag
```

`.tagify()` on `Tag` / `TagList` constructs a new sibling instance. `.tagify()` on `TagifiedTag` / `TagifiedTagList` returns `self`.

`Tagifiable.tagify()` still returns the broad `Tagified` union — downstream `.tagify()` implementations annotate `-> Tagified`. The *shape* of `Tagified` changes:

```python
TagifiedNode = Union[TagifiedTag, TagNodeLeaf]
Tagified     = Union[TagifiedNode, float, None, Sequence[Tagified]]
```

Non-generic, recursive `Union` — the form pyright handles cleanly cross-module. `TagifiedTagList` is structurally `Sequence[TagifiedNode] <: Sequence[Tagified]` and matches the recursive arm.

## Rejected alternatives

### 1. Alias-only (the `main`-branch state before #116)

`TagifiedTag` and `TagifiedTagList` are `TypeAliasType`s for `Tag[TagifiedNode]` / `TagList[TagifiedNode]`.

**Why rejected:** No runtime distinguishability. `isinstance(x, TagifiedTag)` doesn't work — the alias dissolves into the underlying generic, and `isinstance(x, TagList)` is `True` for both buildable and tagified containers. `.append(some_tagifiable)` on a tagified container is silent at type-check time. The static-input gap of #115/#116 is wide open.

### 2. Subclasses with input-narrowed mutator overrides (PR #118 approach)

Real subclasses (`TagifiedTag(Tag["TagifiedNode"])`), with `.append/.extend/.insert` overridden to a narrow `Tagified`-only signature.

**Why rejected:** Input narrowing in a subclass is contravariantly LSP-unsafe — pyright flags every override with `reportIncompatibleMethodOverride`. Each override needs a `# pyright: ignore` suppression, plus an `_LSPNarrowingCanary` tripwire test to detect future pyright behavior changes that would invalidate the suppression. Source-cost of the suppressions and canary outweighs the win; the architecture is harder to read than the result.

### 3. Generic `TagChild[TagNodeT]` recursive alias

Promote `TagChild` from a non-generic Union to a generic `TypeAliasType` parameterized on `TagNodeT` so mutator input narrows by substitution. Attempted in spike `schloerke/spike-tagnodeT-append-narrowing` commit `79a266b`.

**Why rejected:** Pyright 1.1.409 has a cross-module bug — the recursive `Sequence[TagChild[TagNodeT]]` arm renders as `Sequence[Unknown]` when an external module imports the alias in strict mode. This is the same failure that motivated #105's choice of a non-generic `TagChild` originally. It triggers thousands of `reportUnknownMemberType` errors in downstream strict-mode CI (e.g. Shiny). Verified by reproducing the leak in a 30-line cross-module test fixture during the spike.

### 4. PEP 695 `type` syntax instead of `TypeAliasType`

Same shape as (3) but using `type TagChild[T] = T | float | None | Sequence[TagChild[T]]`. Pyright handles this correctly cross-module — verified.

**Why rejected:** PEP 695 `type` syntax requires Python 3.12+. htmltools supports Python 3.10+. Out of scope until the minimum-Python bump.

### 5. Mutable tagified containers with narrow mutator signatures

The sibling design but with `.append(item: Tagified)` on the tagified side — narrow input, no LSP question (no parent contract to narrow), no `TagNodeT` generics.

**Why rejected:** "Tagified" semantically means frozen-final-shape. Allowing mutation undermines the invariant and requires a render-time `RuntimeError` guard to catch mutation-after-`.tagify()`. Going immutable eliminates the guard, the mutator signatures, and the question of what to do when `tagified.append(some_tag)` is called — it becomes a categorical `AttributeError`, which is the right answer. "Method doesn't exist" is a stronger guarantee than "method narrows input".

## Why the chosen design wins

- **Disjoint runtime types.** `isinstance(x, Tag)` and `isinstance(x, TagifiedTag)` are mutually exclusive. `Tag` reliably means "buildable"; `TagifiedTag` reliably means "rendered". The two-step `isinstance(x, Tag) and not isinstance(x, TagifiedTag)` dance that alternative 1 forced disappears.
- **No LSP question** — no parent contract to violate.
- **No `TagNodeT`** → no recursive `TypeAliasType` → no cross-module pyright leak.
- **Static "no mutators" is stronger than "narrow mutators"** — categorical, not signature-dependent. Pyright reports `reportAttributeAccessIssue` (cleaner diagnostic) instead of `reportArgumentType`.
- **Render-time `RuntimeError` guard becomes dead code** and is deleted along with mutators. Mutation-after-`.tagify()` is structurally impossible.
- **Boundary `TypeError` in `TagList.tagify()` stays** — that one guards the *construction* contract (a child's `.tagify()` returning un-tagified content), not mutation.

## Cost accepted

`def f(t: Tag)` accepting a `tagified` value is now a real static type error. (It was permissive under PR #118's subclass form — pyright treated the `TagifiedTag(Tag["TagifiedNode"])` flow into `Tag` as assignable. With siblings, it's a clean rejection.) This is the variance break that issue #116 originally documented as the "intentional cost" of distinguishing the two kinds at the type level.

Downstream fix recipes (also in `CHANGELOG.md` for 0.7.0):

- **Widen the parameter:** `def f(t: Tag | TagifiedTag): ...` — minimal and explicit. Best for short, render-only signatures.
- **Use a Protocol or the shared `_TagBase`** if the function only needs render-time methods.
- **Cast at the call site:** `cast("Tag", tagified)` — escape hatch for one-off mismatches.

## Related

- Issue #115 — https://github.com/posit-dev/py-htmltools/issues/115 (Self-typed overload alternative, abandoned)
- Issue #116 — https://github.com/posit-dev/py-htmltools/issues/116
- Issue #105 — https://github.com/posit-dev/py-htmltools/issues/105 (original Tagified type system; documented the `Sequence[Unknown]` leak)
- PR #118 — https://github.com/posit-dev/py-htmltools/pull/118 (subclass-overrides approach, superseded by this decision)
- Spike branch `schloerke/spike-tagnodeT-append-narrowing` commit `79a266b` — generic-`TagChild` attempt with documented cross-module leak.
