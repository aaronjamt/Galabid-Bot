# Galabid Autobidder

This is a Python utility to automatically bid on Galabid auctions. While normally an autobidder would only place a single bid right at the end of the auction, this one watches for bids on selected items and instantly out-bids them. It was originally one file that did just that, but over time I added more features, and eventually had to split it into multiple files, hence the mix of code styles, formatting, and `utils.py`.

## Structure

`main.py`: This is the main program. Run it in a cronjob, as a SystemD service, or otherwise, and it will run in headless mode where it runs the autobidders and notification hooks.

`notifier.py`: This is the noitifcation part of the program. It can be used as a library, as described below, and will send Discord notifications when a bid is placed or someone makes posts a message.

`bidder.py`: This is the most important part. It contains all the code necessary to detect a bid, place a bid, and send messages. It can also be used as a library if that's all you're after.

`util.py`: Some stuff that's common between `notifier.py` and `bidder.py` and I didn't want to duplicate.

# Usage

## Running the whole shebang

Copy `config.default.py` to `config.py` and configure it, then just run the `main.py` script (with `python main.py` in the folder you download this repo to, or the equivalent on your machine).

## Usage as a library

### `notifier.py`

```python
import notifier
notif = notifier.Notifier("auction_name")
```

Right now, the Notifier class doesn't expose much that's useful. When you instatiate the class, it will start the notification listener automatically, so you don't really need to actually put it into a variable.

### `bidder.py`

This is the main part!

```python
import bidder

# Create a Bidder
bid = bidder.Bidder("auction_name", "email@address.com", "password_here_changeme")

# Place a bid on item with bidding_item UUID 00000000-0000-0000-0000-000000000000 for $10
bid.submitBid("00000000-0000-0000-0000-000000000000", 10)

# Say "Hello, world!"
bid.postComment("Hello, world!")

# Comment on the item "Galabid" with the message "I love Python"
bid.postComment("I love Python", "Galabid")

# Start autobidding on 3 items (by UUID) for $10, $50, and $100 respectively
bidding_items = {
	"00000000-0000-0000-0000-000000000000": 10,
	"11111111-1111-1111-1111-111111111111": 50,
	"22222222-2222-2222-2222-222222222222": 1000,
}
name_lookup = {
	"00000000-0000-0000-0000-000000000000": "Hello, world!",
	"11111111-1111-1111-1111-111111111111": "This is the name of the item as it will appear in logs".
	"22222222-2222-2222-2222-222222222222": "That is to say, copy the title of the item here so it shows the real name of the item"
}
bid.startAutobidder(bidding_items, name_lookup)
```
