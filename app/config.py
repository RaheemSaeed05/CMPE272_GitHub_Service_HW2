# Author, Raheem Saeed, Load the environment variables 

import os

from dotenv import load_dotenv


def read_config():
    load_dotenv()
    APP_GITHUB_TOKEN = os.getenv("APP_GITHUB_TOKEN")
    APP_GITHUB_OWNER = os.getenv("APP_GITHUB_OWNER")
    APP_GITHUB_REPO = os.getenv("APP_GITHUB_REPO")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
    PORT = int(os.getenv("PORT", "8000"))
    NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
    NGROK_DOMAIN = os.getenv("NGROK_DOMAIN")

    config_values = {
        'app_github_token': APP_GITHUB_TOKEN,
        'app_github_owner': APP_GITHUB_OWNER,
        'app_github_repo': APP_GITHUB_REPO,
        'webhook_secret': WEBHOOK_SECRET,
        'port': PORT,
        'ngrok_auth_token': NGROK_AUTH_TOKEN,
        'ngrok_domain': NGROK_DOMAIN
    }
    return config_values
