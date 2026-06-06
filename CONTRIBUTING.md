# Contributing to pydsstools

Thank you for your interest in contributing. All contributions — bug reports, feature
requests, documentation improvements, and code — are welcome.

Please read this guide before opening an issue or pull request.

---

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating,
you agree to uphold its standards. Respectful communication is expected in all
project spaces.

---

## Reporting Bugs

Before opening an issue:

1. Check the [changelog](CHANGES.MD) — the behavior may have changed intentionally
   in a recent release.
2. Search [existing issues](https://github.com/gyanz/pydsstools/issues) to avoid
   duplicates.

When opening a bug report, include:

- pydsstools version (`pip show pydsstools`)
- Python version and OS
- Minimal reproducible example
- Full traceback if applicable

---

## Requesting Features

Feature requests are welcome. Open an issue describing:

- The use case — what problem does this solve?
- What the proposed API or behavior would look like
- Whether you are willing to implement it

---

## Versioning and Breaking Changes

pydsstools follows [Semantic Versioning](https://semver.org/):

| Version bump | Meaning |
|---|---|
| **Major** (e.g. 2.x → 3.x) | Breaking API changes |
| **Minor** (e.g. 3.0 → 3.1) | New features, backwards-compatible |
| **Patch** (e.g. 3.0.1 → 3.0.2) | Bug fixes only |

A major version bump is the explicit signal that breaking changes are present.
Older releases remain available on PyPI for workflows that cannot migrate immediately.

### Migration between major versions

This is a community-maintained project with a single maintainer. A formal migration
guide may not always be feasible. The changelog will document notable changes on a
best-effort basis.

pydsstools has a small public API. The large majority of read/write operations are
methods on `pydsstools.heclib.dss.HecDss.Open`, so the scope of any migration is limited.
The [API documentation](https://pydsstools.readthedocs.io/) is the authoritative
reference for current method signatures and is often the fastest way to find the
equivalent of a renamed or restructured call.

If you encounter an undocumented rename or removal, opening an issue is welcome —
community members who have already migrated may be able to help.

For version 3.x, see the [3.0.0 changelog entry](CHANGES.MD) for a summary of
what changed from 2.x.

---

## Submitting Pull Requests

1. Fork the repository and create a branch from `master`.
2. Make your changes. Add or update tests as needed.
3. Run the test suite locally: `pytest tests/`
4. Open a pull request with a clear description of what changed and why.

For large changes, open an issue first to discuss the approach before investing
significant time.

---

## Questions

Feel free to ask questions via [email](mailto:gyanbasyalz@gmail.com) or by
opening a GitHub issue.
