import os
from dotenv import load_dotenv

load_dotenv()

INBOX_DIR = os.getenv("INBOX_DIR", "inbox")
LOG_DIR = os.getenv("LOG_DIR", "logs")