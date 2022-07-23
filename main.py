import asyncio
import os
import sqlite3
from datetime import date, datetime

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TOKEN")

con = sqlite3.connect("users.db3")
cur = con.cursor()
#cur.execute("drop table user;")
cur.execute("""CREATE TABLE IF NOT EXISTS user (
				id_user INTEGER,
                id_guild INTEGER,
				birth DATE NOT NULL,
                PRIMARY KEY (id_user, id_guild));""")
con.commit()


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.synced = False

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.fetch_birthdays())

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print("Logged on as {0}".format(self.user))

    async def on_disconnect(self):
        print("Disconnected from discord")

    async def on_message(self, message):
        if message.author == self.user:
            return 0

        # Stop bot
        if message.content.startswith("cakestop") and message.author.id == 220890887054557184:
            con.commit()
            con.close()
            await client.close()

    async def fetch_birthdays(self):
        """Says happy birthday if it is the correct day"""
        await self.wait_until_ready()
        while not self.is_closed():
            todays_date = datetime.now()
            if todays_date.hour == 21 and todays_date.minute == 31:
                cur.execute("SELECT * FROM user WHERE STRFTIME('%m-%d', birth) = STRFTIME('%m-%d', 'now');")

                for row in cur.fetchall():
                    #print(row)
                    #print("age", todays_date.year - datetime.strptime(row[2], "%Y-%m-%d").year)
                    channel = self.get_channel(376721858218950665) #self.get_channel(i[1])
                    await channel.send("{0} is {1} years old!".format(self.get_user(row[0]).mention, (todays_date.year - datetime.strptime(row[2], "%Y-%m-%d").year)))

            await asyncio.sleep(60)


intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.message_content = True

client = MyClient(intents=intents)

tree = app_commands.CommandTree(client)


@tree.command(name="add_birthday", description="Add or edit your birthday")
async def add_birthday(
        interaction: discord.Interaction,
        year: app_commands.Range[int, 1900, datetime.now().date().year - 18],
        month: app_commands.Range[int, 1, 12],
        day: app_commands.Range[int, 1, 31]):
    birth = date(year, month, day)

    cur.execute("SELECT * FROM user WHERE id_user = ? AND id_guild = ?;", (interaction.user.id, interaction.guild.id))

    if cur.fetchone() is None:
        cur.execute("INSERT INTO user (id_user, id_guild, birth) VALUES (?, ?, ?);", (interaction.user.id, interaction.guild.id, birth))
    else:
        cur.execute("UPDATE user SET birth = ? WHERE id_user = ? AND id_guild = ?;", (birth, interaction.user.id, interaction.guild.id))

    con.commit()

    await interaction.response.send_message("Your cake is set to {}".format(birth.strftime("%B %d, %Y")), ephemeral=True)


@tree.command(name="remove_birthday", description="Remove your birthday")
async def remove_birthday(interaction: discord.Interaction):
    cur.execute("DELETE FROM user WHERE id_user = ? AND id_guild = ?;", (interaction.user.id, interaction.guild.id))
    con.commit()
    await interaction.response.send_message("Your birthday has been removed.", ephemeral=True)


@tree.command(name="stop", description="Stop the bot")
async def stop(interaction: discord.Interaction):
    con.commit()
    con.close()
    await interaction.response.send_message("Stopping the bot...", ephemeral=True)
    await client.close()


client.run(token)
