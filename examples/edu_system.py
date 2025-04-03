from pyustc import CASClient, EduSystem

client = CASClient()

# CAS client logged in by password directly doesn't have permission
# Use `login_by_browser` or `login_by_token` instead
client.login_by_browser()
# client.login_by_token(...)

es = EduSystem(client)

# TODO: Save token to a file
# es.save_token("es_token.json")
# EduSystem.load_token("es_token.json")
