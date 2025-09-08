import os
from html2image import Html2Image
import logging

logger = logging.getLogger(__name__)


def generate_week_html(summary_info, week, output_file=None):

    if output_file is None:
        output_file = f"week_summary_{week}.png"

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #17293b; color: white; padding: 20px; overflow: hidden; }}
            h1 {{ text-align: center; }}

            .podium {{
                display: flex;
                justify-content: center;
                margin-bottom: 40px;
                gap: 20px;
            }}
            .podium .place {{
                text-align: center;
                padding: 10px;
                border-radius: 12px;
                background: #294878;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                width: 150px;
            }}
            .place img {{ width: 80px; height: 80px; border-radius: 50%; }}
            .first {{ border: 3px solid gold; }}
            .second {{ border: 3px solid silver; }}
            .third {{ border: 3px solid #cd7f32; }}

            .leaderboard {{
                margin-top: 20px;
            }}
            .leaderboard .player {{
                display: flex;
                flex-direction: row;   /* force horizontal */
                align-items: center;
                justify-content: space-between; /* distribute children */
                background: #294878;
                padding: 10px;
                margin: 8px 0;
                border-radius: 8px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            }}
            .leaderboard img {{ width: 50px; height: 50px; border-radius: 50%; margin-right: 15px; }}
            .info {{
                flex-grow: 1;
                display: flex;
                flex-direction: row;
                align-items: center;
                gap: 20px;
            }}

            .info .score {{
                flex: 0 0 200px;
            }}

            .info .best-starter {{
                flex: 1;
            }}

            .points {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Week {week} Summary</h1>

            <div class="podium">
                <div class="place second">
                    <img src="{summary_info[1].get("avatar", "No avatar")}">
                    <p>{summary_info[1].get("team_name")}</p>
                    <p class="points">{summary_info[1].get("score")} pts</p>
                    <p>Best Starter</p>
                    <p>{summary_info[1].get("best_starter_name")}</p>
                    <p class="points">{summary_info[1].get("best_starter_points")} pts</p>
                </div>
                <div class="place first">
                    <img src="{summary_info[0].get("avatar")}">
                    <p>{summary_info[0].get("team_name")}</p>
                    <p class="points">{summary_info[0].get("score")} pts</p>
                    <p>Best Starter</p>
                    <p>{summary_info[0].get("best_starter_name")}</p>
                    <p class="points">{summary_info[0].get("best_starter_points")} pts</p>
                </div>
                <div class="place third">
                    <img src="{summary_info[2].get("avatar")}">
                    <p>{summary_info[2].get("team_name")}</p>
                    <p class="points">{summary_info[2].get("score")} pts</p>
                    <p>Best Starter</p>
                    <p>{summary_info[2].get("best_starter_name")}</p>
                    <p class="points">{summary_info[2].get("best_starter_points")} pts</p>
                </div>
            </div>
            <div class="leaderboard">
    """

    for player in summary_info[3:]:
        best_starter_data = player.get("best_starter_data") or {}
        best_starter_points = player.get("best_starter_points", 0)

        html += f"""
            <div class="player">
                <img src="{player.get("avatar")}">
                <div class="info">
                    <div class="score">
                    <p>{player.get("team_name")}</p>
                    <p><b>{player.get("score", 0)}</b> pts</p>
                    </div>
                    <div class="best-starter">
                    <p>Player of the week</p>
                    <p>{player.get("best_starter_name")} <b>{best_starter_points}</b> pts</p>
                    </div>
                </div>
            </div>
        """

    html += """
    </div>
    </body>
    </html>
    """

    with open("week_summary.html", "w", encoding="utf-8") as f:
        f.write(html)

    hti = Html2Image(
        browser_executable='/usr/bin/chromium',
        custom_flags=['--no-sandbox',
                      '--log-level=3'],
    )
    hti.screenshot(html_file="week_summary.html",
                   save_as=output_file, size=(1550, 1550))
    return output_file
