import discord
import os
import sqlite3
from dotenv import load_dotenv
from datetime import date

load_dotenv()
token = os.getenv("TOKEN")

#os.chdir("/home/tristan/Documents/Projects/Anniminder_Discord_bot/")

class MyClient(discord.Client):
	async def on_ready(self):
		print("Logged on as {0.user}".format(self.user))
	
	async def on_message(self, message):
		if message.author == self.author:
			return
		
		if message.content.startswith("myCake is"):
			await message.channel.send("Work still ongoing")

client = MyClient()

client.run(token)
