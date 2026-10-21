# GuildCart — Open-Source Discord Shop Bot

GuildCart is an open-source Discord shop bot project aimed at configurable sales of digital products and subscriptions. The first real-world use case is VPN subscription sales, but the core is intended to remain independent of any single brand, VPN panel, payment method, or Discord server.

> [!WARNING]
> **Early prototype — not production-ready.** The current code provides a basic shop menu, ticket creation, a payment-details modal, and admin notifications. It does not yet provide durable order/payment records, verified payment processing, automated product delivery, or reliable subscription lifecycle management. Do not use it to fulfil real orders until the relevant roadmap acceptance criteria and tests are complete.

## Project goals

- Configure shop text, products, support links, roles, and channels without editing application code.
- Track orders and their state durably instead of treating Discord messages as the database.
- Support manual payment review first, then pluggable payment providers where appropriate.
- Support product-delivery adapters, including a future VPN provisioning adapter.
- Keep the reusable open-source core separate from private deployment configuration for operators such as HyperSentry.
- Make installation, upgrades, backups, and troubleshooting understandable for self-hosters.

See [ROADMAP.md](ROADMAP.md) for phases, scope, release milestones, and acceptance criteria.

## Current implementation

The repository is an early proof of concept.

| Capability | Current state |
|---|---|
| `/shop` shop message and plan selector | Basic implementation |
| Private order/ticket channel | Basic implementation |
| Payment-details modal | Collects user-submitted fields; does **not** verify payment |
| Admin notification | Basic implementation; failure handling needs work |
| Configuration through `.env` and `config.json` | Partial, legacy format |
| Persistent order/payment database | Not implemented in the current flow |
| Admin approve/reject workflow | Not implemented |
| Automatic delivery or VPN provisioning | Not implemented |
| Subscription renewals, expiry and usage limits | Not implemented |
| Test suite and CI | Not yet established |

This table describes code that exists today; planned features are not implied to be implemented.

## Technology

- Python 3.11+
- `discord.py` 2.x
- `python-dotenv`
- JSON configuration for the current prototype

SQLite is a planned first persistent store, not a completed payment database in the current implementation. See the roadmap before relying on the prototype.

## Quick start (prototype)

### 1. Requirements

Install Python 3.11 or newer and create a Discord application/bot in the Discord Developer Portal. Invite it to a test server with only the permissions it needs to create and manage its shop/ticket channels.

### 2. Clone and install

The GitHub repository may retain its original URL until the repository rename is completed:

```bash
git clone https://github.com/power0matin/Harmony-DiscordBot.git
cd Harmony-DiscordBot
python -m venv .venv
```

Activate the virtual environment:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
cp config.json.example config.json
```

Edit `.env` and set `DISCORD_TOKEN` to your bot token. Treat it as a password: never commit `.env`, paste the token into issues, or include it in logs. Configure channel/role names and shop messages for a **test server** first.

The current example configuration uses the legacy label format such as `🛍️ Starter – 50T`. The prototype parses the displayed label to infer a price, which is fragile and is scheduled to be replaced with separate structured fields for product name, amount, currency, duration, and limits. The sample amounts are placeholders, not recommended pricing.

### 4. Run

```bash
python bot.py
```

Use `/shop` in a test server. Because the current implementation is incomplete, a user-submitted amount or payment reference must not be treated as proof of payment, and this prototype must not be used to automatically provision a paid subscription.

## Configuration files

- `.env.example`: safe example for environment-based settings.
- `config.json.example`: legacy plan selector configuration for the current prototype.
- `.env` and `config.json`: local files; never commit them.

The long-term configuration schema is documented in [ROADMAP.md](ROADMAP.md). Expect a breaking schema migration before the first stable release.

## Security and operational notes

- Keep the bot token, payment-provider secrets, VPN-panel credentials, and customer connection details out of Git.
- A screenshot, transaction ID, user-entered amount, or last four card digits is not proof that a payment settled.
- Never log full VPN links, access keys, payment secrets, or other credentials.
- Test permissions, duplicate interactions, service failures, and restart recovery before serving real customers.
- Public publication should follow a full current-tree **and Git-history** secret scan. Removing a secret from the latest file does not remove it from previous commits.
- Use the least-privilege Discord permissions possible.

Report potential vulnerabilities privately; see [SECURITY.md](SECURITY.md).

## Roadmap

The full phase plan and measurable exit criteria live in [ROADMAP.md](ROADMAP.md). In summary:

1. Repository hygiene and a reliable development baseline.
2. Structured configuration, products, and durable order records.
3. A complete manual-payment review workflow.
4. Pluggable, idempotent product delivery.
5. VPN provisioning and subscription lifecycle support.
6. Multi-guild isolation, permissions, tests, deployment, and observability.
7. Public beta, documentation, migration guidance, and stable release.

## Contributing

Contributions are welcome once the repository is prepared for public collaboration. Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request. Please keep private deployment settings and HyperSentry-specific secrets out of the shared core.

## License

MIT. See [LICENSE](LICENSE).
