import asyncio
import logging
import sqlite3
import uuid
from datetime import date, datetime
from os import getenv, makedirs, path
from random import choice

import discord
from discord import app_commands
from dotenv import load_dotenv

if not path.exists("logs"):
    makedirs("logs")

load_dotenv()
token = getenv("DISCORD_TOKEN")

con = sqlite3.connect("database.db3")
cur = con.cursor()
# cur.execute("drop table user;")    # for debugging only
# cur.execute("drop table guild;")   # for debugging only
# cur.execute("drop table event;")   # for debugging only
cur.execute("""CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER,
                guild_id INTEGER,
                birth DATE NOT NULL,
                PRIMARY KEY (user_id, guild_id));""")
cur.execute("""CREATE TABLE IF NOT EXISTS guild (
                guild_id INTEGER,
                channel_id INTEGER,
                PRIMARY KEY (guild_id));""")
cur.execute("""CREATE TABLE IF NOT EXISTS event (
                event_id TEXT,
                guild_id INTEGER,
                event_date DATE NOT NULL,
                event_content TEXT,
                PRIMARY KEY (event_id));""")
con.commit()


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.synced = False

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.fetch_birthdays())
        self.bg_task = self.loop.create_task(self.new_log())

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        
        logging.log(logging.INFO, "Logged on as {0}".format(self.user))

        await self.change_presence(activity=discord.Game("to remember... /help"))

    async def on_disconnect(self):
        logging.log(logging.WARNING, "Disconnected from discord")

    async def on_member_join(self, member):
        """Send a message to inform about the presence of the bot"""
        await member.send("""
Hello! 
You joined {0} where I am already in. I am a bot to remind birthdays of people who decide to share theirs.
All you have to do is to type /add_birthday and follow the instructions.
You can find more help using /help.
I will wish you a happy birthday the right day.
        """.format(member.guild.name))

        logging.log(logging.DEBUG, "User {0} joined {1}".format(member.id, member.guild.id))

    async def on_member_remove(self, member):
        """Remove the user from the database if he leaves the server"""
        cur.execute("DELETE FROM user WHERE user_id = ? AND guild_id = ?;", (member.id, member.guild.id))
        con.commit()

        logging.log(logging.DEBUG, "User {0} left {1}".format(member.id, member.guild.id))

    async def on_guild_join(self, guild):
        """When the bot join a new server"""
        channel = self.get_channel(guild.id)
        await channel.send("""
Hello!
Thank you for adding me to your server.
For your information, an administrator must configure me by using /setup_channel [the channel you want the messages in] first or by default it will be set in the channel you will use either add_birthday or add_event first.
Don't forget /help to get help.
        """)

        logging.log(logging.DEBUG, "Bot added to {0}".format(guild.id))

    async def on_guild_remove(self, guild):
        """Remove guild's users from the database when the guild is removed or the bot is kicked / banned"""
        cur.execute("DELETE FROM guild WHERE guild_id = ?;", (guild.id,))
        cur.execute("DELETE FROM user WHERE guild_id = ?;", (guild.id,))
        cur.execute("DELETE FROM event WHERE guild_id = ?;", (guild.id,))
        con.commit()

        logging.log(logging.DEBUG, "Bot removed from {0}".format(guild.id))

    async def fetch_birthdays(self):
        """Says happy birthday if it is the correct day"""
        await self.wait_until_ready()
        while not self.is_closed():
            todays_date = datetime.now()
            if todays_date.hour == 10 and todays_date.minute == 00:
                logging.log(logging.DEBUG, "Function fetch_birthdays was programmatically called")

                cur.execute("SELECT * FROM user WHERE STRFTIME('%m-%d', birth) = STRFTIME('%m-%d', 'now');")
                for row in cur.fetchall():
                    cur_guild = con.cursor()
                    cur_guild.execute("SELECT channel_id FROM guild WHERE guild_id = ?;", (row[1],))
                    channel = self.get_channel(cur_guild.fetchone()[0])
                    await channel.send(choice(birthday_messages).format(self.get_user(row[0]).mention, (
                                todays_date.year - datetime.strptime(row[2], "%Y-%m-%d").year)))

            await asyncio.sleep(60)
    
    async def fetch_events(self):
        """Remind of an event if it is the correct day"""
        await self.wait_until_ready()
        while not self.is_closed():
            todays_date = datetime.now()
            if todays_date.hour == 10 and todays_date.minute == 00:
                logging.log(logging.DEBUG, "Function fetch_events was programmatically called")

                cur.execute("SELECT * FROM event WHERE STRFTIME('%m-%d', event_date) = STRFTIME('%m-%d', 'now');")
                for row in cur.fetchall():
                    cur_guild = con.cursor()
                    cur_guild.execute("SELECT channel_id FROM guild WHERE guild_id = ?;", (row[1],))
                    channel = self.get_channel(cur_guild.fetchone()[0])
                    await channel.send("Reminder! Someone programmed an event for today saying:\n\n{0}".format(row[3]))

            await asyncio.sleep(60)
    
    async def new_log(self):
        """Make a new log file"""
        now = datetime.now()
        handlers = [logging.FileHandler(filename="logs/{0}.log".format(now.strftime("%Y-%m-%d %H:%M:%S")), encoding="utf-8"), logging.StreamHandler()]
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S", handlers=handlers)
        
        logging.log(logging.DEBUG, "Created a new log file")

        await asyncio.sleep(86400)  # Wait a day


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
    await interaction.response.send_message(
        """
/help - Show this message
/set_channel [channel] - Set the channel where the bot will send the birthday messages
/add_birthday [YYYY] [MM] [DD] - Add or edit your birthday
/remove_birthday - Remove your birthday
/get_birthday [user] - Get another user's birthday
    
Made by Tristan BONY --> https://www.tristanbony.me
    """, ephemeral=True)


@tree.command(name="setup_channel", description="Set the channel for the birthday announcements")
@app_commands.checks.has_permissions(administrator=True)
async def setup_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    cur.execute("INSERT OR REPLACE INTO guild VALUES (?, ?);", (interaction.guild.id, channel.id))
    con.commit()
    
    logging.log(logging.DEBUG, "Guild {0} setted up a channel".format(interaction.guild.id))

    await interaction.response.send_message("Channel set to {0}.".format(channel.mention), ephemeral=True)


@tree.command(name="add_birthday", description="Add or edit your birthday")
async def add_birthday(
        interaction: discord.Interaction,
        year: app_commands.Range[int, 1900, datetime.now().date().year - 13],
        month: app_commands.Range[int, 1, 12],
        day: app_commands.Range[int, 1, 31]):
    birth = date(year, month, day)

    logging.log(logging.DEBUG, "Command add_birthday was called with value {0}-{1}-{2}".format(year, month, day))
    
    try:
        cur.execute("INSERT OR REPLACE INTO user VALUES (?, ?, ?);", (interaction.user.id, interaction.guild.id, birth))

        cur.execute("SELECT * FROM guild WHERE guild_id = ?;", (interaction.guild.id,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO guild VALUES (?, ?);", (interaction.guild.id, interaction.channel.id))

        con.commit()

        await interaction.response.send_message("Your birthday is set to {0}.".format(birth.strftime("%B %d, %Y")),
                                                ephemeral=True)
    except ValueError:
        await interaction.response.send_message(
            "Are you sure you entered your birthday correctly? For information, you entered {0}-{1}-{2} (format YYYY-MM-DD).".format(
                year, month, day), ephemeral=True)
        con.rollback()
    

@tree.command(name="remove_birthday", description="Remove your birthday")
async def remove_birthday(interaction: discord.Interaction):
    cur.execute("DELETE FROM user WHERE user_id = ? AND guild_id = ?;", (interaction.user.id, interaction.guild.id))
    con.commit()

    logging.log(logging.DEBUG, "Command remove_birthday was called")
    
    await interaction.response.send_message("Your birthday has been removed.", ephemeral=True)


@tree.command(name="get_birthday", description="Get another user's birthday")
async def get_birthday(interaction: discord.Interaction, user: discord.User):
    logging.log(logging.DEBUG, "Command get_birthday was called in server {0} to get {1}".format(interaction.guild.id, user.id))
    
    cur.execute("SELECT * FROM user WHERE user_id = ? AND guild_id = ?;", (user.id, interaction.guild.id))
    row = cur.fetchone()
    if row is None:
        await interaction.response.send_message("{0} has no birthday set.".format(user.mention), ephemeral=True)
    else:
        birth = datetime.strptime(row[2], "%Y-%m-%d")
        await interaction.response.send_message(
            "{0}'s birthday is on {1}.".format(user.mention, birth.strftime("%B %d, %Y")), ephemeral=True)


@tree.command(name="add_event", description="Add an event")
async def add_event(
        interaction: discord.Interaction,
        year: app_commands.Range[int, datetime.now().date().year, 2100],
        month: app_commands.Range[int, 1, 12],
        day: app_commands.Range[int, 1, 31],
        event_content: str):
    logging.log(logging.DEBUG, "Command add_event was called in server {0} with date {1}-{2}-{3}".format(interaction.guild.id, year, month, day))

    event_date = date(year, month, day)
    event_id = uuid.uuid4().__str__()

    try:
        cur.execute("INSERT OR REPLACE INTO event VALUES (?, ?, ?, ?);", (event_id, interaction.guild.id, event_date, event_content))

        cur.execute("SELECT * FROM guild WHERE guild_id = ?;", (interaction.guild.id,))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO guild VALUES (?, ?);", (interaction.guild.id, interaction.channel.id))

        con.commit()

        await interaction.response.send_message("The event {0} is set to {1}. Keep the ID in case you want to cancel the event later."
                                                .format(event_id, event_date.strftime("%B %d, %Y")),ephemeral=True)
    except ValueError:
        await interaction.response.send_message(
            "Are you sure you entered the date correctly? For information, you entered {0}-{1}-{2} (format YYYY-MM-DD).".format(
                year, month, day), ephemeral=True)
        con.rollback()


client.run(token)
