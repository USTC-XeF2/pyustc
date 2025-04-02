from pyustc import Passport

passport = Passport()

# Login with username and password
passport.login_by_pwd('username', 'password')
# Or use environment variables:
passport.login_by_pwd()

# Login with token that you got from the cookies 'SOURCEID_TGC' in the browser
passport.login_by_token('token')

# Login with browser(needs to install `pyustc[browser]` and configure the browser driver)
passport.login_by_browser(driver_type="chrome", headless=False, timeout=20)

# Save the token to a file and load it later
passport.save_token("token.json")
passport = Passport.load_token("token.json")

# Check if the login is successful
print(passport.is_login)
