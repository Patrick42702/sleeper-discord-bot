import os
from html2image import Html2Image

def generate_html_image(matchups, standings, week, output_file="matchup_summary.png"):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; background: #3d3d3d; padding: 20px; color: #f0f0f0; }}
            h2 {{ text-align: center; }}
            .matchup {{ display: flex; justify-content: space-between; background: #787878; padding: 15px 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .team {{ width: 40%; text-align: center; }}
            .avatar {{ width: 64px; height: 64px; border-radius: 50%; }}
            .vs {{ font-size: 18px; align-self: center; }}
            .name {{ font-size: 16px; margin-top: 5px; }}
            .winner {{ color: #00ff00; font-weight: bold; }}
            .loser {{ color: #ff6666; }}
            .score {{ font-size: 18px; }}
            .standings {{ margin-top: 40px; }}
            .standings-item {{ font-size: 15px; margin: 5px 0; }}
        </style>
    </head>
    <body>
    """

    for m in matchups:
        team1 = m["team1_name"]
        team2 = m["team2_name"]
        score1 = m["team1_score"]
        score2 = m["team2_score"]

        # Determine winner/loser and labels
        if score1 > score2:
            name1 = f"<span class='winner'>{team1} ✔</span>"
            name2 = f"<span class='loser'>{team2} ✗</span>"
        elif score2 > score1:
            name1 = f"<span class='loser'>{team1} ✗</span>"
            name2 = f"<span class='winner'>{team2} ✔</span>"
        else:
            name1 = f"<span class='name'>{team1}</span>"
            name2 = f"<span class='name'>{team2}</span>"

        html += f"""
        <div class='matchup'>
            <div class='team'>
                <img src='{m['team1_avatar']}' class='avatar'>
                <div class='name'>{name1}</div>
                <div class='score'>{score1:.2f} pts</div>
            </div>
            <div class='vs'>vs</div>
            <div class='team'>
                <img src='{m['team2_avatar']}' class='avatar'>
                <div class='name'>{name2}</div>
                <div class='score'>{score2:.2f} pts</div>
            </div>
        </div>
        """

    html += """
    </body>
    </html>
    """

    with open("matchups.html", "w", encoding="utf-8") as f:
        f.write(html)

    hti = Html2Image()
    hti.screenshot(html_file="matchups.html", save_as=output_file, size=(800, 1000))
    return output_file
