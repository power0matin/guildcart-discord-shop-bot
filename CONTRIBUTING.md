# Contributing to GuildCart

Thank you for considering a contribution.

## Before opening an issue

- Search existing issues and pull requests first.
- Include the relevant phase from [ROADMAP.md](ROADMAP.md) when describing a planned feature.
- Never include bot tokens, payment credentials, VPN credentials, real customer data, or production access links in an issue, log, or screenshot.

## Pull request expectations

- Keep changes focused and explain the problem they solve.
- Update documentation and example configuration whenever behavior or settings change.
- Add tests for business logic, permissions, state transitions, failure paths, and regressions.
- Do not describe unimplemented roadmap items as working features.
- Avoid adding generated files, `__pycache__`, virtual environments, local databases, or `.env`.
- Do not add HyperSentry-specific credentials or private deployment settings to the shared codebase.

## Local checks

The project is still an early prototype and its automated test/lint commands are being established. Until CI commands are defined, at minimum verify Python syntax and exercise the changed workflow in a separate Discord test guild. Clearly report what you did and did not test in the pull request.

## Design direction

- Keep the reusable shop core independent of any one VPN provider.
- Treat payment status and order history as durable domain data, not data derived from Discord messages.
- Make external side effects retry-safe where practical.
- Validate permissions at the point of each privileged action.
- Prefer clear, maintainable code to abstraction without a concrete use case.


## Package structure

- Start the bot with `python main.py` from the repository root.
- Keep process startup and bot construction in `guildcart/app.py`.
- Put Discord commands and interaction UI in `guildcart/cogs/`.
- Keep domain validation in `guildcart/domain/` and persistence in `guildcart/storage/`.
- Prefer imports from `guildcart.*`; legacy files at the repository root and under `features/` should remain thin compatibility wrappers.
- Before submitting changes, run `python -m unittest discover -s tests -v` and `python -m compileall -q main.py bot.py config.py guildcart features tests`.
