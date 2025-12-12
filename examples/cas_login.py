from pyustc import CASClient

client = CASClient()

# Login with username and password
client.login_by_pwd("username", "password")
# Or use environment variables:
client.login_by_pwd()

# Login with token that you got from the cookies 'SOURCEID_TGC' in the browser
client.login_by_token("token")

# Save the token to a file and load it later
client.save_token("token.json")
client = CASClient.load_token("token.json")

# Check if the login is successful
print(client.is_login)
