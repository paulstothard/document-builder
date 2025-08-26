import os
import json
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect

# Load from environment
APP_KEY = os.getenv("DOCUMENT_BUILDER_DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DOCUMENT_BUILDER_DROPBOX_APP_SECRET")
TOKEN_FILE = os.getenv("DOCUMENT_BUILDER_DROPBOX_TOKEN_FILE", os.path.expanduser("~/.document-builder-secrets.json"))

if not APP_KEY or not APP_SECRET:
    print("❌ Error: Set DOCUMENT_BUILDER_DROPBOX_APP_KEY and DOCUMENT_BUILDER_DROPBOX_APP_SECRET in your environment.")
    exit(1)

# Start OAuth flow with offline access to get a refresh token
flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET, token_access_type='offline')
authorize_url = flow.start()

print("📎 1. Go to this URL and click 'Allow':\n")
print(authorize_url)
print("\n📋 2. Copy the authorization code and paste it below.")

auth_code = input("🔑 3. Authorization code: ").strip()

try:
    result = flow.finish(auth_code)
except Exception as e:
    print(f"❌ OAuth failed: {e}")
    exit(1)

refresh_token = result.refresh_token

if not refresh_token:
    print("❌ No refresh token received.")
    exit(1)

# Save to JSON token file
token_data = {
    "refresh_token": refresh_token
}

try:
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)
    os.chmod(TOKEN_FILE, 0o600)
    print(f"\n✅ Saved refresh token to: {TOKEN_FILE}")
except Exception as e:
    print(f"❌ Failed to write token file: {e}")