import discord
import sleeper_api
from db_instance import (league_settings_db, link_user, unlink_user, user_db,
                         weekly_db)
from discord import app_commands
from tasks import generate_week_summary_image
from utils import load_json, save_json

# Data files
# USER_FILE = "user_links.json"
# LEAGUE_FILE = "league_settings.json"
# TRACKER_FILE = "weekly_tracker.json"
PLAYER_FILE = "players.json"
#
# user_links = load_json(USER_FILE)
# league_settings = load_json(LEAGUE_FILE)
# weekly_tracker = load_json(TRACKER_FILE)
players_data = load_json(PLAYER_FILE)



class SleeperGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="sleeper", description="Sleeper fantasy football commands"
        )

    @app_commands.command(name="set_user", description="Link a Discord user to a Sleeper user ID")
    async def set_user(self, interaction: discord.Interaction, discord_user: discord.Member, sleeper_user_id: str,):

        link_user(discord_user.id, sleeper_user_id)
        # user_links.setdefault("discord_to_sleeper", {})
        # user_links.setdefault("sleeper_to_discord", {})

        # user_links["discord_to_sleeper"][str(discord_user.id)] = sleeper_user_id
        # user_links["sleeper_to_discord"][sleeper_user_id] = str(discord_user.id)
        # save_json(USER_FILE, user_links)
        await interaction.response.send_message(
            f"✅ Linked {discord_user.mention} to Sleeper ID `{sleeper_user_id}`."
        )
        return

    @app_commands.command(name="set_league", description="Set default Sleeper league for this channel")
    async def set_league(self, interaction: discord.Interaction, league_id: str):
        try:
            league = sleeper_api.get_league(league_id)
            avatars = sleeper_api.get_avatars(league_id)
            if "name" not in league:
                await interaction.response.send_message("❌ Invalid league ID.")
                return
            # league_settings[str(interaction.channel_id)] = league_id
            league_settings_db.set(str(interaction.channel_id), league_id)
            league_settings_db.save()
            # save_json(LEAGUE_FILE, league_settings)
        except Exception as e:
            print(f"there was an exception saving league: {e}")
        await interaction.response.send_message(f"✅ League set: **{league['name']}**")

    @app_commands.command(name="standings", description="Show standings for this channel's league")
    async def standings(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel_id)
        # if channel_id not in league_settings:
        league_id = league_settings_db.get(channel_id)
        if league_id is None:
            await interaction.response.send_message("No league set for this channel.")
            return

        # league_id = league_settings[channel_id]
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

    @app_commands.command(name="matchup", description="Show matchups for a week")
    async def matchup(self, interaction: discord.Interaction, week: int):
        channel_id = str(interaction.channel_id)
        # if channel_id not in league_settings:
        league_id = league_settings_db.get(channel_id)
        if league_id is None:
            await interaction.response.send_message("No default league set.")
            return

        msg = f" **Here are the matchups for week {week}**\n"
        await interaction.response.send_message(msg)

        # Send styled summary image after text
        await generate_week_summary_image(interaction.channel, league_id, week)


    @app_commands.command(name="my_team", description="Show your team starters")
    async def my_team(self, interaction: discord.Interaction):
        channel_id = str(interaction.channel_id)
        user_id = str(interaction.user.id)

        league_id = league_settings_db.get(channel_id)
        sleeper_id = user_db.get("discord_to_sleeper").get(user_id)
        # if channel_id not in league_settings:
        if league_id is None:
            await interaction.response.send_message("No default league set.")
            return
        if sleeper_id is None:
            await interaction.response.send_message(
                "You haven't linked your Sleeper account."
            )
            return
        # league_id = league_settings[channel_id]
        # sleeper_id = user_links[user_id]
        rosters = sleeper_api.get_roster(league_id)

        for r in rosters:
            if r["owner_id"] == sleeper_id:
                starters = r.get("starters", [])
                names = [
                    players_data.get(pid, {}).get("full_name", pid) for pid in starters
                ]
                msg = "🧑‍💻 **Your Starters:**\n" + ", ".join(names)
                await interaction.response.send_message(msg)
                return

        await interaction.response.send_message(
            "Couldn't find your team in this league."
        )
        return

    @app_commands.command(name="weekly_recap", description="Get the recap for a week's matchup")
    async def weekly_recap(self, interaction: discord.Interaction, week: int):
        channel_id = str(interaction.channel_id)

        # if channel_id not in league_settings:
        league_id = league_settings_db.get(channel_id)
        if league_id is None:
            await interaction.response.send_message("No default league set.")
            return

        # league_id = league_settings[channel_id]

        try:
            res = sleeper_api.get_matchups(league_id, week)
            roster_id_to_points = [(team["roster_id"], team["points"]) for team in res]
            roster_id_to_points = sorted(roster_id_to_points, key=lambda x: x[1], reverse=True) # sort on points scored
            rosters = sleeper_api.get_roster(league_id)
            users = sleeper_api.get_users_in_league(league_id)

            roster_id_to_owner = {r["roster_id"]: r["owner_id"] for r in rosters}
            owner_id_to_username = {u["user_id"]: u["display_name"] for u in users}

            msg = ""
            for idx,team in enumerate(roster_id_to_points):
                roster_id = team[0]
                points_scored = team[1]
                user_id = roster_id_to_owner.get(roster_id)
                if user_id:
                    discord_id = user_db.get("sleeper_to_discord")[user_id]
                    print("user_id:", user_id, " discord_id: ", discord_id)
                if discord_id:
                    member = interaction.guild.get_member(int(discord_id))
                    if member:
                        team_name = member.mention
                    else:
                        team_name = owner_id_to_username.get(user_id, "Unknown User")
                else:
                    fallback_user_id = roster_id_to_owner.get(roster_id)
                    team_name = owner_id_to_username.get(fallback_user_id, "Unknown User")

                if idx == 0:
                    msg += (f"### The top scorer for week {week} was __**{team_name}**__ with {points_scored}!\n"
                            f"This is how the rest of the league performed:\n")
                else:
                    msg += f"{idx + 2}. {team_name}: {points_scored}\n"
        except Exception as e:
            print(f"There was an error: {e}")

        await interaction.response.send_message(msg)
        return
