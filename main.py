import discord
import os
import sqlite3
from dotenv import load_dotenv
from datetime import date
from datetime import datetime


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
	async def on_ready(self):
		print("Logged on as {0}".format(self.user.id))
	
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
			cur.execute("SELECT * FROM user WHERE id = ?", (message.author.id,))
			L = [int(i) for i in message.content[11:].split("/")]	# YYYY/MM/DD
			# Add date verification
			#print("User", self.get_user(message.author.id), "made a request !")

			if cur.fetchone() is None:
				cur.execute("INSERT INTO user (id, birth) VALUES (?, ?)", (message.author.id, date(L[0], L[1], L[2]).isoformat()))
			else:
				cur.execute("UPDATE user SET birth = ? WHERE id = ?", (date(L[0], L[1], L[2]).isoformat(), message.author.id))
			
			con.commit()

			await message.reply("Your cake is set to {}".format(date(L[0], L[1], L[2]).strftime("%B %d, %Y")))
		
		# Stop bot
		if message.content.startswith("cakestop") and message.author.id == 220890887054557184:
			con.commit()
			con.close()
			await client.close()
		
		# Says happy birthday if it is the correct day
		if datetime.now().hour == 10 and datetime.now().minute == 0:
			cur.execute("SELECT * FROM user WHERE birth = ?", (datetime.now().strptime(message.content[11:], "%Y-%m-%d")))
			
			for i in cur.fetchall():
				await message.channel.send("{0} is {1} years old".format(discord.get_user(i[0]), (datetime.now().date().year - datetime.strptime(i[2], "%Y-%m-%d").date().year)))


intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.messages = True

client = MyClient(intents=intents)
client.run(token)
