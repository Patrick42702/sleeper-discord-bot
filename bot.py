import discord
from discord.ext import tasks, commands
from discord import app_commands
import asyncio
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv

import sleeper_api
from utils import load_json, save_json

load_dotenv()
TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Data files
USER_FILE = "user_links.json"
LEAGUE_FILE = "league_settings.json"
TRACKER_FILE = "weekly_tracker.json"

user_links = load_json(USER_FILE)
league_settings = load_json(LEAGUE_FILE)
weekly_tracker = load_json(TRACKER_FILE)
players_data = {}


def get_current_week(league_id):
    league = sleeper_api.get_league(league_id)
    return league.get("week")


class SleeperGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="sleeper", description="Sleeper fantasy football commands"
        )

    @app_commands.command(
        name="set_user", description="Link a Discord user to a Sleeper user ID"
    )
    async def set_user(
        self,
        interaction: discord.Interaction,
        discord_user: discord.Member,
        sleeper_user_id: str,
    ):
        user_links[str(discord_user.id)] = sleeper_user_id
        save_json(USER_FILE, user_links)
        await interaction.response.send_message(
            f"✅ Linked {discord_user.mention} to Sleeper ID `{sleeper_user_id}`."
        )

    @app_commands.command(
        name="set_league",
        description="Set default Sleeper league for this channel",
    )
    async def set_league(self, interaction: discord.Interaction, league_id: str):
        league = sleeper_api.get_league(league_id)
        if "name" not in league:
            await interaction.response.send_message("❌ Invalid league ID.")
            return
        league_settings[str(interaction.channel_id)] = league_id
        save_json(LEAGUE_FILE, league_settings)
        await interaction.response.send_message(f"✅ League set: **{league['name']}**")

    @app_commands.command(
        name="standings", description="Show standings for this channel's league"
    )
    async def standings(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel_id)
        if channel_id not in league_settings:
            await interaction.response.send_message("No league set for this channel.")
            return

        league_id = league_settings[channel_id]
        standings = sleeper_api.get_standings(league_id)
        users = sleeper_api.get_users_in_league(league_id)
        user_map = {u["user_id"]: u["display_name"] for u in users}

        msg = "**📈 Standings:**\n"
        for i, team in enumerate(standings, 1):
            owner = user_map.get(team["owner_id"], "Unknown")
            wins = team["settings"]["wins"]
            losses = team["settings"]["losses"]
            msg += f"{i}. {owner} — {wins}-{losses}\n"

        await interaction.response.send_message(msg)

    ### ========== /sleeper matchup ==========
    @app_commands.command(
        name="sleeper_matchup", description="Show matchups for a week"
    )
    async def matchup(self, interaction: discord.Interaction, week: int):
        channel_id = str(interaction.channel_id)
        if channel_id not in league_settings:
            await interaction.response.send_message("No default league set.")
            return

        league_id = league_settings[channel_id]
        matchups = sleeper_api.get_matchups(league_id, week)
        rosters = sleeper_api.get_roster(league_id)
        users = sleeper_api.get_users_in_league(league_id)

        roster_id_to_owner = {r["roster_id"]: r["owner_id"] for r in rosters}
        owner_id_to_username = {u["user_id"]: u["display_name"] for u in users}
        scores = {m["roster_id"]: m["points"] for m in matchups}
        lineups = {m["roster_id"]: m.get("starters", []) for m in matchups}

        pairs = {}
        for m in matchups:
            pairs.setdefault(m["matchup_id"], []).append(m["roster_id"])

        def player_names(starters):
            return [players_data.get(pid, {}).get("full_name", pid) for pid in starters]

        msg = f"📅 **Week {week} Matchups**\n"
        for ids in pairs.values():
            if len(ids) == 2:
                r1, r2 = ids
                u1 = owner_id_to_username.get(roster_id_to_owner.get(r1), "Unknown")
                u2 = owner_id_to_username.get(roster_id_to_owner.get(r2), "Unknown")
                s1 = scores.get(r1, 0)
                s2 = scores.get(r2, 0)
                msg += f"\n__**{u1}**__ ({s1:.2f}) vs __**{u2}**__ ({s2:.2f})\n"
                msg += f"> {u1}'s Starters: {', '.join(player_names(lineups.get(r1, [])))}\n"
                msg += f"> {u2}'s Starters: {', '.join(player_names(lineups.get(r2, [])))}\n"

        await interaction.response.send_message(msg)

    @app_commands.command(name="sleeper_my_team", description="Show your team starters")
    async def my_team(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel_id)
        user_id = str(interaction.user.id)

        if channel_id not in league_settings:
            await interaction.response.send_message("No default league set.")
            return
        if user_id not in user_links:
            await interaction.response.send_message(
                "You haven't linked your Sleeper account."
            )
            return

        league_id = league_settings[channel_id]
        sleeper_id = user_links[user_id]
        rosters = sleeper_api.get_roster(league_id)

        for r in rosters:
            if r["owner_id"] == sleeper_id:
                starters = r.get("starters", [])
                names = [
                    players_data.get(pid, {}).get("full_name", pid) for pid in starters
                ]
                msg = f"🧑‍💻 **Your Starters:**\n" + ", ".join(names)
                await interaction.response.send_message(msg)
                return

        await interaction.response.send_message(
            "Couldn't find your team in this league."
        )

async def on_ready():
    global players_data
    players_data = sleeper_api.get_players()
    await tree.sync()
    tree.add_command(SleeperGroup())
    print(f"✅ Logged in as {client.user}")
    weekly_summary_task.start()


### ========== Scheduled Summary ==========
@tasks.loop(minutes=1)
async def weekly_summary_task():
    tz = pytz.timezone("US/Eastern")
    now = datetime.now(tz)
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

                channel = client.get_channel(int(channel_id))
                if channel:
                    await send_weekly_summary(channel, league_id, last_week)
                    weekly_tracker[str(channel_id)] = last_week
                    save_json(TRACKER_FILE, weekly_tracker)
            except Exception as e:
                print(f"❌ Summary Error in channel {channel_id}: {e}")


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

    msg = f"🏈 **Week {week} Results**\n"
    for ids in pairs.values():
        if len(ids) == 2:
            r1, r2 = ids
            u1 = owner_id_to_username.get(roster_id_to_owner.get(r1), "Unknown")
            u2 = owner_id_to_username.get(roster_id_to_owner.get(r2), "Unknown")
            s1 = scores.get(r1, 0)
            s2 = scores.get(r2, 0)
            winner = u1 if s1 > s2 else u2
            msg += f"- {u1} ({s1:.2f}) vs {u2} ({s2:.2f}) → **Winner: {winner}**\n"

    standings = sleeper_api.get_standings(league_id)
    msg += "\n📈 **Standings**\n"
    for i, team in enumerate(standings, 1):
        owner = owner_id_to_username.get(team["owner_id"], "Unknown")
        wins = team["settings"]["wins"]
        losses = team["settings"]["losses"]
        msg += f"{i}. {owner} — {wins}-{losses}\n"

    await channel.send(msg)


client.run(TOKEN)
