accounts = [
	{
		# The name as it will appear in the application and logs
		"name": "Account display name",
		# The username/email address to log in
		"username": "email@address.com",
		# The account password
		"password": "amazing_password_123",
		# The name of the Galabid auction for this account
		"auction": "my_awesome_auction",
		# A list of item UUIDs and the maximum amount to bid for each item
		"items": {
			"00000000-0000-0000-0000-000000000000": 50,
		},
	},
	{
		"name": "John Doe",
		"username": "jdoe@galabid.com",
		"password": "a_super_strong_password",
		"auction": "a_second_cool_auction",
		"items": {
			"11111111-1111-1111-1111-111111111111": 200,
			"22222222-2222-2222-2222-222222222222": 1000,
		},
	},
]

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1234567890123456778/..."
