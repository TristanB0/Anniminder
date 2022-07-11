import discord
import os
import sqlite3
from dotenv import load_dotenv
from datetime import date

load_dotenv()
token = os.getenv("TOKEN")

sqlite3.connect("users.db3")
sqlite3.Connection().execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, birth DATETIME NOT NULL, created_at DATETIME DEFAULT CURRENT_DATE, updated_at DATETIME DEFAULT CURRENT_DATE);")


class MyClient(discord.Client):
	async def on_ready(self):
		print("Logged on as {0.user}".format(self.user))
	
	async def on_message(self, message):
		if message.author == self.author:
			return 0
		
		if message.content.startswith("my cake is"):
			await message.channel.send("Work still ongoing")
			#sqlite3.Connection().execute("insert into ...")
		
		if message.content.startswith("cakestop") and message.author.id == "220890887054557184":
			client.close()


client = MyClient()

client.run(token)
