import json, pysher
from discord_webhook import DiscordWebhook, DiscordEmbed
from util import *
from config import *

class Notifier:
	def __init__(self, auction):
		self.previousMessages = []
		self.auction = auction

		def connect_handler(data):
			self.channel = self.pusher.subscribe('auction@' + self.auction)
			self.channel.bind('activityfeedpost.create', onUpdateWrapper(self.activityFeedPost))

		self.pusher = pysher.Pusher("443cf048ddf5360c8636") #appkey for galabid
		self.pusher.connection.bind('pusher:connection_established', connect_handler)
		self.pusher.connect()

	def notify(self, notifArgs, embedArgs=None):
		webhook = DiscordWebhook(
			url=DISCORD_WEBHOOK_URL,
			avatar_url="https://s3-ap-southeast-2.amazonaws.com/frontend.galabid.com/static/images/favicon/favicon-32x32.png",
			**notifArgs
		)
		if embedArgs:
			embed = DiscordEmbed(**embedArgs)
			webhook.add_embed(embed)

		response = webhook.execute()
		# TODO: Parse response

	def activityFeedPost(self, data):
		# Convert from JSON to Python objects
		data = json.loads(data)

		# Don't notify multiple times for the same message
		if data in self.previousMessages:
			return
		self.previousMessages.append(data)

		message = f"[{currentTime()}] New message: {data['profile_full_name']} said \"{data['message']}\""
		if data['item_name']:
			message += f" on item: '{data['item_name']}'"
			embed = {
				"description": f"Item '{data['item_name']}'"
			}
		else:
			embed = None

		self.notify({
			"username": data['profile_full_name'],
			"content": data['message'],
		}, embed)

		with open("galabid.log","a") as f:
			f.write(message)
			f.write("\n")
		print(message)
