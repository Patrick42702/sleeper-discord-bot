import datetime
import os
import pytz
import discord
from discord.ext import commands, tasks
import sleeper_api
from utils import load_json, save_json, find_avatar_path
from html_generator import generate_html_image

# Data files
USER_FILE = "user_links.json"
LEAGUE_FILE = "league_settings.json"
TRACKER_FILE = "weekly_tracker.json"

user_links = load_json(USER_FILE)
league_settings = load_json(LEAGUE_FILE)
weekly_tracker = load_json(TRACKER_FILE)

def get_current_week(league_id):
    league = sleeper_api.get_league(league_id)
    return league.get("week")

class SummaryTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_summary_task.start()

    @tasks.loop(minutes=1)
    async def weekly_summary_task(self):
        tz = pytz.timezone("US/Eastern")
        now = datetime.datetime.now(tz)

        if now.weekday() == 3 and now.hour == 20:
            for channel_id, league_id in league_settings.items():
                try:
                    current_week = get_current_week(league_id)
                    last_week = str(int(current_week) - 1)

                    if (
                        str(channel_id) in weekly_tracker
                        and weekly_tracker[str(channel_id)] == last_week
                    ):
                        continue

                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        await send_weekly_summary(channel, league_id, last_week)
                        weekly_tracker[str(channel_id)] = last_week
                        save_json(TRACKER_FILE, weekly_tracker)
                except Exception as e:
                    print(f"❌ Summary Error in channel {channel_id}: {e}")

    @weekly_summary_task.before_loop
    async def before_summary(self):
        await self.bot.wait_until_ready()


async def send_weekly_summary(channel, league_id, week):
    matchups = sleeper_api.get_matchups(league_id, week)
    rosters = sleeper_api.get_roster(league_id)
    users = sleeper_api.get_users_in_league(league_id)

    roster_id_to_owner = {r["roster_id"]: r["owner_id"] for r in rosters}
    owner_id_to_username = {u["user_id"]: u["display_name"] for u in users}
    scores = {m["roster_id"]: m["points"] for m in matchups}

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
                "team1_avatar": f"avatars/{roster_id_to_owner.get(r1)}.png",
                "team2_name": owner_id_to_username.get(roster_id_to_owner.get(r2), "Unknown"),
                "team2_score": scores.get(r2, 0),
                "team2_avatar": f"avatars/{roster_id_to_owner.get(r2)}.png"
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


async def generate_week_summary_image(channel, league_id, week):
    matchups = sleeper_api.get_matchups(league_id, week)
    rosters = sleeper_api.get_roster(league_id)
    users = sleeper_api.get_users_in_league(league_id)

    roster_id_to_owner = {r["roster_id"]: r["owner_id"] for r in rosters}
    owner_id_to_username = {u["user_id"]: u["display_name"] for u in users}
    scores = {m["roster_id"]: m["points"] for m in matchups}

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
                "team2_name": owner_id_to_username.get(roster_id_to_owner.get(r2), "Unknown"),
                "team2_score": scores.get(r2, 0),
                "team2_avatar": find_avatar_path(roster_id_to_owner.get(r2))
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
