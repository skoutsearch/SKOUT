import os
import sys
import re

# Add project root to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.synergy_client import SynergyClient


def normalize(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


client = SynergyClient()

response = client._get("/ncaamb/teams", params={"take": 500, "skip": 0})

if not response:
    print("No response from /ncaamb/teams")
    sys.exit(1)

teams = response.get("data", [])

print(f"\nTotal teams returned: {len(teams)}\n")

for t in teams:
    team = t.get("data", t)
    print(
        team.get("id"),
        "| market:", team.get("market"),
        "| name:", team.get("name"),
        "| alias:", team.get("alias")
    )
