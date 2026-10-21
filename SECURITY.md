# Security Policy

## Project status

GuildCart is an early prototype and is **not currently suitable for processing real paid orders or production VPN provisioning**. See [ROADMAP.md](ROADMAP.md) for the work required before production use.

## Reporting a vulnerability

Please do not publish exploitable details, credentials, or customer data in a public issue. Contact the repository maintainer privately through the contact method listed on the maintainer's GitHub profile. Include a concise description, impact, affected revision, and safe reproduction steps.

Do not test against infrastructure or Discord servers that you do not own or have explicit permission to assess.

## Sensitive data

Never commit or include in logs, screenshots, test fixtures, or issues:

- Discord bot tokens or application secrets.
- Payment-provider API keys, webhook secrets, or private payment data.
- VPN-panel credentials, client configuration links, UUIDs, or access keys.
- Real customer details, receipts, or private support transcripts.

Use sanitized fixtures and test accounts. If a secret may have been exposed, revoke or rotate it immediately; deleting it from the current file is not sufficient.
