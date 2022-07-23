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
				id INTEGER PRIMARY KEY,
				birth DATE NOT NULL);""")
con.commit()


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.synced = False

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

        if message.content.startswith("remove my cake"):
            cur.execute("DELETE FROM user WHERE id = ?;", (message.author.id,))
            con.commit()

        # Insert / Modify date into database
        if message.content.startswith("my cake is"):
            cur.execute("SELECT * FROM user WHERE id = ?",
                        (message.author.id,))
            L = [int(i) for i in message.content[11:].split("/")]  # YYYY/MM/DD
            # Add date verification
            #print("User", self.get_user(message.author.id), "made a request !")

            if cur.fetchone() is None:
                cur.execute("INSERT INTO user (id, birth) VALUES (?, ?)",
                            (message.author.id, date(L[0], L[1], L[2]).isoformat()))
            else:
                cur.execute("UPDATE user SET birth = ? WHERE id = ?", (date(
                    L[0], L[1], L[2]).isoformat(), message.author.id))

            con.commit()

            await message.reply("Your cake is set to {}".format(date(L[0], L[1], L[2]).strftime("%B %d, %Y")))

        # Stop bot
        if message.content.startswith("cakestop") and message.author.id == 220890887054557184:
            con.commit()
            con.close()
            await client.close()

    async def fetch_birthdays(self, message):
        """Says happy birthday if it is the correct day"""
        todays_date = datetime.today()
        if todays_date.hour == 10 and todays_date.minute == 0:
            cur.execute("SELECT * FROM user WHERE birth = ?",
                        (todays_date.isoformat()))

            for i in cur.fetchall():
                await message.channel.send("{0} is {1} years old".format(discord.get_user(i[0]), (datetime.now().date().year - datetime.strptime(i[2], "%Y-%m-%d").date().year)))


intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.message_content = True

client = MyClient(intents=intents)

tree = app_commands.CommandTree(client)


@tree.command(name="add_birthday", description="Add or edit your birthday")
async def add_birthday(
        interaction: discord.Interaction,
        year: app_commands.Range[int, 1900, datetime.now().date().year],
        month: app_commands.Range[int, 1, 12],
        day: app_commands.Range[int, 1, 31]):
    birth = date(year, month, day)

    cur.execute("SELECT * FROM user WHERE id = ?", (interaction.user.id,))

    if cur.fetchone() is None:
        cur.execute("INSERT INTO user (id, birth) VALUES (?, ?)",
                    (interaction.user.id, birth))
    else:
        cur.execute("UPDATE user SET birth = ? WHERE id = ?",
                    (birth, interaction.user.id))

    con.commit()

    await interaction.response.send_message("Your cake is set to {}".format(birth.strftime("%B %d, %Y")), ephemeral=True)


@tree.command(name="remove_birthday", description="Remove your birthday")
async def remove_birthday(interaction: discord.Interaction):
    cur.execute("DELETE FROM user WHERE id = ?;", (interaction.user.id,))
    con.commit()
    await interaction.response.send_message("Your birthday has been removed", ephemeral=True)


client.run(token)
