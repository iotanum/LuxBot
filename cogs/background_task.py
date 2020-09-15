from discord.ext import tasks, commands
import discord

from cogs import twitter_henti

import traceback
import asyncio
import random
import os


class Task(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.twitter = twitter_henti.Twitter()

        self.tracked_channels = []
        self.batch_of_tweets = []

        self.background_task.start()

    async def log_fatal_error_to_creator_dm(self):
        creator_discord_id = 450567441437687818

        try:
            await self.bot.get_user(creator_discord_id).send(f"```{traceback.format_exc()}```\n")

        except discord.errors.HTTPException:
            traceback_error = traceback.format_exc().split('Traceback')
            api_response = traceback_error[0][-1000:]
            api_response = traceback_error[1][-1000:] if api_response is "" else api_response

            await self.bot.get_user(creator_discord_id).send(f"```{api_response}```\n")

    async def send_henti_tweets_to_channel(self, tweets):
        for channel_id in self.tracked_channels:
            channel = self.bot.get_channel(channel_id)

            for tweet_url in tweets:
                await channel.send(tweet_url)
                await asyncio.sleep(random.randint(1, 3))

    async def _update_read_tracked_channels_in_file(self, update=False):
        if not os.path.exists('channels.txt'):
            with open('channels.txt', 'w'): pass

        if update:
            with open('channels.txt', 'w') as file:
                file.write(",".join(str(channel) for channel in self.tracked_channels))

        else:
            with open('channels.txt', 'r') as file:
                channels = file.read()

                if channels == '':
                    self.tracked_channels = []
                    return

                self.tracked_channels = channels.split(",")

    @commands.command(brief="Lock a channel where Lux is gonna post.")
    async def here(self, ctx):
        if ctx.channel.id not in self.tracked_channels:
            self.tracked_channels.append(ctx.channel.id)
            print(self.tracked_channels)
            await self._update_read_tracked_channels_in_file(update=True)
            print(f"Tracking in: {len(self.tracked_channels)} channels.")
            await ctx.message.add_reaction('\U0001f44d')

    @commands.command(brief="Remove channel from tracked list.")
    async def nothere(self, ctx):
        if ctx.channel.id in self.tracked_channels:
            self.tracked_channels.remove(ctx.channel.id)
            await self._update_read_tracked_channels_in_file(update=True)
            print(f"Tracking in: {len(self.tracked_channels)} channels.")
            await ctx.message.add_reaction('\U0001f44d')

    async def _reset_gathered_tweets(self):
        self.twitter.gathered_tweets['tweet_urls'] = []

    @tasks.loop(minutes=15, reconnect=True)
    async def background_task(self):
        try:
            print(self.tracked_channels)
            if len(self.tracked_channels) >= 1:
                gathered_tweets = await self.twitter.get_all_henti_tweets()

                print("Found:", len(gathered_tweets['tweet_urls']), 'tweets.')
                # Ideally I want at least 10 tweets per batch to be sent
                if len(self.batch_of_tweets) <= 10:
                    self.batch_of_tweets += gathered_tweets['tweet_urls']

                    # This 'background task' is already sleeping 15 minutes after this
                    # ends it's execution, thus placeholder 1s sleep time
                    sleep_timer = 1
                    print(f"Not enough, sleeping {sleep_timer}s, in total {len(self.batch_of_tweets)} now.")

                if len(self.batch_of_tweets) >= 10:
                    await self.send_henti_tweets_to_channel(self.batch_of_tweets)
                    self.batch_of_tweets = []
                    sleep_timer = 30 * random.randint(120, 320)
                    print(f"More than enough, sending in. Sleeping {sleep_timer}s")

                # Sleep a random timer from 1h to 3h
                await asyncio.sleep(sleep_timer)
                print(f"Slept {sleep_timer}s. "
                      f"{f'Posted {len(self.batch_of_tweets)} tweets.' if len(self.batch_of_tweets) >= 10 else ''}")

                # Reset gathered tweets after a send
                await self._reset_gathered_tweets()

        except Exception as e:
            await self.log_fatal_error_to_creator_dm()

    @background_task.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()
        await self._update_read_tracked_channels_in_file()
        print(f"Logged in as {self.bot.user}.")


def setup(bot):
    bot.add_cog(Task(bot))
