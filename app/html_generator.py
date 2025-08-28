import os
from html2image import Html2Image

def generate_html_image(matchups, standings, week, output_file=None):
    scale = 1.0 / max(1, len(matchups) / 6)
    if output_file is None:
        output_file = f"matchup_summary_week_{week}.png"

    # Check if file already exists
    if os.path.exists(output_file):
        print(f"[INFO] {output_file} already exists. Skipping regeneration.")
        return output_file
    html = f"""
    <html>
    <head>
        <style>
            html, body {{
                margin: 0;
                padding: 20px;
                background: #3d3d3d;
                font-family: Arial, sans-serif;
                color: #f0f0f0;
                overflow: hidden; /* no scrollbar */
                height: 100%;
                width: 100%;
            }}

            body {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-start;
                box-sizing: border-box;
                transform-origin: top center;
                transform: scale({scale})
            }}

        .matchup {{
            display: flex;
            justify-content: space-between;
            background: #787878;
            padding: 15px 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            width: 90%;
            max-width: 800px;
            }}

            .team {{
                width: 40%;
                text-align: center;
            }}

            .avatar {{
                width: 64px;
                height: 64px;
                border-radius: 50%;
            }}

            .vs {{
                font -size: 18px;
                align-self: center;
            }}

            .name {{font -size: 16px; margin-top: 5px; }}
            .winner {{color: #00ff00; font-weight: bold; }}
            .loser {{ color: #ff6666; }}
            .score {{ font -size: 18px; }}

            .standings {{ margin -top: 40px; }}
            .standings-item {{ font -size: 15px; margin: 5px 0; }}
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
                <div class='team-name'>{m['team1_team']}</div>
                <div class='score'>{m['team1_score']} pts</div>
            </div>
            <div class='vs'>vs</div>
            <div class='team'>
                <img src='{m['team2_avatar']}' class='avatar'>
                <div class='name'>{name2}</div>
                <div class='team-name'>{m['team2_team']}</div>
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


    hti = Html2Image(
        browser_executable='/usr/bin/chromium',
        custom_flags=['--no-sandbox',
                      '--log-level=3'],
    )
    hti.screenshot(html_file="matchups.html", save_as=output_file, size=(1200, 1200))
    return output_file
