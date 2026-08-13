# Security

## Supported path

Only `MHS35-safe` and the files under `modern/` are being developed as the
safer Raspberry Pi 5 path. The legacy scripts and bundled packages remain for
reference and are not recommended for installation.

## Automated checks

The `Security` workflow runs tests, ShellCheck, CodeQL, Gitleaks, Syft SBOM
generation, and Grype vulnerability scanning. GitHub dependency review runs on
pull requests, including Dependabot updates. All third-party actions and the
Syft and Grype tools are pinned.

GitHub native secret scanning and push protection are enabled for this public
repository. OpenSSF Scorecard's GitHub Action does not support repositories
that GitHub identifies as forks, so it is not installed here. The repository
must become a standalone repository before that action can provide valid
results.

An SBOM identifies components; it does not establish that they are trustworthy.
The legacy binary packages and archives still require removal or complete
provenance verification. See [RESEARCH_NOTES.md](RESEARCH_NOTES.md).

## Reporting a vulnerability

Do not include secrets or exploit details in a public issue. Report the problem
to the repository owner through GitHub's private vulnerability reporting when
that option is available.
