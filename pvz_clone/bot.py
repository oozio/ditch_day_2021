import discord
import logging
import os

from dotenv import load_dotenv

from game import Game


class GameBot(discord.ext.commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.reactions = True
        intents.messages = True

        super().__init__(command_prefix='!', intents=intents)
        self.logger = logging.getLogger('discord')
    
    async def on_ready(self):
        self.logger.info(f'Client logged in as {self.user}')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    bot = GameBot()
    bot.add_cog(Game(bot))
    bot.run(TOKEN)
