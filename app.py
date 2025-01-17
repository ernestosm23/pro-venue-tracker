import psycopg2
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify, render_template
from api_key import postgres_pw
import datetime as dt
import pytz 

engine = create_engine(f'postgresql+psycopg2://postgres:{postgres_pw}@localhost:5432/project_3')

Base = automap_base()

Base.prepare(autoload_with=engine)

Venue = Base.classes.venue
Team = Base.classes.team
League = Base.classes.league
Event = Base.classes.event

# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chart")
def chart():
    return render_template("chart.html")


@app.route("/api/teams")
def team():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all teams"""
    # Query all teams with league joined
    results = session.query(Team.team, Team.venue_id, League.league,
                            Venue.venue_id, Venue.venue_name, Venue.venue_state,
                            Venue.venue_address, Venue.venue_lat, Venue.venue_lon).filter(Team.league_id == League.league_id).filter(Team.venue_id == Venue.venue_id).all()

    session.close()

    all_teams = []
    for result in results:
        team_dict = {}
        team_dict["team"] = result[0]
        team_dict["venue_id"] = result[1]
        team_dict["league"] = result[2]
        team_dict["venue_id"] = result[3]
        team_dict["venue_name"] = result[4]
        team_dict["venue_state"] = result[5]
        team_dict["venue_address"] = result[6]
        team_dict["venue_lat"] = float(result[7])
        team_dict["venue_lon"] = float(result[8])

        all_teams.append(team_dict)

    return jsonify(all_teams)

@app.route("/api/venues")
def venue():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all teams"""
    # Query all teams with league joined
    results = session.query(Team.team, League.league,
                            Venue.venue_name, Venue.venue_state,
                            Venue.venue_address, Team.team_id,
                            Venue.venue_lat, Venue.venue_lon).\
                                filter(Team.league_id == League.league_id).\
                                filter(Team.venue_id == Venue.venue_id).all()

    venues_dict = {}

    for result in results:
        team_dict = {}
        team_dict["team"] = result[0]
        team_dict["league"] = result[1]
        team_dict["venue_name"] = result[2]
        team_dict["venue_state"] = result[3]
        team_dict["venue_address"] = result[4]
        team_dict["team_id"] = int(result[5])
        team_dict["venue_lat"] = float(result[6])
        team_dict["venue_lon"] = float(result[7])

        venue_name = result[2]

        if venue_name not in venues_dict.keys():
            venues_dict[venue_name] = [team_dict]
        else:
            venues_dict[venue_name].append(team_dict)

    today = dt.date.today()

    for venue in venues_dict:
        for team in venues_dict[venue]:
            if team["league"] != "NBA":
                home_id = team["team_id"]

                next_event = session.query(Event.event_timestamp_cst, Event.away_id).\
                                            filter(Event.home_id == home_id).\
                                            filter(Event.event_timestamp_cst > today).\
                                            order_by(Event.event_timestamp_cst).limit(1).all()
                
                event_time = next_event[0][0].strftime("%Y-%m-%d %I:%M %p") + " CST"


                team["next_event"] = [event_time]
                away_id = next_event[0][1]

                away_team = session.query(Team.team).filter(Team.team_id == away_id)[0][0]
                team["next_event"].append(away_team)

            else:
                team["next_event"] = "NBA Schedule not yet released."

    session.close()

    return jsonify(venues_dict)

if __name__ == '__main__':
    app.run(debug=True)

