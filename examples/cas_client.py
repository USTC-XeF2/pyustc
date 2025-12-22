from pyustc import CASClient


async def main():
    # Login with username and password, environment variables can be used
    async with CASClient.login_by_pwd("username", "password") as client:
        # Save the token to a file and load it later
        client.save_token("token.json")

    # If the token is invalid, will fallback to username/password login
    async with CASClient.load_token("token.json") as client:
        # Get the user info
        user = await client.get_info()
        print(user)
        print(
            user.id,
            user.name,
            user.gid,
            user.email,
            await user.get_idcard(),
            await user.get_phone(),
        )
