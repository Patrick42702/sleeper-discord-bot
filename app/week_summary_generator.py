import os
from html2image import Html2Image
import logging

logger = logging.getLogger(__name__)

def generate_week_html(summary_info, week, output_file=None):
    logger.info(summary_info)
    logger.info(week)

    if output_file is None:
        output_file = f"week_summary_{week}.png"

    # # Check if file already exists
    # if os.path.exists(output_file):
    #     print(f"[INFO] {output_file} already exists. Skipping regeneration.")
    #     return output_file

   
    logger.info(summary_info[1])
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px; }}
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
                background: #fff;
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
                align-items: center;
                background: #fff;
                padding: 10px;
                margin: 8px 0;
                border-radius: 8px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            }}
            .leaderboard img {{ width: 50px; height: 50px; border-radius: 50%; margin-right: 15px; }}
            .info {{ flex-grow: 1; }}
            .points {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Week {week} Summary</h1>

            <div class="podium">
                <div class="place second">
                    <img src="{summary_info[1].avatar}">
                    <p>{summary_info[1].team_name}</p>
                    <p>{summary_info[1].score} pts</p>
                </div>
                <div class="place first">
                    <img src="{summary_info[0].avatar}">
                    <p>{summary_info[0].team_name}</p>
                    <p>{summary_info[0].score} pts</p>
                </div>
                <div class="place third">
                    <img src="{summary_info[2].avatar}">
                    <p>{summary_info[2].team_name}</p>
                    <p>{summary_info[2].score} pts</p>
                </div>
            </div>
    """
    
    for player in summary_info[3:]:
        html+= f"""
            <div class="player">
                <img src="{player.avatar}">
                <div class="info">
                <p><b>{player.team_name}</b> - {player.best_player} ({player.best_points} pts)</p>
            </div>
            <div class="points">{player.points} pts</div>
        """

    html += """
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
    hti.screenshot(html_file="week_summary.html", save_as=output_file, size=(1200, 1200))
    return output_file

#   <div class="leaderboard">
#     {% for player in summary[3:] %}
#       <div class="player">
#         <img src="{{player.avatar}}">
#         <div class="info">
#           <p><b>{{player.team_name}}</b> - {{player.best_player}} ({{player.best_points}} pts)</p>
#         </div>
#         <div class="points">{{player.points}} pts</div>
#       </div>
#     {% endfor %}
#   </div>
# </body>
# </html>
