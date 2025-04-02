from pyustc import Passport, EduSystem

passport = Passport()

# Passport logged in with password doesn't have permission
# Use `login_by_browser` or `login_by_token` instead
passport.login_by_browser()
# passport.login_by_token(...)

es = EduSystem(passport)

# TODO: Save token to a file
# es.save_token("es_token.json")
# EduSystem.load_token("es_token.json")
