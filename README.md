# 💎 Discord Shop & Ticket Bot

A professional **Discord bot** for selling plans, collecting payments, and managing support tickets.
Built with **discord.py**, it supports modals for payment, automatic ticket channels, admin notifications, and fully configurable via `.env`.

## 🌟 Features

| Feature            | Description                               |
| ------------------ | ----------------------------------------- |
| 🛍️ Shop Display    | Display multiple plans in Discord         |
| 💳 Payment Modal   | Users submit payment info directly        |
| 🎫 Ticket Channels | Private channels per user                 |
| 🔒 Ticket Closing  | Users or admins can close tickets         |
| 📢 Admin Alerts    | Admins notified of new tickets & payments |
| 🌐 Configurable    | `.env` + `config.json` for easy setup     |
| 🔗 Telegram Links  | Direct links for support & shop           |

## ⚡ Prerequisites

- Python 3.11+
- `discord.py` 2.x
- `python-dotenv`
- SQLite (optional for payment DB)

## 🛠️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/discord-shop-bot.git
cd discord-shop-bot
```

2. **Create a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Environment Variables

Rename `.env.example` to `.env`:

```bash
cp .env.example .env
```

Fill in your values:

```dotenv
# Discord
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
CATEGORY_NAME=🎫 Support Tickets
ADMIN_CHANNEL_NAME=admin-log
ADMIN_ROLE_NAME=SupportTeam

# Payment
CARD_NUMBER=1111-2222-3333-4444
PAYMENT_TIMEOUT_MINUTES=30
PAYMENTS_DB=data/payments.db
CRYPTO_ADDRESS_USDT=USDT_WALLET_ADDRESS

# Ticket
TICKET_NAME_TEMPLATE=ticket-{author}-{rand6}

# Shop Texts
SHOP_TITLE=💎 Service Shop
SHOP_DESCRIPTION=Select a plan and complete payment to get access.
SHOP_FOOTER=Thank you for choosing our service.

# Telegram
TELEGRAM_SHOP_URL=https://t.me/your_channel
TELEGRAM_SUPPORT_URL=https://t.me/your_support

# Buttons
BTN_SHOP_LABEL=📱 Channel
BTN_SUPPORT_LABEL=🧑‍💻 Support
BTN_PAY_LABEL=💳 Submit Payment
BTN_CLOSE_LABEL=🔒 Close Ticket
```

### 2. Plans Configuration

Rename `config.json.example` to `config.json`:

```bash
cp config.json.example config.json
```

Edit the plans and prices:

```json
{
  "plans": [
    { "label": "Plan A – 50T", "value": "plan_a" },
    { "label": "Plan B – 100T", "value": "plan_b" },
    { "label": "Plan C – 200T", "value": "plan_c" }
  ]
}
```

## 🚀 Running the Bot

```bash
python main.py
```

### Usage

- Use `/shop` command in Discord to display the shop.
- Users select a plan → bot creates a private ticket → user submits payment info.
- Admins are automatically notified.

## 🧩 Directory Structure

```
discord-shop-bot/
│
├─ features/                # Core bot functionality
│  ├─ __init__.py
│  ├─ hello.py
│  ├─ newfeature.py
│  └─ shop.py
│
├─ data/
│  └─ payments.db      # SQLite database
│
├─ .env.example        # Example env file
├─ config.json.example # Example plan config
├─ bot.py             # Bot entry point
├─ requirements.txt
└─ README.md
```

## 📝 Commands

| Command | Description                                                      |
| ------- | ---------------------------------------------------------------- |
| `/shop` | Display shop plans, select a plan, create ticket, submit payment |

## 💡 Tips

- Always **keep your `.env` secret** — never commit to GitHub.
- Use `.env.example` to share default values.
- Ensure your bot has permissions to **create channels and manage messages**.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a Pull Request with a description of your changes

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file.
