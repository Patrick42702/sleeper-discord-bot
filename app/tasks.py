from html_generator import generate_html_image
from utils import load_json, save_json, find_avatar_path
import sleeper_api
from discord.ext import commands, tasks
import datetime
import os
import pytz
import discord
import logging
logger = logging.getLogger(__name__)

# Data files
USER_FILE = "/app/json/user_links.json"
LEAGUE_FILE = "/app/json/league_settings.json"

user_links = load_json(USER_FILE)
league_settings = load_json(LEAGUE_FILE)


def get_current_week():
    league = sleeper_api.get_state()
    return league.get("week")


class SummaryTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_summary_task.start()

    @tasks.loop(minutes=1)
    async def weekly_summary_task(self):
        tz = pytz.timezone("US/Eastern")
        now = datetime.datetime.now(tz)

        if now.weekday() == 5 and now.hour == 16:
            logger.info("Code ran, now we just need to fix up the summary")
            for channel_id, league_id in league_settings.items():
                try:
                    current_week = get_current_week()
                    last_week = str(int(current_week) - 1)
                    logger.info(f"The last week was {last_week}")
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        await send_weekly_summary(channel, league_id, last_week)
                        logger.info("Sent weekly summary")
                except Exception as e:
                    print(f"❌ Summary Error in channel {channel_id}: {e}")

    @weekly_summary_task.before_loop
    async def before_summary(self):
        await self.bot.wait_until_ready()


# TODO:
async def send_weekly_summary(channel, league_id, week):
    matchups = sleeper_api.get_matchups(league_id, week)
    rosters = sleeper_api.get_roster(league_id)
    users = sleeper_api.get_users_in_league(league_id)

    roster_id_to_owner = {r["roster_id"]: r["owner_id"] for r in rosters}
    owner_id_to_user = {u["user_id"]: u for u in users}

    summary = []

    for m in matchups:
        roster_id = m["roster_id"]
        owner_id = roster_id_to_owner[roster_id]
        user = owner_id_to_user.get(owner_id, {})

        team_name = user.get("metadata", {}).get(
            "team_name") or user.get("display_name", "Unknown")

        points = m.get("points", 0)

        scores = {m["roster_id"]: m["points"] for m in matchups}
        owner_id_to_teamname = {
            u["user_id"]: u.get("metadata", {}).get("team_name", "")
            for u in users
        }

        pairs = {}
        for m in matchups:
            pairs.setdefault(m["matchup_id"], []).append(m["roster_id"])

        matchups_data = []
        for ids in pairs.values():
            if len(ids) == 2:
                r1, r2 = ids
                matchups_data.append({
                    "team1_name": owner_id_to_username.get(roster_id_to_owner.get(r1), "Unknown"),
                    "team1_score": scores.get(r1, 0),
                    "team1_avatar": find_avatar_path(roster_id_to_owner.get(r1)),
                    "team1_team": owner_id_to_teamname.get(roster_id_to_owner.get(r1), ""),
                    "team2_name": owner_id_to_username.get(roster_id_to_owner.get(r2), "Unknown"),
                    "team2_score": scores.get(r2, 0),
                    "team2_avatar": find_avatar_path(roster_id_to_owner.get(r2)),
                    "team2_team": owner_id_to_teamname.get(roster_id_to_owner.get(r2), ""),
                })

        # Starters for the week

        # Highest scoring NFL player on roster
        # get_highest_player()
        # https://api.sleeper.com/stats/nfl/player/421?season_type=regular&season=2024&grouping=week

        # summary.append({
        #     "team_name": team_name,
        #     "avatar": find_avatar_path(owner_id),
        #     "points": round(points, 2),
        #     "best_player": highest_player,
        #     "best_points": round(highest_score, 2),
        # })


async def generate_matchup_summary(channel, league_id, week):
    matchups = sleeper_api.get_matchups(league_id, week)
    rosters = sleeper_api.get_roster(league_id)
    users = sleeper_api.get_users_in_league(league_id)

    roster_id_to_owner = {r["roster_id"]: r["owner_id"] for r in rosters}
    owner_id_to_username = {u["user_id"]: u["display_name"] for u in users}
    scores = {m["roster_id"]: m["points"] for m in matchups}
    owner_id_to_teamname = {
        u["user_id"]: u.get("metadata", {}).get("team_name", "")
        for u in users
    }

    pairs = {}
    for m in matchups:
        pairs.setdefault(m["matchup_id"], []).append(m["roster_id"])

    matchups_data = []
    for ids in pairs.values():
        if len(ids) == 2:
            r1, r2 = ids
            matchups_data.append({
                "team1_name": owner_id_to_username.get(roster_id_to_owner.get(r1), "Unknown"),
                "team1_score": scores.get(r1, 0),
                "team1_avatar": find_avatar_path(roster_id_to_owner.get(r1)),
                "team1_team": owner_id_to_teamname.get(roster_id_to_owner.get(r1), ""),
                "team2_name": owner_id_to_username.get(roster_id_to_owner.get(r2), "Unknown"),
                "team2_score": scores.get(r2, 0),
                "team2_avatar": find_avatar_path(roster_id_to_owner.get(r2)),
                "team2_team": owner_id_to_teamname.get(roster_id_to_owner.get(r2), ""),
            })

    standings = sleeper_api.get_standings(league_id)
    standings_data = [
        {
            "name": owner_id_to_username.get(team["owner_id"], "Unknown"),
            "wins": team["settings"]["wins"],
            "losses": team["settings"]["losses"]
        }
        for team in standings
    ]

    image_path = generate_html_image(matchups_data, standings_data, week)
    await channel.send(file=discord.File(image_path))
