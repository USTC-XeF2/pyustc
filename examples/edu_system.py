from pyustc import CASClient, EduSystem

client = CASClient()
client.login_by_pwd()

es = EduSystem(client)

# TODO: Save token to a file
# es.save_token("es_token.json")
# EduSystem.load_token("es_token.json")
