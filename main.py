import discord
import os
import sqlite3
from dotenv import load_dotenv
from datetime import date

load_dotenv()
token = os.getenv("TOKEN")

#sqlite3.connect("users.db3")
#sqlite3.Connection().execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, name TEXT NOT NULL, birth DATETIME NOT NULL, created_at DATETIME DEFAULT CURRENT_DATE, updated_at DATETIME DEFAULT CURRENT_DATE);")


class MyClient(discord.Client):
	async def on_ready(self):
		print("Logged on as {0}".format(self.user.id))
	
	async def on_message(self, message):		
		if message.author == self.user:
			return 0
		
		if message.content.startswith("my cake is"):
			await message.channel.send("Work still ongoing")
			#sqlite3.Connection().execute("BEGIN TRANSACTION;")
			#sqlite3.Connection().execute("insert into ...")
			#sqlite3.Connection().execute("COMMIT;")
		
		if message.content.startswith("cakestop") and message.author.id == 220890887054557184:
			await client.close()

intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.messages = True

client = MyClient(intents=intents)
client.run(token)
