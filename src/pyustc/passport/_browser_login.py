import json

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    msg = "The relevant modules are not installed. Please install them with 'pip install pyustc[browser]'"
    raise ImportError(msg)

from ..url import generate_url

def _get_driver(type: str, headless: bool):
    if type == "chrome":
        driver_class = webdriver.Chrome
        options = webdriver.ChromeOptions()
        logging_prefix = "goog"
    elif type == "edge":
        driver_class = webdriver.Edge
        options = webdriver.EdgeOptions()
        logging_prefix = "ms"
    else:
        raise ValueError(f"Unsupported driver type {type!r}")
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.set_capability(f"{logging_prefix}:loggingPrefs", {"performance": "ALL"})
    return driver_class(options=options)

def login(usr: str, pwd: str, driver_type: str, headless: bool, timeout: int) -> str:
    url = generate_url("id", "cas/login")
    with _get_driver(driver_type, headless) as driver:
        driver.get(url)

        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys(usr)
        pwd_xpath = '//*[@id="normalLoginForm"]/div[2]/nz-input-group/input'
        driver.find_element(By.XPATH, pwd_xpath).send_keys(pwd)
        driver.find_element(By.ID, "submitBtn").click()
        WebDriverWait(driver, timeout).until(
            lambda d: d.current_url != url
        )

        for log in driver.get_log("performance"):
            msg = json.loads(log["message"])["message"]
            if msg["method"] == "Network.responseReceivedExtraInfo":
                cookie = msg["params"]["headers"].get("Set-Cookie")
                if cookie and cookie.startswith("SOURCEID_TGC"):
                    return cookie.split(";")[0].split("=", maxsplit=1)[1]
        raise ValueError("Failed to get token")
