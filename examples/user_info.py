from pyustc import CASClient

client = CASClient()
client.login_by_pwd()

# Get the user info
user = client.get_info()
print(user)
print(
    user.id,
    user.name,
    user.gid,
    user.email,
    user.idcard,  # need to request again
    user.phone,  # need to request again
)
