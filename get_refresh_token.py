from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json", SCOPES
)

credentials = flow.run_local_server(port=0)

print("\n--- SAVE THESE ---")
print("Client ID:", credentials.client_id)
print("Client Secret:", credentials.client_secret)
print("Refresh Token:", credentials.refresh_token)