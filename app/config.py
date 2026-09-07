# Author, Raheem Saeed, Load the environment variables 

import os

from dotenv import load_dotenv


def read_config():
    load_dotenv()
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_OWNER = os.getenv("GITHUB_OWNER")
    GITHUB_REPO = os.getenv("GITHUB_REPO")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
    PORT = int(os.getenv("PORT", "8000"))
    NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
    NGROK_DOMAIN = os.getenv("NGROK_DOMAIN")

    config_values = {
        'github_token': GITHUB_TOKEN,
        'github_owner': GITHUB_OWNER,
        'github_repo': GITHUB_REPO,
        'webhook_secret': WEBHOOK_SECRET,
        'port': PORT,
        'ngrok_auth_token': NGROK_AUTH_TOKEN,
        'ngrok_domain': NGROK_DOMAIN
    }
    return config_values
