# new file: `html_generator.py`
import os
from html2image import Html2Image

def generate_html_image(matchups, standings, week, output_file="matchup_summary.png"):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; background: #f2f2f2; padding: 20px; }}
            h2 {{ text-align: center; }}
            .matchup {{ display: flex; justify-content: space-between; background: #fff; padding: 15px 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .team {{ width: 40%; text-align: center; }}
            .avatar {{ width: 64px; height: 64px; border-radius: 50%; }}
            .vs {{ font-size: 18px; align-self: center; color: #999; }}
            .name {{ font-weight: bold; font-size: 16px; margin-top: 5px; }}
            .score {{ font-size: 18px; color: #333; }}
            .standings {{ margin-top: 40px; }}
            .standings-item {{ font-size: 15px; margin: 5px 0; }}
        </style>
    </head>
    <body>
    """
        # <h2>Week {week} Matchups</h2>
    for m in matchups:
        html += f"""
        <div class='matchup'>
            <div class='team'>
                <img src='{m['team1_avatar']}' class='avatar'>
                <div class='name'>{m['team1_name']}</div>
                <div class='score'>{m['team1_score']} pts</div>
            </div>
            <div class='vs'>vs</div>
            <div class='team'>
                <img src='{m['team2_avatar']}' class='avatar'>
                <div class='name'>{m['team2_name']}</div>
                <div class='score'>{m['team2_score']} pts</div>
            </div>
        </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    with open("matchups.html", "w", encoding="utf-8") as f:
        f.write(html)

    hti = Html2Image()
    hti.screenshot(html_file="matchups.html", save_as=output_file, size=(800, 1000))
    return output_file