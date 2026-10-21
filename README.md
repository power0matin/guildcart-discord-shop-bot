# GuildCart — Open-Source Discord Shop Bot

GuildCart is an open-source Discord shop bot project aimed at configurable sales of digital products and subscriptions. The first real-world use case is VPN subscription sales, but the core is intended to remain independent of any single brand, VPN panel, payment method, or Discord server.

> [!WARNING]
> **Early prototype — not production-ready.** The current code provides a shop menu, ticket creation, SQLite-backed pending orders, and manual staff review commands. User-submitted payment details are not independently verified, and approving an order does not deliver a product or provision a VPN subscription. Do not use this version to fulfil real paid orders.

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
| SQLite-backed pending order records | Implemented; includes per-guild scope and review metadata |
| Manual order review | `/orders`, `/order approve`, and `/order reject`; requires administrator permission or configured shop-admin role |
| Automatic delivery or VPN provisioning | Not implemented |
| Subscription renewals, expiry and usage limits | Not implemented |
| Automated checks | CI runs unit tests for plan parsing and SQLite order transitions, plus syntax checks |

This table describes code that exists today; planned features are not implied to be implemented.

## Technology

- Python 3.11+
- `discord.py` 2.x
- `python-dotenv`
- JSON configuration for the current prototype

SQLite stores order status and review metadata for a single bot instance. It does not verify payment or deliver products. See the roadmap before relying on the prototype.

## Project layout

```text
main.py                     # Primary process entry point
bot.py                      # Backward-compatible entry point
guildcart/
  app.py                    # Bot factory, startup and extension registration
  settings.py               # Runtime settings and configuration validation
  cogs/
    core.py                 # Help command and shared Discord events
    shop.py                 # Shop UI, tickets and order-review commands
  domain/
    plans.py                # Plan parsing and validation
  storage/
    order_store.py          # SQLite order repository
features/                   # Compatibility wrappers for old imports
tests/
```

Run GuildCart with `python main.py` from the repository root. The former `python bot.py` entry point remains as a compatibility wrapper. Internal code should import from `guildcart.*`; add Discord commands in `guildcart/cogs/`, domain rules in `guildcart/domain/`, and persistence adapters in `guildcart/storage/`.

## Quick start (prototype)

### 1. Requirements

Install Python 3.11 or newer and create a Discord application/bot in the Discord Developer Portal. Invite it to a test server with only the permissions it needs to create and manage its shop/ticket channels.

### 2. Clone and install

Clone the renamed repository:

```bash
git clone https://github.com/power0matin/guildcart-discord-shop-bot.git
cd guildcart-discord-shop-bot
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

The current example configuration uses the legacy label format such as `Starter – 50T`. The prototype parses the displayed label to infer the price; this will be replaced by structured product fields before a stable release. The sample amounts are placeholders, not recommended pricing.

### 4. Run

```bash
python main.py
```

Use `/shop` in a test server. A user-submitted amount or payment reference is not proof of payment. The order-review commands record staff decisions only; this prototype does not automatically provision a paid subscription.

## Configuration files

- `.env.example`: safe example for environment-based settings.
- `config.json.example`: legacy plan selector configuration for the current prototype.
- `.env` and `config.json`: local files; never commit them.

The long-term configuration schema is documented in [ROADMAP.md](ROADMAP.md). Expect a breaking schema migration before the first stable release.

## Manual order review (prototype)

After setting up the bot in a test server:

- Run `/shop`, select a plan, and submit the payment details in the ticket.
- Staff can run `/orders` to list up to 10 pending orders in that server.
- After checking payment independently, authorized staff can run `/order approve <order_id>` or `/order reject <order_id> <reason>`.
- Decisions and reviewer IDs are saved in SQLite. A rejected or already-reviewed order cannot be reviewed again.
- A submitted order is saved before the staff notification is attempted. If that notification fails, the order remains available through `/orders`.

Approval records a manual staff decision only. No product or VPN subscription is automatically provisioned yet. The form's cardholder name and last four digits are sent to the staff channel but are not stored in the SQLite order record; optional transaction references are stored locally.

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
