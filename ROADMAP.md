# GuildCart Roadmap

This roadmap is the source of truth for the planned evolution of GuildCart. It separates the existing prototype from future work and defines completion criteria instead of promising dates that may change.

## Product direction

GuildCart is an open-source, self-hostable Discord shop and order-management bot for digital products and subscriptions. The first practical deployment is intended to sell HyperSentry VPN subscriptions, but the reusable core must not depend on HyperSentry, a single VPN panel, one payment provider, or one Discord server.

### Product principles

1. **Orders are data, not messages.** Discord is the user interface; durable records are the source of truth.
2. **No false payment success.** Client-submitted amounts, receipts, last-four digits, and transaction references are claims to review, not payment verification.
3. **Delivery is replaceable.** VPN provisioning is a provider adapter behind a stable interface.
4. **Retries must be safe.** Repeating a payment callback or delivery job must not create duplicate orders, charges, or VPN accounts.
5. **Secrets stay local.** Runtime tokens, payment credentials, VPN-panel API keys, and customer connection links never belong in source control or ordinary logs.
6. **Guild data is isolated.** Configuration, products, orders, tickets, and settings are scoped to the owning Discord guild.
7. **Ship tested increments.** A feature is not complete until its failure paths and permissions are tested and its user-facing documentation is updated.

## Current status (2026-10-21)

The current repository is an early prototype. The shop selector, ticket creation, SQLite-backed pending orders, and manual staff review commands exist. Trusted payment verification, automatic product delivery, VPN provisioning, subscription renewals/expiry, restart-safe Discord interactions, and end-to-end testing in a Discord test guild remain incomplete. Do not use this revision to fulfil real paid orders.

Do not use the current revision to fulfil real paid orders. No release milestone below should be treated as complete until its acceptance criteria are demonstrated by code and tests.

## Phase 0 — Repository hygiene and naming

**Goal:** make the repository safe and understandable before wider public exposure.

- [x] Adopt the GuildCart project name consistently in README, default shop text, ticket embeds, sample configuration, and documentation.
- [x] Choose and apply the final GitHub repository slug (`guildcart-discord-shop-bot`).
- [x] Set the repository description and relevant GitHub Topics.
- [ ] Remove tracked `__pycache__`, `.pyc`, local databases, logs, generated artifacts, and local configuration files.
- [x] Expand `.gitignore` for Python caches, virtual environments, `.env`, local config, database files, coverage, and build output.
- [ ] Scan the current tree and the full Git history for tokens, credentials, private URLs, payment data, and customer information before changing visibility.
- [ ] Rotate any secret that was ever committed or disclosed; history rewriting alone is not enough.
- [x] Add contribution and vulnerability-reporting guidance.
- [ ] Verify the declared license is intentional and applies to the files being published.

**Exit criteria**

- A clean checkout contains source and safe examples only.
- No real credentials, customer data, local database, or generated Python bytecode is tracked.
- Secret-scanning review has covered the full history; any exposed credentials have been rotated.
- README install/run instructions match actual filenames and are reproducible.

## Phase 1 — Reliable application baseline

**Goal:** a predictable startup and maintainable codebase before adding more sales features.

- [x] Load environment configuration before reading `DISCORD_TOKEN`.
- [x] Make `main.py` the primary entry point and retain `bot.py` as a compatibility wrapper.
- [x] Group application startup, Discord Cogs, domain utilities, and order storage under the `guildcart` package.
- [ ] Fail at startup with actionable validation messages for invalid required settings.
- [ ] Pin and test a supported Python/`discord.py` combination; document required Discord intents and permissions.
- [ ] Replace broad exception swallowing during configuration/extension loading with explicit validation and useful structured logs.
- [x] Separate application startup, runtime settings, Discord Cogs, domain validation, and SQLite persistence into package modules.
- [ ] Separate the remaining shop/payment orchestration from Discord UI and external-service adapters.
- [ ] Review application-command sync behavior so development changes do not cause unnecessary global syncs or rate-limit problems.
- [ ] Define one error-response strategy for slash commands, component interactions, and prefix commands.
- [ ] Add automated formatting/linting and type checks where they provide measurable value.

**Exit criteria**

- A new environment can install dependencies and start the bot using the documented steps.
- Missing/invalid settings stop startup safely and explain what needs correction without printing secrets.
- Command and component failures do not leave interactions unanswered.
- CI runs on pull requests and fails on actual test/lint/type-check failures.

## Phase 2 — Structured shop configuration and catalogue

**Goal:** remove fragile parsing and make the product catalogue configurable without source edits.

- [ ] Define a validated configuration schema with a version field and explicit migration behavior.
- [ ] Model products with stable IDs, name, description, active state, product type, price amount, currency, optional image, and delivery mode.
- [ ] For VPN plans, support duration, traffic/data cap, concurrent-device limit, and applicable access/protocol metadata where the upstream provider supports them.
- [ ] Store currency amounts as integers in the currency's minor unit where applicable; do not use binary floating-point comparisons for money.
- [ ] Validate IDs, duplicate values, name/description limits, URLs, allowed currencies, numeric bounds, and Discord component limits.
- [ ] Distinguish product identity from display labels; never parse price or plan identity from a UI string.
- [ ] Support reload/restart behavior with explicit handling for malformed configuration.
- [ ] Provide a complete generic example config and a migration note for the current legacy `plans: [{label, value}]` schema.

**Exit criteria**

- A shop owner can add, edit, disable, and reorder products through documented configuration.
- Product prices and attributes are validated independently of display text.
- Invalid config is rejected with a clear path/key error and does not silently start an empty or misleading shop.
- Legacy configuration migration is tested.

## Phase 3 — Orders and manual payment review

**Goal:** implement a reliable human-reviewed sales workflow.

- [x] Add durable SQLite order storage for a single self-hosted instance; PostgreSQL support remains a future decision.
- [ ] Define order and payment-attempt records with stable IDs, guild ID, customer ID, product snapshot, amount/currency, timestamps, and state.
- [ ] Define explicit order states: `pending_payment`, `pending_review`, `paid`, `rejected`, `cancelled`, `fulfilled`, and `refunded` where supported.
- [x] Guard manual review transitions and store reviewer, review time, and reason.
- [x] Provide approve/reject commands protected by administrator permission or the configured shop-admin role; replacing role-name matching with stable IDs remains open.
- [ ] Treat a receipt/reference as submitted evidence only. Do not mark an order paid merely because form values match the expected price.
- [x] Confirm only that the order was submitted for review; explicitly state that submission is not payment verification.
- [x] Store durable order IDs, guild/customer IDs, product/price snapshots, and the originating ticket channel ID.
- [x] Persist an order before attempting staff notification and report database/notification failures honestly; duplicate form submissions still need deduplication.
- [ ] Add migrations, backups, and retention/privacy guidance for stored customer records.

**Exit criteria**

- An order remains available after restart and is never considered paid without an authorized review or trusted provider confirmation.
- Approve/reject actions are authorized, auditable, and idempotent.
- Failed notification delivery does not silently lose an order.
- Tests cover duplicate submissions, invalid state transitions, unauthorized decisions, and database failures.

## Phase 4 — Product delivery adapter

**Goal:** fulfil an order only after a trusted paid state.

- [ ] Define a `ProvisioningProvider` or equivalent interface for validate, provision, renew, inspect, disable/revoke, and reconcile operations as needed.
- [ ] Implement a safe manual-delivery provider first, with an auditable completion action.
- [ ] Define provider outcomes, timeouts, retryable errors, permanent errors, and reconciliation behavior.
- [ ] Use order IDs/idempotency keys to protect against duplicate provisioning on retries.
- [ ] Deliver customer data in a private channel or DM, with graceful handling when DMs are disabled.
- [ ] Never include raw access credentials in logs, staff-wide channels, exception traces, or analytics.
- [ ] Make fulfilment results durable and recoverable after process restart.

**Exit criteria**

- One paid order produces at most one logical fulfilment.
- Failed delivery can be retried without duplicate account creation.
- An operator can reconcile an order whose provider outcome is unknown.
- Customer delivery details are visible only to the intended customer and authorized staff.

## Phase 5 — VPN provider integration and subscription lifecycle

**Goal:** make VPN subscription sales the first complete production use case without coupling the core to one panel.

- [ ] Select and document the supported VPN panel/API and version before implementing an adapter; do not assume different panel forks share behavior.
- [ ] Put endpoint, credentials, inbound/profile identifiers, and provider-specific mapping in private deployment configuration.
- [ ] Map a GuildCart product to provider-side duration, data limit, device/connection limit, and other supported limits.
- [ ] Implement create, inspect, extend/renew, disable/expire, and revoke flows supported by the chosen API.
- [ ] Persist the external provider identifier and local subscription/order IDs needed for reconciliation.
- [ ] Prevent duplicate clients on retry and handle API timeouts with unknown outcomes safely.
- [ ] Add subscription states such as `provisioning`, `active`, `renewal_pending`, `expired`, `suspended`, `revoked`, and `provisioning_failed`.
- [ ] Run an expiry/renewal worker with bounded retries, timezone-aware timestamps, durable schedules, and observability.
- [ ] Notify customers of successful delivery, renewal, and expiry without leaking secrets.
- [ ] Add a reconciliation command/report comparing local subscription state with upstream provider state.
- [ ] Keep provider credentials and real VPN configs out of the public sample files and test fixtures.

**Exit criteria**

- A sandbox/test subscription can be created, checked, renewed, expired, and revoked through the real selected provider API.
- Repeated jobs and restarts do not duplicate clients or extend a subscription unintentionally.
- Provider API downtime leaves the order/subscription in an explicit recoverable state.
- No production credential is needed to run unit tests.

## Phase 6 — Multi-guild safety, permissions, and abuse controls

**Goal:** allow independent shop setups on multiple Discord servers.

- [ ] Scope every business record and configuration by `guild_id`; enforce the scope in repository methods.
- [ ] Prefer configured Discord IDs for roles/channels over mutable names.
- [ ] Add per-user open-ticket/order limits, component cooldowns, and appropriate rate limits.
- [ ] Validate guild/channel context for shop/order commands and interactions.
- [ ] Validate admin permissions at the point of each sensitive action.
- [ ] Prevent cross-guild reads/updates and test them explicitly.
- [ ] Make customer data retention, deletion, and export behavior clear.
- [ ] Avoid collecting full card numbers or unrelated personal information.

**Exit criteria**

- Integration tests prove that one guild cannot view or modify another guild's settings, products, orders, or subscriptions.
- Sensitive operations fail closed when the actor or configuration is missing.
- Abuse limits produce helpful, non-leaking responses.

## Phase 7 — Reliability, deployment, and operations

**Goal:** make self-hosting and maintenance predictable.

- [ ] Add structured logs with order correlation IDs while redacting secrets and access links.
- [ ] Add health/readiness behavior suitable for process supervision; do not rely on an interaction or console banner as the only health signal.
- [ ] Add graceful shutdown and ensure active database/provider operations reach a safe recoverable state.
- [ ] Add Dockerfile and a minimal Compose example only after the runtime and persistent-data paths are settled.
- [ ] Document environment variables, volumes, backups, restore, upgrades, rollback, and database migrations.
- [ ] Add dependency vulnerability scanning and secret scanning in CI.
- [ ] Test restarts, database locking/errors, Discord/API outages, provider timeouts, and recovery paths.
- [ ] Define support expectations and a sensible logging/retention policy.

**Exit criteria**

- A new operator can deploy, update, back up, restore, and roll back using documented instructions.
- CI and release checks pass on a clean environment.
- A test restore recovers products, orders, and subscription references.
- Logs provide enough diagnostic context without disclosing credentials.

## Phase 8 — Public beta and first stable release

**Goal:** publish an honestly described, installable open-source project.

- [ ] Complete a full Git-history secret scan and rotate any previously exposed credentials before changing repository visibility.
- [ ] Verify the repository slug, description, Topics, license, default branch, and badges.
- [ ] Publish a threat/security reporting process and contribution guide.
- [ ] Add bug report and feature request issue templates.
- [ ] Document supported Python and Discord-library versions, required permissions, intents, and known limitations.
- [ ] Include a sanitized example store and screenshots of the current working Discord UI.
- [ ] Document breaking configuration migrations and the upgrade path from the prototype.
- [ ] Tag a beta only when the stated beta scope and its tests are complete.
- [ ] Do not label the bot production-ready until manual/automatic payment truth, fulfilment, data recovery, and provider failure criteria are satisfied.

**Exit criteria**

- Fresh-clone installation, setup, shop display, test order, review, fulfilment, and restart recovery are demonstrated using a test guild.
- No undocumented real credentials or private HyperSentry configuration are required.
- Release notes distinguish supported behavior from planned work.

## Phase 9 — Optional improvements after the core is reliable

Only prioritize these after the earlier acceptance criteria pass:

- [ ] Coupons, promotions, product inventory, and limited-time offers.
- [ ] Revenue/order metrics and exportable reports.
- [ ] Additional payment-provider adapters with trusted status verification and webhook signature checks.
- [ ] Additional digital-product providers beyond VPN provisioning.
- [ ] Localization, including Persian/RTL-friendly product and payment messages.
- [ ] PostgreSQL and multi-instance deployment if actual scale requires it.
- [ ] Optional web dashboard only if Discord-based configuration proves insufficient.

These are optional extensions, not prerequisites for the first stable core.

## Proposed release milestones

| Milestone | Scope | Release gate |
|---|---|---|
| `0.1.0-alpha` | Clean baseline, safe samples, setup docs, basic shop | Clean install and smoke tests pass |
| `0.2.0-alpha` | Structured configuration and persistent product/order model | Migrations and domain tests pass |
| `0.3.0-beta` | Manual payment review and admin order workflow | No client-only path can mark an order paid |
| `0.4.0-beta` | Durable fulfilment interface and manual provider | Retry/idempotency tests pass |
| `0.5.0-beta` | First VPN provider adapter and subscription lifecycle | Sandbox provider lifecycle and reconciliation pass |
| `0.9.0-rc` | Multi-guild checks, deployment, recovery, security review | Release-candidate checklist passes |
| `1.0.0` | Documented, supported stable release | All stable-release gates are met |

Milestone labels are planning targets, not claims that the milestones are currently implemented.

## Recommended build order

1. Repository hygiene and startup reliability.
2. Configuration/schema and database foundations.
3. Order lifecycle and manual payment review.
4. Safe, idempotent delivery.
5. The chosen VPN provider adapter and subscription lifecycle.
6. Multi-guild permission isolation, deployment, recovery, and security tests.
7. Beta publication, then stable release only after the acceptance gates pass.

## Open design decisions

Resolve these before implementing the relevant phase, and document the decision in the pull request or an architecture note:

- Which VPN panel/API and exact supported version will be the first provider?
- Which currencies and payment flows are required for the first installation?
- Is the first supported deployment single-guild or multi-guild? The data model should still be guild-scoped.
- What customer data must be retained, for how long, and how can it be deleted?
- What is the supported minimum Python version and release cadence?
- Is SQLite sufficient for the first production instance, or is PostgreSQL immediately required by a concrete deployment need?

## Out of scope for the first stable release

- A complex web dashboard before the Discord workflow is reliable.
- Microservices or a distributed queue without a demonstrated need.
- Claiming automatic payment verification where no trusted payment API/webhook exists.
- Embedding HyperSentry production credentials or deployment-specific IDs in the public core.
