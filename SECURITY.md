# MRFoundry security policy

## Scope

This repository distributes documentation-style agent skills (Markdown) plus one
small helper shell script (`skills/mri-reconstruction/scripts/bart_recon.sh`). It
runs no server or network service and contains no secrets. The practical risks
are (a) a bug in the helper script and (b) an outbound link pointing somewhere
unexpected.

## Reporting a vulnerability

Please report privately using GitHub's **"Report a vulnerability"** button on the
repository's **Security** tab (Security Advisories). Do **not** open a public
issue for security reports. We aim to respond promptly and will credit reporters
who wish to be credited.

## Note for users

Agent skills run with your agent's full permissions. **Review any script before
running it**, install only from sources you trust, and never paste secrets or
API tokens into an agent session. External resources this skill links to are
governed by their own terms.
