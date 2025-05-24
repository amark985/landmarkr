import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Access your API keys from environment variables
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
NPS_API_KEY = os.getenv("NPS_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

