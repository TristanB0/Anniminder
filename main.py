import asyncio
import sqlite3
from datetime import date, datetime
from os import getenv
from random import choice

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
token = getenv("TOKEN")

con = sqlite3.connect("database.db3")
cur = con.cursor()
#cur.execute("drop table user;")    # for debugging only
#cur.execute("drop table guild;")   # for debugging only
cur.execute("""CREATE TABLE IF NOT EXISTS user (
   				user_id INTEGER,
                guild_id INTEGER,
                birth DATE NOT NULL,
                PRIMARY KEY (user_id, guild_id));""")
cur.execute("""CREATE TABLE IF NOT EXISTS guild (
                guild_id INTEGER,
                channel_id INTEGER,
                PRIMARY KEY (guild_id));""")
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

        await self.change_presence(activity=discord.Game("to remember... /help"))

    async def on_disconnect(self):
        print("Disconnected from discord")

    async def on_member_join(self, member):
        """Send a message to inform about the presence of the bot"""
        await member.send("""
        Hello! \n
        You joined {0} where I am already in. I am a bot to remind birthdays of people who decide to share theirs. \n
        All you have to do is to type /add_birthday and follow the instructions. \n
        You can find more help using /help. \n
        I will wish you a happy birthday the right day.
        """.format(member.guild.name))
    
    async def on_member_remove(self, member):
        """Remove the user from the database if he leaves the server"""
        cur.execute("DELETE FROM user WHERE user_id = ? AND guild_id = ?;", (member.id, member.guild.id))
        con.commit()

    async def on_guild_join(self, guild):
        """When the bot join a new server"""
        channel = self.get_channel(guild.id)
        await channel.send("""
        Hello! \n
        Thank you for adding me to your server. \n
        For your information, an administrator must configure me by using /setup_channel [the channel you want the messages in] first. \n
        Don't forget /help to get help. \n
        """)

    async def on_guild_remove(self, guild):
        """Remove guild's users from the database when the guild is removed or the bot is kicked / banned"""
        cur.execute("DELETE FROM guild WHERE guild_id = ?;", (guild.id,))
        cur.execute("DELETE FROM user WHERE guild_id = ?;", (guild.id,))
        con.commit()

    async def fetch_birthdays(self):
        """Says happy birthday if it is the correct day"""
        await self.wait_until_ready()
        while not self.is_closed():
            todays_date = datetime.now()
            if todays_date.hour == 10 and todays_date.minute == 00:
                cur.execute("SELECT * FROM user WHERE STRFTIME('%m-%d', birth) = STRFTIME('%m-%d', 'now');")
                for row in cur.fetchall():
                    curGuild = con.cursor()
                    curGuild.execute("SELECT channel_id FROM guild WHERE guild_id = ?;", (row[1],))
                    channel = self.get_channel(curGuild.fetchone()[0])
                    await channel.send(choice(birthday_messages).format(self.get_user(row[0]).mention, (todays_date.year - datetime.strptime(row[2], "%Y-%m-%d").year)))

            await asyncio.sleep(60)


birthday_messages = [
    "{0} is {1} years old!",
    "Have a good day {0}, you are {1} right?",
    "Congratulations {0} for your {1} birthday!",
    "Happy birthday {0}! You are {1} years old today!",
    "Happy {1} birthday {0}!",
    "Already {1} years old {0}? Time flies!"
    ]

intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.message_content = True

client = MyClient(intents=intents)

tree = app_commands.CommandTree(client)


@tree.command(name="help", description="Get help")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("""
    /help - Show this message \n
    /set_channel [channel] - Set the channel where the bot will send the birthday messages \n
    /add_birthday [YYYY] [MM] [DD] - Add or edit your birthday \n
    /remove_birthday - Remove your birthday \n
    /get_birthday [user] - Get another user's birthday \n \n
    Made by Tristan BONY --> https://www.tristanbony.me
    """, ephemeral=True)
    return None


@tree.command(name="setup_channel", description="Set the channel for the birthday announcements")
@app_commands.checks.has_permissions(administrator=True)
async def setup_channel(interaction: discord.Interaction, channel: discord.TextChannel):
	cur.execute("INSERT OR REPLACE INTO guild VALUES (?, ?);", (interaction.guild.id, channel.id))
	con.commit()
	await interaction.response.send_message("Channel set to {0}.".format(channel.mention), ephemeral=True)
	return 0


@tree.command(name="add_birthday", description="Add or edit your birthday")
async def add_birthday(
        interaction: discord.Interaction,
        year: app_commands.Range[int, 1900, datetime.now().date().year - 13],
        month: app_commands.Range[int, 1, 12],
        day: app_commands.Range[int, 1, 31]):
    birth = date(year, month, day)

    try:
        cur.execute("INSERT OR REPLACE INTO user VALUES (?, ?, ?);", (interaction.user.id, interaction.guild.id, birth))

        cur.execute("SELECT * FROM guild WHERE guild_id = ?;", (interaction.guild.id,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO guild VALUES (?, ?);", (interaction.guild.id, interaction.channel.id))

        con.commit()

        await interaction.response.send_message("Your birthday is set to {0}.".format(birth.strftime("%B %d, %Y")), ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Are you sure you entered your birthday correctly? For information, you entered {0}-{1}-{2} (format YYYY-MM-DD).".format(year, month, day), ephemeral=True)
        con.rollback()


@tree.command(name="remove_birthday", description="Remove your birthday")
async def remove_birthday(interaction: discord.Interaction):
    cur.execute("DELETE FROM user WHERE user_id = ? AND guild_id = ?;", (interaction.user.id, interaction.guild.id))
    con.commit()
    await interaction.response.send_message("Your birthday has been removed.", ephemeral=True)


@tree.command(name="get_birthday", description="Get another user's birthday")
async def get_birthday(interaction: discord.Interaction, user: discord.User):
	cur.execute("SELECT * FROM user WHERE user_id = ? AND guild_id = ?;", (user.id, interaction.guild.id))
	row = cur.fetchone()
	if row is None:
		await interaction.response.send_message("{0} has no birthday set.".format(user.mention), ephemeral=True)
	else:
		birth = datetime.strptime(row[2], "%Y-%m-%d")
		await interaction.response.send_message("{0}'s birthday is on {1}.".format(user.mention, birth.strftime("%B %d, %Y")), ephemeral=True)

client.run(token)
