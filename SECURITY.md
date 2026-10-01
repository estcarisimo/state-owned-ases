# Security Policy

## Supported versions

This is an archived dataset with a small tooling package, maintained on a best-effort
basis. Only the latest release receives fixes.

| Version | Supported |
| ------- | --------- |
| 2.x     | ✅        |
| 1.x (2021 files) | ❌ |

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Use GitHub's private reporting:
[Report a vulnerability](https://github.com/estcarisimo/state-owned-ases/security/advisories/new).

Include a description, reproduction steps, and the version you used. Expect an
acknowledgment within about two weeks. This is an academic side project, so response
times are best-effort. Confirmed issues are fixed in a pull request, released, and
disclosed in `CHANGELOG.md` under *Security* and in a GitHub security advisory that
credits the reporter (unless they prefer otherwise). Please keep details private until
the fix is released.

## What the tooling does

`state-owned-ases` reads the JSON documents in `data/canonical/` and writes files to the
directory you choose. It makes no network requests, needs no credentials, and sends no
telemetry.

## Scope

In scope:

- Unintended file writes or path traversal through the CLI's output options.
- Unsafe parsing of the canonical documents.
- Dependency vulnerabilities with a plausible exploitation path in this tool.

Out of scope:

- The content of third-party websites linked from the data's `url` field. Those links
  were recorded in 2019–2020, and some domains may have changed hands since. Treat them
  as historical references, not trusted links.
- Findings from automated scanners with no demonstrated impact.

## Automated scanning

CI runs `bandit` over the package and `pip-audit` over the locked dependencies on every
pull request. CodeQL scans the code, and Dependabot proposes dependency updates.
