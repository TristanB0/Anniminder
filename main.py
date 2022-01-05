import discord
import os
#from dotenv import load_dotenv

#load_dotenv()
token = os.getenv("TOKEN")

#os.chdir("/home/tristan/Documents/Projects/Anniminder_Discord_bot/")

class MyClient(discord.Client):
	async def on_ready(self):
		print("Logged on as {0.user}".format(self.user))

client = MyClient()

#client.run(token)
