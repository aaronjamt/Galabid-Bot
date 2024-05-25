# TODO: Add feature to use number keys to jump to items in menu
# TODO: Update minimum bid value in TUI mode, currently it just loads once at startup
import sys, requests, time, bidder
from config import *

RUNNING_HEADLESS = not sys.stdin.isatty() or ('HEADLESS' in sys.argv)

bidders = []
items = {}
uuids_to_names = {}

print("Logging into Galabid accounts...")
for acc in accounts:
	bidders.append(
		bidder.Bidder(
			acc['auction'],	 # The name of the auction
			acc['username'], # The username/email of the account
			acc['password'], # The password of the account
		)
	)

print("Fetching auction items (this may take a while, especially on large auctions!)...")
for acc in accounts:
	if acc['auction'] not in items:
		# Look up auction's items
		items[acc['auction']] = requests.get("https://api.galabid.com/api/app/auctions/"+acc['auction']+"/items/").json()['results']
		uuids_to_names |= {i['uuid']: i['name'] for i in items[acc['auction']]}

print("Ready to run, waiting for Galabid...")
# Wait for all `bidder[*].connected` flags to be True
while True:
	time.sleep(0.1)
	for bidder in bidders:
		if not bidder.connected:
			continue
	break

if RUNNING_HEADLESS:
	# Run headless autobidder
	print("Running!")

	# Start autobidders and join the threads (will basically just wait for the program to exit)
	[bidders[i].startAutobidder(accounts[i]['items'], uuids_to_names) for i in range(len(accounts))]
	[bidder.bidderThread.join() for bidder in bidders]
else:
	# Run headful CLI
	from getch import getch as _getch
	import shutil

	# Wrapper for getch to echo the typed char and (optionally) to only accept certain chars
	def getch(allowed=None):
		if allowed:
			char = 'None'
			while char.lower() not in [i.lower() for i in allowed]:
				char = _getch()
		else:
			char = _getch()
		print(char)
		return char

	ANSI_CLEAR = "\x1B[H\x1B[J"
	ANSI_RESET = "\x1B[0m"
	ANSI_ITALIC = "\x1B[3m"
	ANSI_UNDERLINE = "\x1B[4m"
	ANSI_INVERT = "\x1B[7m"

	_HEADER = f"{ANSI_CLEAR}Running Galabid control panel!\n"

	def doMenu(title, items):
		item_idx = 0
		while True:
			# Recompute every time we refresh in case the terminal is resized
			termSize = shutil.get_terminal_size((80, 20))
			maxItems = termSize.lines - 6 # Subtract 6 to leave room for header, title, and cursor
			maxWidth = termSize.columns

			# We create a string, fill it with the menu data, then print all at once
			# to minimize screen scrolling/flickering/cursor movement during redraw
			menu = ""

			menu += HEADER + "\n"
			menu += title + "\n"

			if len(items) == 0:
				menu += "No items available! Press any key to return\n\n"
				print(menu)
				_getch()
				return None

			# Only show maxItems items, but center around the highlighted item
			minIdx = max(0, item_idx - (maxItems//2))
			maxIdx = min(len(items), minIdx + maxItems)
			if maxIdx - minIdx < maxItems:
				minIdx = max(0, maxIdx - maxItems)

			# Print list of items
			for i in range(minIdx,maxIdx):
				prefix = ""
				if i == item_idx:
					prefix = ANSI_INVERT
				item = ''.join([str(i) for i in [
					" ", # Space at beginning of line to make it clear it's a part of the list
					i+1, ". ", # Show index of item (but add one to show in the human 1-indexed format)
					ANSI_INVERT if i == item_idx else "", # Invert if selected
					items[i]['name'], # Name of the item
					''.join([
						" (min bid $",
						str(items[i]['bidding_item']['minimum_next_bid']),
						")"
					]) if 'bidding_item' in items[i] else '',
					ANSI_RESET # Reset if inverted
				]])

				if len(item) > maxWidth:
					item = item[:maxWidth]

				menu += item + "\n"

			# Print menu and wait for user input
			print(menu, end="")
			got = _getch()

			if got == '\n':
				break
			elif got == 'q':
				item_idx = None # No selection made
				break
			elif got == '\x1B':
				# Escape sequence
				if _getch() == '[':
					got = _getch()
					if got == 'A':
						# Up arrow
						item_idx -= 1
						if item_idx < 0:
							item_idx += len(items)
					elif got == 'B':
						# Down arrow
						item_idx += 1
						if item_idx >= len(items):
							item_idx -= len(items)
					elif got == 'C':
						# Right arrow
						break
					elif got == 'D':
						# Left arrow
						item_idx = None # No selection made
						break

					elif got == 'H':
						# Home
						item_idx = 0
					elif got == 'F':
						# End
						item_idx = len(items) - 1
					elif got == '5' and _getch() == '~':
						# Page up
						item_idx -= maxItems
						if item_idx < 0:
							item_idx = 0
					elif got == '6' and _getch() == '~':
						# Page down
						item_idx += maxItems
						if item_idx > len(items):
							item_idx = len(items) - 1
			elif got in '0123456789':
				# Subtract 1 because the index is 0-based
				item_idx = (10 if got == '0' else int(got)) - 1

		print("\n")
		return item_idx

	HEADER = _HEADER
	currentAccountIdx = doMenu("Select an account:", accounts)
	if currentAccountIdx is None:
		print("Goodbye!")
		exit()

	while True:
		currentAccount = accounts[currentAccountIdx]
		currentBidder = bidders[currentAccountIdx]

		HEADER = _HEADER
		HEADER += f"Auction: {ANSI_ITALIC}{currentAccount['auction']}{ANSI_RESET}\n"
		HEADER += f"Welcome back, {currentAccount['name']}\n"

		print(HEADER)
		print("What do you want to do? You can:")
		print(f"* {ANSI_UNDERLINE}B{ANSI_RESET}id on an item")
		print(f"* send a {ANSI_UNDERLINE}M{ANSI_RESET}essage")
		print(f"* leave a {ANSI_UNDERLINE}C{ANSI_RESET}omment on an item")
		print(f"* change {ANSI_UNDERLINE}A{ANSI_RESET}ccounts")
		print(f"* {ANSI_UNDERLINE}Q{ANSI_RESET}uit")
		print("[bmcaq] > ", end="", flush=True)

		cmd = getch("bmcaq")
		if cmd.lower() == "b":
			item_idx = doMenu("Select an item to bid on:", items[currentAccount['auction']])
			if item_idx is not None:
				item = items[currentAccount['auction']][item_idx]['bidding_item']['uuid']

				amount = input("How much do you want to bid?\n> $")
				try:
					amount = int(amount)
				except:
					print("Amount can only be a whole number integer! Do not add comma(s), period(s), or other letters or symbols.")
					continue
				print("Bid? [yN] ", end="", flush=True)
				if getch("yn").lower() == 'y':
					currentBidder.submitBid(item, amount)
		elif cmd.lower() == "m":
			msg = input("What is the message?\n> ")
			print("Send? [yN] ", end="", flush=True)
			if getch("yn").lower() == 'y':
				currentBidder.postComment(msg)
		elif cmd.lower() == "c":
			item_idx = doMenu("Select an item to comment on:", items[currentAccount['auction']] + [{"name":"Enter custom item name..."}])
			if item_idx is not None:
				if item_idx == len(items[currentAccount['auction']]):
					item = input("What is the name of the item you'd like to comment on?\n> ")
				else:
					item = items[currentAccount['auction']][item_idx]['name']

				msg = input("What is the message?\n> ")
				print("Send? [yN] ", end="", flush=True)
				if getch("yn").lower() == 'y':
					currentBidder.postComment(msg, item)
		elif cmd.lower() == "a":
			newAccountIdx = doMenu("Select an account:", accounts)
			if newAccountIdx is not None:
				currentAccountIdx = newAccountIdx
		elif cmd.lower() == "q":
			print("Goodbye!")
			exit()
		else:
			print("Unknown command!")
