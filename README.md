# README.md

## Discord Bot Project

A professional, modular Discord bot built with discord.py 2.x. Supports prefix and slash commands, rich embeds, buttons, select menus, DM responses, logging, and more. Designed for production use on high-performance servers.

### Features
- Modular cogs in `features/` for easy extension.
- Auto-loading of cogs on startup.
- Custom help command.
- Error handling and logging.
- Secure config with environment variables.
- Example cogs: hello (simple command), shop (embeds, buttons, selects, DMs).
- Ready for multi-server deployment.

### Installation
1. Ensure Python 3.10+ is installed.
2. Clone the repo: `git clone <repo-url>`
3. Install dependencies: `pip install -r requirements.txt`
4. Set environment variables: `export DISCORD_TOKEN=your-bot-token` (Linux/Mac) or equivalent on Windows.
5. Run the bot: `python bot.py`

### Usage
- Prefix commands: `!hello`
- Slash commands: `/hello`
- Add bot to server via Discord Developer Portal.
- Configure in `config.py` (prefix, log level).

### Adding New Features
1. Create a new file in `features/` (e.g., `myfeature.py`).
2. Define a Cog class:
   ```python
   from discord.ext import commands

   class MyFeature(commands.Cog):
       def __init__(self, bot):
           self.bot = bot

       @commands.hybrid_command(name='mycommand')
       async def mycommand(self, ctx):
           await ctx.send('Hello from new feature!')

   async def setup(bot):
       await bot.add_cog(MyFeature(bot))