from html_generator import generate_html_image
from week_summary_generator import generate_week_html
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
PLAYERS = "/app/json/players.json"

user_links = load_json(USER_FILE)
league_settings = load_json(LEAGUE_FILE)
players = load_json(PLAYERS)


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

        if now.weekday() == 6 and now.hour == 12:
            for channel_id, league_id in league_settings.items():
                try:
                    # current_week = get_current_week() # BUG: USE IN PROD
                    current_week = 2
                    last_week = str(int(current_week) - 1)
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        summary_data = await generate_weekly_summary(channel, league_id, last_week)
                except Exception as e:
                    print(f"❌ Summary Error in channel {channel_id}: {e}")

    @weekly_summary_task.before_loop
    async def before_summary(self):
        await self.bot.wait_until_ready()


# TODO:
async def generate_weekly_summary(channel, league_id, week):
    try:
        matchups = sleeper_api.get_matchups(league_id, week)
        rosters = sleeper_api.get_roster(league_id)
        users = sleeper_api.get_users_in_league(league_id)

        roster_id_to_owner = {r["roster_id"]: r["owner_id"] for r in rosters}
        owner_id_to_username = {u["user_id"]: u["display_name"] for u in users}
        owner_id_to_teamname = {
            u["user_id"]: u.get("metadata", {}).get("team_name", "")
            for u in users
        }

        summary = []

        for m in matchups:
            roster_id = m["roster_id"]
            score = m["points"]
            starters_pts = list(zip(m["starters"], m["starters_points"]))
            info = {
                "roster_id": m["roster_id"],
                "score": score,
                "avatar": find_avatar_path(roster_id_to_owner.get(roster_id)),
                "team_name": owner_id_to_teamname.get(roster_id_to_owner.get(roster_id))
            }
            best_starter = (None, 0)
            for idx in range(0, len(starters_pts)):
                if starters_pts[idx][1] > best_starter[1]:
                    best_starter = starters_pts[idx]
            if best_starter[0] is not None:
                best_starter_data = sleeper_api.get_player_points(
                    best_starter[0], week)
                best_starter_name = players[best_starter[0]]["full_name"]
                info["best_starter_name"] = best_starter_name
                info["best_starter_data"] = best_starter_data[week]
            else:
                info["best_starter_name"] = None
                info["best_starter_data"] = None
            summary.append(info)

        summary = list(sorted(summary, key=lambda x: x["score"], reverse=True))
        image_path = generate_week_html(summary, week)
        await channel.send(file=discord.File(image_path))

    except Exception:
        logger.exception("The following exception occured")


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
