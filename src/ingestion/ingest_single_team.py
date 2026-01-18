import os
import sys
import argparse
import time
import re
import chromadb

# Ensure project root is on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.ingestion.synergy_client import SynergyClient

from config.ncaa_di_mens_basketball import NCAA_DI_MENS_BASKETBALL
from config.ncaa_dii_mens_basketball import NCAA_DII_MENS_BASKETBALL
from config.ncaa_diii_mens_basketball import NCAA_DIII_MENS_BASKETBALL


# --------------------------------------------------
# NORMALIZATION
# --------------------------------------------------
def normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9]', '', text.lower())


# --------------------------------------------------
# DIVISION → CONFERENCE MAP
# --------------------------------------------------
DIVISION_MAP = {
    "DI": NCAA_DI_MENS_BASKETBALL,
    "DII": NCAA_DII_MENS_BASKETBALL,
    "DIII": NCAA_DIII_MENS_BASKETBALL,
}


# --------------------------------------------------
# INGESTER
# --------------------------------------------------
class SingleTeamIngester:
    def __init__(self):
        self.client = SynergyClient()

        db_path = os.path.join(os.getcwd(), "data/vector_db")
        os.makedirs(db_path, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.meta_collection = self.chroma_client.get_or_create_collection(
            name="skout_game_metadata"
        )

    # --------------------------------------------------
    # INTERACTIVE SELECTION
    # --------------------------------------------------
    def interactive_select(self):
        print("\n🏀 NCAA Men's Basketball – Interactive Team Selection\n")

        # Division
        divisions = list(DIVISION_MAP.keys())
        division = self._prompt_choice("Select Division", divisions)

        # Conference
        conferences = sorted(DIVISION_MAP[division].keys())
        conference = self._prompt_choice("Select Conference", conferences)

        # Team
        teams = DIVISION_MAP[division][conference]
        team = self._prompt_choice("Select Team", teams)

        print(f"\n✅ Selected: {division} → {conference} → {team}")
        return team

    def _prompt_choice(self, title, options):
        print(f"\n{title}:")
        for i, opt in enumerate(options, 1):
            print(f"  [{i}] {opt}")

        while True:
            choice = input("> ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                return options[int(choice) - 1]
            print("Invalid selection, try again.")

    # --------------------------------------------------
    # TEAM ID RESOLUTION
    # --------------------------------------------------
    def resolve_team_id(self, team_name):
        print(f"\n🔍 Resolving Synergy team ID for {team_name}...")

        normalized_target = normalize(team_name)

        skip = 0
        take = 500

        while True:
            response = self.client._get(
                "/ncaamb/teams",
                params={"take": take, "skip": skip}
            )

            teams = response.get("data", [])
            if not teams:
                break

            for wrapper in teams:
                team = wrapper.get("data", wrapper)
                name = normalize(team.get("name", ""))
                market = normalize(team.get("market", ""))
                alias = normalize(team.get("alias", ""))

                combined = f"{market}{name}{alias}"

                if normalized_target in combined:
                    print(f"✅ Matched Synergy team: {team.get('market')} {team.get('name')}")
                    return team["id"]

            if len(teams) < take:
                break

            skip += take
            time.sleep(0.2)

        raise RuntimeError(f"Team '{team_name}' not found in Synergy team list")

    # --------------------------------------------------
    # SEASONS
    # --------------------------------------------------
    def get_recent_seasons(self, years_back=6):
        response = self.client.get_seasons(league_code="ncaamb")

        seasons = []
        for wrapper in response.get("data", []):
            season = wrapper.get("data", wrapper)
            seasons.append({
                "id": season["id"],
                "name": season.get("name"),
            })

        seasons.sort(key=lambda s: s["name"], reverse=True)
        return seasons[:years_back]

    # --------------------------------------------------
    # INGESTION
    # --------------------------------------------------
    def ingest_team_history(self, team_name, years_back=6):
        team_id = self.resolve_team_id(team_name)
        seasons = self.get_recent_seasons(years_back)

        total = 0

        for season in seasons:
            print(f"\n📅 Ingesting {season['name']}")

            skip = 0
            take = 50

            while True:
                response = self.client._get(
                    "/ncaamb/games",
                    params={
                        "seasonId": season["id"],
                        "teamId": team_id,
                        "take": take,
                        "skip": skip
                    }
                )

                games = response.get("data", [])
                if not games:
                    break

                for wrapper in games:
                    game = wrapper.get("data", wrapper)
                    self.save_game_metadata(game, season["id"])
                    total += 1

                if len(games) < take:
                    break

                skip += take
                time.sleep(0.2)

        print(f"\n🎉 Ingestion complete: {total} games indexed for {team_name}")

    # --------------------------------------------------
    # STORAGE
    # --------------------------------------------------
    def save_game_metadata(self, game, season_id):
        game_id = str(game.get("id"))
        home = game.get("homeTeam", {}).get("name", "Unknown")
        away = game.get("awayTeam", {}).get("name", "Unknown")
        date = game.get("date") or game.get("scheduled")

        description = f"{home} vs {away} on {date}"

        self.meta_collection.add(
            ids=[game_id],
            documents=[description],
            metadatas=[{
                "season_id": season_id,
                "home_team": home,
                "away_team": away,
                "game_date": date,
                "status": game.get("status")
            }]
        )


# --------------------------------------------------
# CLI ENTRYPOINT
# --------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SKOUT – Interactive Single Team Ingestion (Men's NCAA Basketball)"
    )
    parser.add_argument("--history", type=int, default=6)
    args = parser.parse_args()

    ingester = SingleTeamIngester()
    team = ingester.interactive_select()
    ingester.ingest_team_history(team, args.history)
