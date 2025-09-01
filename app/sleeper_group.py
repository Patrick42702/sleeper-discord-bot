import discord
import sleeper_api
from discord import app_commands
from tasks import generate_matchup_summary, generate_weekly_summary
from utils import load_json, save_json
from week_summary_generator import generate_week_html
import logging

logger = logging.getLogger(__name__)

# Data files
USER_FILE = "/app/json/user_links.json"
LEAGUE_FILE = "/app/json/league_settings.json"
PLAYER_FILE = "/app/json/players.json"

user_links = load_json(USER_FILE)
league_settings = load_json(LEAGUE_FILE)
players_data = load_json(PLAYER_FILE)


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
            f"✅ Linked {discord_user.mention} to Sleeper ID {sleeper_user_id}."
        )
        return

    @app_commands.command(
        name="set_league",
        description="Set default Sleeper league for this channel",
    )
    async def set_league(self, interaction: discord.Interaction, league_id: str):
        league = sleeper_api.get_league(league_id)
        avatars = sleeper_api.get_avatars(league_id)
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
        return

    @app_commands.command(
        name="matchup", description="Show matchups for a week"
    )
    async def matchup(self, interaction: discord.Interaction, week: int):
        channel_id = str(interaction.channel_id)
        if channel_id not in league_settings:
            await interaction.response.send_message("No default league set.")
            return

        league_id = league_settings[channel_id]
        msg = f" **Here are the matchups for week {week}**\n"
        await interaction.response.send_message(msg)

        # Send styled summary image after text
        await generate_matchup_summary(interaction.channel, league_id, week)

    @app_commands.command(name="my_team", description="Show your team starters")
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
        return

    @app_commands.command(name="weekly_recap", description="Get recap of the league's week")
    async def weekly_recap(self, interaction: discord.Interaction, week: int):
        channel_id = str(interaction.channel_id)

        if channel_id not in league_settings:
            await interaction.response.send_message("No default league set.")
            return

        league_id = league_settings[channel_id]

        try:
            summary_info = await generate_weekly_summary(channel_id, league_id, week)
            generate_week_html(summary_info, week)
            # await interaction.response.send_message(msg)
            summary_image = (summary_info)

        except Exception:
            logger.exception("There was an error")
        return
