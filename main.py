import discord
import os
import sqlite3
from dotenv import load_dotenv
from datetime import date


load_dotenv()
token = os.getenv("TOKEN")

con = sqlite3.connect("users.db3")
cur = con.cursor()
#cur.execute("drop table user;")
cur.execute("""CREATE TABLE IF NOT EXISTS user (
				id INTEGER PRIMARY KEY,
				name TEXT NOT NULL,
				birth DATE NOT NULL);""")
con.commit()


class MyClient(discord.Client):
	async def on_ready(self):
		print("Logged on as {0}".format(self.user.id))
	
	async def on_message(self, message):		
		if message.author == self.user:
			return 0
		
		if message.content.startswith("my cake is"):
			await message.channel.send("Work still ongoing")
			L = [int(i) for i in message.content[11:].split("/")]
			cur.execute("INSERT INTO user (id, name, birth) VALUES (?, ?, ?)", (message.author.id, message.author.name, date(L[2], L[1], L[0]).isoformat()))
			con.commit()
		
		if message.content.startswith("cakestop") and message.author.id == 220890887054557184:
			con.commit()
			con.close()
			await client.close()


intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.messages = True

client = MyClient(intents=intents)
client.run(token)
