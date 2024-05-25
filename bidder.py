import json, pysher, queue, requests, threading, notifier
from dateutil import parser as dateparser

from util import *

class Bidder:
	def __init__(self, auction, username, password):
		self.auction = auction
		self.username = username
		self.password = password
		self.bids_queue = queue.Queue()
		self.session = requests.Session()
		self.notif = notifier.Notifier(auction)
		self.connected = False

		# Connect Pusher API
		self.pusher = pysher.Pusher("443cf048ddf5360c8636") # appkey for galabid
		self.pusher.connection.bind('pusher:connection_established', self.connect_handler)
		self.pusher.connect()

	def startAutobidder(self, items, uuid_name_lookup):
		self.uuid_name_lookup = uuid_name_lookup
		self.items = items

		# Autobidder thread
		def _bidderThread():
			while True:
				bid = self.bids_queue.get()
				print(f"Bid {bid[1]} on {bid[0]}")
				self.submitBid(bid[0], bid[1])
		self.bidderThread = threading.Thread(target=_bidderThread,daemon=True)
		self.bidderThread.start()

		# Listen for any new bids
		self.channel.bind('biddingitem.update', onUpdateWrapper(self.biddingItemUpdate))

	def submitBid(self, item, amount):
		self.doPost("bids", {
			"profile": self.profile_uuid,
			"amount": amount,
			"bidding_item": item
		})

	def postComment(self, message, itemName=None):
		if itemName:
			# The UUID doesn't have to be valid, it just has to be a UUID...
			# Also the item name isn't checked in any way - 10/10 security
			item = {"item_name": str(itemName), "item_uuid": "00000000-0000-0000-0000-000000000000", "item_type": "bidding"}
		else:
			# If we aren't commenting on an item, leave the item data blank
			item = {}

		response = self.doPost("/activity-feed-post/", {
			"auction": self.auction,
			"message": message,
		} | item)

	def connect_handler(self, data):
		self.channel = self.pusher.subscribe('auction@' + self.auction)

		# Authenticate session
		response = self.doPost("login", {
			"identity": self.username,
			"password": self.password
		})
		# Save auth to header
		self.session.headers.update({'Authorization': "Token " + response.json()['token']})
		self.token = response.json()['token']
		self.profile_uuid = response.json()['profile']['uuid']

		# Set up authenticated pusher channel/profile
		self.pusher.auth_endpoint="https://api.galabid.com/api/app/pusher/auth/"
		self.pusher.auth_endpoint_headers = {'Authorization': "Token " + self.token}
		self.pusher.subscribe('private-auctionprofile@' + self.profile_uuid)

#		def profileCreate(data):
#			print("===GOT PROFILE===\n\t",data)
#		self.channel.bind('auctionprofile.create', profileCreate)

		self.connected = True

	def doPost(self, endpoint, data=None, headers=None):
		ADDL_HEADERS = {
			"Content-Type": "application/json"
		}
		response = self.session.post(
			"https://api.galabid.com/api/app/auctions/" + self.auction + "/" + endpoint + "/",
			data=json.dumps(data) if data is not None else None,
			headers=(headers if headers is not None else {}) | ADDL_HEADERS
		)
		if False: # Debug flag
			print("")
			print("REQUEST:")
			print("-> URL:", response.request.url)
			print("-> HEADERS:", response.request.headers)
			print("-> BODY", response.request.body)
			print("RESPONSE:")
			print("-> URL:", response.url)
			print("-> HEADERS:", response.headers)
			print("-> BODY", response.text)
			print("")
		return response

	def biddingItemUpdate(self, update):
		# Convert from JSON to Python objects
		update = json.loads(update)
		bids = update['winning_bids']
		item_uuid = update['item']

		# Notify about top winning bid (newest one) even if we aren't going to actually up our own bid
		top_bid = newest_bid = bids[0]
		for bid in bids:
			bid['created'] = dateparser.parse(bid['created'])
			if bid['created'] > newest_bid['created']:
				newest_bid = bid

		# Send push notification about bid
		self.notif.notify({
			"username": newest_bid['profile_full_name'],
			"content": f"> Bid ${newest_bid['amount']} on \"{self.uuid_name_lookup[item_uuid]}\""
		})

		# Log bid
		message = f"[{currentTime()}] Updated item '{self.uuid_name_lookup[item_uuid]}' with current top bid set at '{top_bid['created']}' to {top_bid['amount']} by '{top_bid['profile_full_name']}' and '{newest_bid['profile_full_name']}' just bid ${newest_bid['amount']} (at '{newest_bid['created']}')"
		with open("galabid.log","a") as f:
			f.write(message)
			f.write("\n")
		print(message)

		# Check UUID of item
		if item_uuid not in self.items:
			# Not an item we care about, ignore it
			print("Ignore this item")
			return

		# Check if we have a winning bid already
		if self.profile_uuid in [bid['profile_uuid'] for bid in bids]:
			# We have a winning bid on this item
			print("Already have the winning bid for this item")
			return

		# Check if we can afford to bid on the item again
		next_bid = update['minimum_next_bid']
		max_bid = self.items[item_uuid]
		if max_bid > 0 and next_bid > max_bid:
			print(f"NEXT MINIMUM BID ({next_bid}) FOR ITEM '{self.uuid_name_lookup[item_uuid]}' EXCEEDS MAX BID ({max_bid})!")
			self.notif.notify({
				"username": "Galabid Autobidder",
				"content": f"[Autobidder] Unable to increase bid for item '{self.uuid_name_lookup[item_uuid]}'! Next minimum bid is ${next_bid}, which exceeds the max bid of ${max_bid}!"
			})
			return

		print(f"Now bid {next_bid}...")
		self.bids_queue.put((newest_bid['bidding_item'], next_bid))
