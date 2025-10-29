import requests
import json

# --- Configuration ---
# WARNING: API keys should be provided via environment variables or secure configuration
# This file is deprecated - use slack_fetcher.py instead
import os

# Try to get from environment variables
ACCESS_TOKEN = os.getenv('SLACK_BOT_TOKEN', '')
CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID', 'C01AA471D46')
API_URL = "https://slack.com/api/conversations.history"

# --- Headers for the API Request ---
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
} if ACCESS_TOKEN else {}

# --- Parameters for the API Request ---
params = {
    "channel": CHANNEL_ID,
    "limit": 200  # You can adjust this value (max 1000) to fetch more messages per request
}

# --- Make the API Request ---
try:
    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()  # This will raise an exception for HTTP errors (e.g., 401, 404)
    
    data = response.json()

    if data.get("ok"):
        messages = data.get("messages", [])
        
        # --- Process and Save the Data ---
        # You can now process the 'messages' list as needed for your analysis.
        # For this example, we will save the messages to a JSON file.
        
        with open("slack_channel_history.json", "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)
            
        print(f"Successfully fetched {len(messages)} messages and saved them to 'slack_channel_history.json'")

        # --- Handling Pagination ---
        # If there are more messages to fetch, the response will include a 'next_cursor'.
        if data.get("has_more"):
            print("There are more messages to fetch. You can implement pagination using the 'next_cursor'.")

    else:
        print(f"Error from Slack API: {data.get('error')}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred with the HTTP request: {e}")
except json.JSONDecodeError:
    print("Failed to decode the JSON response from the server.")
