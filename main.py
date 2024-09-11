import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime 
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import json
from sqlalchemy import MetaData
from flask_ckeditor import CKEditor
from webforms import PostForm, PasswordForm, UserForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, PlayerForm, PlayerRosterForm, SearchForm, OwnerForm, CapHoldForm, AddPlayerRosterForm, FranchisePlayerRosterForm
from werkzeug.utils import secure_filename
import uuid as uuid
import os
from dotenv import load_dotenv
import smtplib
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer 
import csv
from decimal import Decimal
import math
from datetime import date  
import pandas as pd
from io import StringIO, BytesIO
from werkzeug.wrappers import Response
from openpyxl import Workbook 

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

app = Flask(__name__)


# @app.route('/')
# def index():
#     return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})

#add CKEditor for rich text text fields
ckeditor = CKEditor(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///testsleeper.db'
# postgresql://${{ PGUSER }}:${{ PGPASSWORD }}@${{ PGHOST }}:${{ PGPORT }}/${{ PGDATABASE }}
# app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DBUsername}:{DBPassword}@{DBHost}:{DBPort}/{DBName}'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://${{ PGUSER }}:${{ PGPASSWORD }}@${{ PGHOST }}:${{ PGPORT }}/${{ PGDATABASE }}'

# get environment variables: see here:https://towardsdatascience.com/the-quick-guide-to-using-environment-variables-in-python-d4ec9291619e
load_dotenv()
database_url = os.environ.get('DATABASE_URL')
secret_key = os.environ.get('SECRET_KEY')
host = os.environ.get('HOST')
port = os.environ.get('PORT')
debug = os.environ.get('DEBUG')
gmail_pwd = os.environ.get('GMAILPWD')
gmail_address = os.environ.get('GMAIL_ADDRESS')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url


                                           



# app.config['SECRET_KEY'] = "super secret key"

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# app.config['FLASK_RUN_PORT'] = 3000
# app.config['FLASK_RUN_HOST'] = '0.0.0.0'

# app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{DBUsername}:{DBPassword}@localhost/{DBName}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key


#initialize the database
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)

# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))

# helper function
def round_half_up(n, decimals=0):
    multiplier = 10 ** decimals
    half = Decimal("0.5")
    return int(math.floor(n * multiplier + half) / multiplier)
 

# Create Custom Error Pages

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
	return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
	return render_template("500.html"), 500


admin_user_list = [1,2]
UserId = "499807936168587264"
Sport = "nfl"
# LeagueId = "859990766557179904" # 2022  
# LeagueId = "986829727832805376" # 2023
LeagueId = "1111386461611593728" # 2024

#setup urls for API calls
user_url = f'https://api.sleeper.app/v1/user/{UserId}'
league_users_url = f'https://api.sleeper.app/v1/league/{LeagueId}/users'
rosters_url = f'https://api.sleeper.app/v1/league/{LeagueId}/rosters'
# players_url = 'https://api.sleeper.app/v1/players/nfl'
current_season = 2024
caphold_multiplier = Decimal("0.3")
year_over_year_multiplier = Decimal("1.1")
drop_cap_hold_stop = date.fromisoformat('2024-03-01')
drops_cap_hold_cutoff = date.fromisoformat('2024-09-01')
roster_max = 18
pause_transaction_processing = False


def getLeagueStatus():
    league_url = f'https://api.sleeper.app/v1/league/{LeagueId}'
    print(league_url)
    league_info = requests.get(league_url).json()
    status = league_info['status']
    
    return status

def getLeagueRookieDraft():
    drafts_url = f'https://api.sleeper.app/v1/league/{LeagueId}/drafts'
    response = requests.get(drafts_url)
    drafts = response.json()
    rookie_draft = ""
    for draft in drafts:
        if draft['type'] == 'linear' and draft['status'] == 'complete':
            rookie_draft = draft['draft_id']
            return rookie_draft

def getRookieDraftDate():
    drafts_url = f'https://api.sleeper.app/v1/league/{LeagueId}/drafts'
    response = requests.get(drafts_url)
    drafts = response.json()
    for draft in drafts:
        if draft['type'] == 'linear' and draft['status'] == 'complete':
            draft_start_time = draft['start_time']
            return pd.to_datetime(draft_start_time, unit='ms')        
        
def getLeagueAuctionDraft():
    drafts_url = f'https://api.sleeper.app/v1/league/{LeagueId}/drafts'
    response = requests.get(drafts_url)
    drafts = response.json()
    rookie_draft_23 = ""
    for draft in drafts:
        if draft['type'] == 'auction' and draft['status'] == 'complete':
            auction_draft = draft['draft_id']
            return auction_draft 

def getAuctionDraftDate():
    drafts_url = f'https://api.sleeper.app/v1/league/{LeagueId}/drafts'
    response = requests.get(drafts_url)
    drafts = response.json()
    for draft in drafts:
        if draft['type'] == 'auction' and draft['status'] == 'complete':
            draft_start_time = draft['start_time']
            return pd.to_datetime(draft_start_time, unit='ms') 
        
def GetTeamIdbyOwnerId(ownerId):
    t = Team.query.filter_by(owner_id=ownerId).first()
    return t.id



@app.route('/user/update/<int:id>', methods = ['GET', 'POST'])
@login_required
def update_user(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        # name_to_update.teamname = request.form['teamname']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update_user.html", 
				form=form,
				name_to_update = name_to_update, id=id)
        except:
            flash("Error!  Looks like there was a problem...try again!")
            return render_template("update_user.html", 
				form=form,
				name_to_update = name_to_update,
				id=id)
    else:
        return render_template("update_user.html", 
				form=form,
				name_to_update = name_to_update,
				id = id)



@app.route('/user/add', methods = ['GET', 'POST'])
def add_user():
	name = None
	form = UserForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(email=form.email.data).first()
		if user is None:
			## Hash the password!!!
			hashed_pw = generate_password_hash(form.password_hash.data, 'pbkdf2:sha256')
			user = Users(name=form.name.data, username=form.username.data,email=form.email.data, password_hash = hashed_pw)
			db.session.add(user)
			db.session.commit()
		name = form.name.data
		form.name.data = ''
		form.username.data = ''
		form.email.data = ''
		# form.teamname.data = ''
		form.password_hash.data = ''

		flash("User Added Successfully!")
	our_users = Users.query.order_by(Users.date_added)
	return render_template("add_user.html", 
		form=form,
		name=name,
		our_users=our_users)

@app.route('/user/delete/<int:id>')
@login_required
def delete_user(id):
    # Check logged in id vs. id to delete
    if id == current_user.id or id in admin_user_list:
        user_to_delete = Users.query.get_or_404(id)
        name = None
        form = UserForm()

        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash("User Deleted Successfully!!")

            our_users = Users.query.order_by(Users.date_added)
            return render_template("add_user.html", 
            form=form,
            name=name,
            our_users=our_users)

        except:
            flash("Whoops! There was a problem deleting user, try again...")
            return render_template("add_user.html", 
            form=form, name=name,our_users=our_users)
    else:
        flash("Sorry, you can't delete that user! ")
        return redirect(url_for('dashboard'))




# # add code to call sleeper API
# @app.route('/owners')
# def getOwners():
#     response = requests.get(league_users_url)
#     league = response.json()
#     league_df = pd.DataFrame(league)

#     #convert metadata column to separate columns
#     league_metadata = pd.json_normalize(league_df['metadata'])

#     #concatenate metadata columns to league data
#     league_df = pd.concat([league_df, league_metadata], axis=1)

#     #fill team name based on username if missing
#     league_df['team_name'] = league_df['team_name'].fillna(league_df['display_name'])

#     league = league_df.to_html()
        
#     return render_template('owners.html', league=league)

@app.route('/update/<int:id>', methods = ['GET', 'POST'])
def updatePlayer(id):
    form = PlayerForm()
    player_to_update = Player.query.get_or_404(id)
    if request.method == "POST":
        player_to_update.fullname = request.form['name']
        try:
            db.session.commit()
            flash("Player updated successfully.")
            return render_template('update.html', form=form, player_to_update = player_to_update)
        except:
            flash("Oops, that didn't work.")
            return render_template('update.html', form=form, player_to_update = player_to_update)
    else:
        return render_template('update.html', form=form, player_to_update = player_to_update)



@app.route('/players/load')
def getPlayers():
    players_url = 'https://api.sleeper.app/v1/players/nfl'
    response = requests.get(players_url)
    players = response.json()
    
    player_id_list = list(players.keys())
    position_list = ['QB', 'WR', 'RB', 'TE', 'K']
    added_player_count = 0
    #add status logic
    for id in player_id_list:  
        # if (players[id]['position'] in position_list) and (players[id]['search_rank'] != 9999999) and (players[id]['active'] == True) and (added_player_count < 5000): 
        if (players[id]['position'] in position_list) and (players[id]['active'] == True) and (added_player_count < 5000): 

            player_to_update = Player.query.filter_by(id=id).first()
            if player_to_update == None:
                p = Player()
                p.id = players[id]['player_id']
                p.search_full_name = players[id]['search_full_name']
                p.search_last_name = players[id]['search_last_name']
                p.search_first_name = players[id]['search_first_name']
                p.full_name = players[id]['full_name']
                p.last_name = players[id]['last_name']
                p.first_name = players[id]['first_name']
                p.position = players[id]['position']
                p.status = players[id]['status']
                p.team = players[id]['team']
                db.session.add(p)
                db.session.commit()
                added_player_count += 1
                print(f'added player {p.full_name} with id {p.id}.')
            else: print(f'player {players[id]["full_name"]} already exists, no changes made.')
        # added_player_count += 1
    flash(f"successfully added {added_player_count} players")
        
    return render_template('load_players.html')


@app.route('/players/update')
def update_active_players():
    players_url = 'https://api.sleeper.app/v1/players/nfl'
    response = requests.get(players_url)
    players = response.json()
    
    player_id_list = list(players.keys())
    position_list = ['QB', 'WR', 'RB', 'TE', 'K']
    added_player_count = 0
    #add status logic
    for id in player_id_list:  
        if (players[id]['position'] in position_list) and (players[id]['search_rank'] != 9999999) and (players[id]['active'] == True) and (added_player_count < 5000): 
            p = Player.query.filter_by(id=id).first()
            if p == None:
                p = Player()
            p.id = players[id]['player_id']
            p.search_full_name = players[id]['search_full_name']
            p.search_last_name = players[id]['search_last_name']
            p.search_first_name = players[id]['search_first_name']
            p.full_name = players[id]['full_name']
            p.last_name = players[id]['last_name']
            p.first_name = players[id]['first_name']
            p.position = players[id]['position']
            p.status = players[id]['status']
            p.team = players[id]['team']
            db.session.add(p)
            db.session.commit()
            added_player_count += 1
            print(f'updated player {p.full_name} with id {p.id}.')
            # else: print(f'player {players[id]["full_name"]} already exists, no changes made.')
        # added_player_count += 1
    flash(f"successfully updated {added_player_count} players")        
    return render_template('load_players.html')

@app.route('/owners/update')
def update_owners():
    response = requests.get(league_users_url)
    league = response.json()

    updated_owner_count = 0
    for i in league:
        id = i['user_id']
        display_name = i['display_name']
        team_name = ''
        avatar = ''
        try:
            avatar = i['metadata']['avatar']
        except KeyError:
            pass
        try:
            team_name = i['metadata']['team_name']
        except:
            team_name = display_name

        owner = Owners.query.filter_by(id=id).first()
        if owner == None:
            owner = Owners()
            owner.id = id
            owner.display_name = display_name
            owner.teamname = team_name
            owner.avatar = avatar
            owner.user_id = None
            db.session.add(owner)
            print(f'added owner {owner.display_name} with id {owner.id}.')
        else:
            owner.display_name = display_name
            owner.teamname = team_name
            owner.avatar = avatar
            owner.date_updated = datetime.utcnow()
            print(f'updated owner {owner.display_name} with id {owner.id}.')
        db.session.commit()
        updated_owner_count += 1
    
    flash(f"successfully updated {updated_owner_count} owners")        
    owners = Owners.query.order_by(Owners.id)  

    return render_template('owners.html', owners = owners)

    # return render_template('load_from_api.html', load_object = "Owners")

@app.route('/owners/edit/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_owner(id):
    owner = Owners.query.get_or_404(id)
    print(owner.display_name)
    form = OwnerForm()
    if request.method == "POST":
            owner.user_id = form.user.data
            print(f"user:{form.user.data}")
            # Update Database
            # db.session.add(owner)
            db.session.commit()
            flash("Owner Has Been Updated!")
            # return redirect(url_for('edit_owner', id=owner.id))
            return redirect("/")

    if current_user.id  in admin_user_list:    
        form.displayname.data = owner.display_name
        form.user.choices = [(user.id, user.username) for user in Users.query.order_by(Users.id)]
        return render_template('edit_owner.html', form=form)
    else:
        flash("You don't have authority to edit users")
        return redirect(url_for('/'))


@app.route('/rosters/add')
def add_rosters():
    response = requests.get(rosters_url)
    rosters = response.json()
    updated_roster_count = 0
    for r in rosters:
        owner_id = r['owner_id']
        roster_id = r['roster_id']
        t = Team.query.filter_by(id=roster_id).first()
        if t == None:
            t = Team()
            t.id = roster_id
        t.owner_id = owner_id
        db.session.add(t)
        db.session.commit()
        updated_roster_count += 1
    flash(f"Added {updated_roster_count} teams")
    return redirect("/")

@app.route('/rosters/updatetaxi')
# @login_required
def update_taxi(method="all"):
    MySys = GetSystemSettings()
    processed_date = date.today()

    if method == "auto":
        if (MySys.last_taxi_update_date):
            difference = processed_date - MySys.last_taxi_update_date
            if difference.days == 0:
                #if already updated today, return true
                print("skipped processing taxi, already did them today")
                return True

    response = requests.get(rosters_url)
    rosters = response.json()
    updated_roster_count = 0
    print("processing taxi players")
    old_taxi_players = RosterPlayer.query.filter(RosterPlayer.is_Taxi == True)
    for old_taxi_player in old_taxi_players:
        print(old_taxi_player.player.full_name)
        old_taxi_player.is_Taxi = None
        db.session.add(old_taxi_player)
        db.session.commit()
    
    print("processing new taxi players")
    #don't process new taxi players if drops turned off
    if MySys.allow_taxi_processing:
        #get Taxi and set new ones
        for r in rosters:
            roster_id = r['roster_id']
            taxi_ids = ''
            if r['taxi'] != None:
                taxi_ids = r['taxi']
            if taxi_ids:
                for taxi in taxi_ids:
                    # p = Player.query.filter_by(id=taxi).first()
                    # t = Team.query.filter_by(id=roster_id).first()
                    # flash(f'Team:{t.owner.teamname}, IR:{p.full_name}')
                    rp = RosterPlayer.query.filter(RosterPlayer.team_id == roster_id, RosterPlayer.player_id == taxi, RosterPlayer.date_removed.is_(None)).first()
                    if rp:
                        rp.is_Taxi = True
                        db.session.add(rp)
                        db.session.commit()

    #update system paramter for when last processed
    MySys.last_taxi_update_date = processed_date
    db.session.add(MySys)
    db.session.commit()

@app.route('/rosters/updateir')
# @login_required
def update_roster_ir(method="all"):
    MySys = GetSystemSettings()
    processed_date = date.today()

    if method == "auto":
        if (MySys.last_ir_update_date):
            difference = processed_date - MySys.last_ir_update_date
            if difference.days == 0:
                #if already updated today, return true
                print("skipped processing IR, already did them today")
                return True

    response = requests.get(rosters_url)
    rosters = response.json()
    updated_roster_count = 0
    # set all IR to false
    old_ir_players = RosterPlayer.query.filter(RosterPlayer.is_ir == True)
    for old_ir_player in old_ir_players:
        print(old_ir_player.player.full_name)
        old_ir_player.is_ir = False
        db.session.add(old_ir_player)
        db.session.commit()


    print("processing new IR players")
    #get IR and set new ones
    for r in rosters:
        roster_id = r['roster_id']
        reserve_id = ''
        if r['reserve'] != None:
            reserve_id = r['reserve'][0]
        if reserve_id:
            p = Player.query.filter_by(id=reserve_id).first()
            t = Team.query.filter_by(id=roster_id).first()
            # flash(f'Team:{t.owner.teamname}, IR:{p.full_name}')
            rp = RosterPlayer.query.filter(RosterPlayer.team_id == roster_id, RosterPlayer.player_id == reserve_id, RosterPlayer.date_removed.is_(None)).first()
            if rp:
                rp.is_ir = True
                db.session.add(rp)
                db.session.commit()      

    #update system paramter for when last processed
    MySys.last_ir_update_date = processed_date
    db.session.add(MySys)
    db.session.commit() 

# @app.route('/rosters/update_ir')
def update_roster_ir_and_taxi():
    update_roster_ir("auto")
    update_taxi("auto")  
    return None
           

@app.route('/rosters/')
def view_rosters():
    update_roster_ir_and_taxi()

    # teams = db.session.query(Team).join(Team.owner).order_by(Owners.teamname)
    # teams = Team.query.order_by(Team.id).all()
    teams = Team.query.join(Team.owner).order_by(Owners.teamname).all()
    print(teams)
    # my_list = teams.tolist()
    # print(my_list)

    for t in teams:
        team_roster = RosterPlayer.query.filter(RosterPlayer.team_id == t.id, RosterPlayer.date_removed.is_(None)).order_by(RosterPlayer.salary.desc())
        capholds = CapHold.query.filter(CapHold.team_id == t.id, CapHold.season == current_season).order_by(CapHold.caphold.desc())
        
        active_roster_count = 0
        taxi_count = 0
        roster_salary = 0
        total_cap_holds = 0
        # print(t.id)
        for r in team_roster:
            # print(r.id)
            if not r.is_ir: 
                if r.salary > 0:
                    roster_salary += r.salary
                if not r.is_Taxi:
                    active_roster_count += 1
                    # print(f'added to roster_count: {active_roster_count}')
            if r.is_Taxi:
                taxi_count += 1
        for c in capholds:
            total_cap_holds += c.caphold  
        
        roster_space = 18-active_roster_count
        used_cap = roster_salary + total_cap_holds
        cap_space = 200 - used_cap
        t.cap_space = cap_space
        t.used_cap = used_cap
        t.active_roster_salary = roster_salary
        t.cap_holds = total_cap_holds
        t.active_roster_count = active_roster_count
        t.roster_space = roster_space
        t.taxi_count = taxi_count


    return render_template('teams.html', teams=teams)

@app.route('/capholdsactive/')
def view_active_cap_holds():
    active_cap_holds = CapHold.query.filter(CapHold.season == GetCurrentSeason()).order_by(CapHold.team_id.asc(), CapHold.effective_date.desc(), CapHold.caphold.desc())
    return render_template('capholds.html', capholds = active_cap_holds)

@app.route('/rosters/<int:id>')
def view_roster(id):
    success = process_transactions("view_roster", method="week")
    if not success:
        flash("Error processing transactions. Please contact admininstrator")
    update_roster_ir_and_taxi()
    team = Team.query.filter_by(id = id).first()
    # team_roster = RosterPlayer.query.filter_by(team_id = id).order_by(RosterPlayer.salary.desc())
    team_roster = RosterPlayer.query.filter(RosterPlayer.team_id == id, RosterPlayer.date_removed.is_(None), RosterPlayer.is_Taxi.is_(None)).order_by(RosterPlayer.salary.desc())
    taxi_roster = RosterPlayer.query.filter(RosterPlayer.team_id == id, RosterPlayer.date_removed.is_(None), RosterPlayer.is_Taxi == True).order_by(RosterPlayer.salary.desc())

    roster_history = RosterPlayer.query.filter(RosterPlayer.team_id == id, RosterPlayer.date_removed.isnot(None), RosterPlayer.season == int(current_season)).order_by(RosterPlayer.date_removed.desc())

    for rh in roster_history:
        print(f'{rh.player.full_name}, salary:{rh.salary}, date_removed:{rh.date_removed}')

    capholds = CapHold.query.filter(CapHold.team_id == id, CapHold.season == current_season).order_by(CapHold.caphold.desc())

    active_roster_salary = 0
    active_roster_count = 0
    taxi_salary = 0
    total_cap_holds = 0

    for t in team_roster:
        if not t.is_ir:
            active_roster_salary += t.salary
            active_roster_count += 1
        # print(f'after {t.player.full_name}, active_roster_salary:{active_roster_salary}')
    for tx in taxi_roster:
        if not tx.is_ir:
            taxi_salary += tx.salary
    for c in capholds:
        total_cap_holds += c.caphold  
    used_cap = active_roster_salary + total_cap_holds + taxi_salary
    cap_space = 200 - used_cap
    roster_space = roster_max - active_roster_count

    print("test team roster")
    print(team_roster)


    return render_template('team_roster.html', 
        team=team, 
        team_roster = team_roster, 
        taxi_roster = taxi_roster,
        roster_history = roster_history,
        capholds = capholds, 
        active_roster_salary = active_roster_salary, 
        taxi_salary = taxi_salary,
        total_cap_holds = total_cap_holds, 
        used_cap = used_cap, 
        cap_space = cap_space, 
        roster_space = roster_space,
        active_roster_count = active_roster_count        
        )


@app.route('/offseasonupdate/')
def offseason_roster_update():
    # before running this, make sure to update current season variable. Do not run this twice. 
    print(f'starting offseason migration for {current_season}')
    teams = Team.query.order_by(Team.id)
    player_migrated_count = 0
    for team in teams:
        print(team.id)
    # # team_roster = RosterPlayer.query.filter_by(team_id = id).order_by(RosterPlayer.salary.desc())
        team_roster = RosterPlayer.query.filter(RosterPlayer.team_id == team.id, RosterPlayer.date_removed.is_(None)).order_by(RosterPlayer.salary.desc())
    
        for rp in team_roster:
            rp_new = RosterPlayer()
            rp_new.player_id = rp.player_id
            rp.date_removed = datetime.utcnow()
            rp.date_updated = datetime.utcnow()
            rp.is_IR = False
            #set season, make sure value is updated before this happens
            rp_new.season = current_season

            if rp.is_franchised:
                rp_new.salary = rp.unadjusted_salary #set franchised players back to previous acquired value
            else:
                if rp.unadjusted_salary: #this would only be the case for salary holdovers from trades or something like that
                    rp_new.salary = round_half_up(rp.unadjusted_salary * year_over_year_multiplier)
                elif rp.salary < 5:
                    rp_new.salary = 5
                else:
                    rp_new.salary = round_half_up(rp.salary * year_over_year_multiplier)

                    
            rp_new.unadjusted_salary = 0
            rp_new.date_added = datetime.utcnow()
            rp_new.date_updated = datetime.utcnow()
            rp_new.team_id = rp.team_id
            rp_new.is_franchised = False
            rp_new.is_ir = False
            rp_new.is_Taxi = None
            rp_new.note = f'Offseason processing July {current_season}'

            db.session.add(rp)
            db.session.add(rp_new)
            db.session.commit()
            player_migrated_count += 1
        print(f'successfully migrated {player_migrated_count} to {current_season} for team {team.owner.teamname}')

    flash(f"Migrated {player_migrated_count} players to {current_season}")
    return redirect("/")


@app.route('/exportcurrentrosters/')
def export_current_rosters():
    export_count = 0
    today = date.today().isoformat()
    filename = f"Rosters{today}.csv"
    outputFile = open(filename, 'w', newline='')
    outputWriter = csv.writer(outputFile)
    headers = ['Team Name','Player Name', 'Position', '2023 Salary']
    outputWriter.writerow(headers)
    # sample_data = ['Resident Stevil','Lamar Jackson', 'QB', '23']
        
    teams = Team.query.order_by(Team.id)
    for team in teams:
        team_roster = RosterPlayer.query.filter(RosterPlayer.team_id == team.id, RosterPlayer.season == current_season, RosterPlayer.date_removed.is_(None)).order_by(RosterPlayer.salary.desc())
        
        for rp in team_roster:
            # name = rp.Player.fullname
            datarow = [team.owner.teamname, rp.player.full_name, rp.player.position, rp.salary]
            outputWriter.writerow(datarow)
            export_count += 1
    
    # outputWriter.writerow(sample_data)
    outputFile.close()



    # teams = Team.query.order_by(Team.id)
    # for team in teams:
    #     print(team.id)
    # # # team_roster = RosterPlayer.query.filter_by(team_id = id).order_by(RosterPlayer.salary.desc())
    #     team_roster = RosterPlayer.query.filter(RosterPlayer.team_id == team.id, RosterPlayer.date_removed.is_(None)).order_by(RosterPlayer.salary.desc())
    

        # for rp in team_roster:
        #     rp_new = RosterPlayer()
        #     rp_new.player_id = rp.player_id
        #     rp.date_removed = datetime.utcnow()
        #     rp.date_updated = datetime.utcnow()
        #     #set season, make sure value is updated before this happens
        #     rp_new.season = current_season
        #     if rp.unadjusted_salary:
        #         rp_new.salary = round_half_up(rp.unadjusted_salary * year_over_year_multiplier)
        #     else:
        #         rp_new.salary = round_half_up(rp.salary * year_over_year_multiplier)
        #     rp_new.unadjusted_salary = 0
        #     rp_new.date_added = datetime.utcnow()
        #     rp_new.date_updated = datetime.utcnow()
        #     rp_new.team_id = rp.team_id
        #     rp_new.is_franchised = False
        #     rp_new.is_ir = False
        #     rp_new.note = f'Offseason processing July 2023'

        #     db.session.add(rp)
        #     db.session.add(rp_new)
        #     db.session.commit()
        #     player_migrated_count += 1

    flash(f"Exported {export_count} players to CSV")
    return redirect("/")


@app.route('/exportcurrentrosterslocal/')
def export_current_rosters_local():
    export_count = 0
    today = date.today().isoformat()
    filename = f"Rosters{today}.csv"



    # outputFile = open(filename, 'w', newline='')
    # outputWriter = csv.writer(outputFile)
    headers = ['Team Name','Player Name', 'Position', '2023 Salary']
    # outputWriter.writerow(headers)
    # sample_data = ['Resident Stevil','Lamar Jackson', 'QB', '23']
        
    output = StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow(headers)
    teams = Team.query.order_by(Team.id)
    for team in teams:
        team_roster = RosterPlayer.query.filter(RosterPlayer.team_id == team.id, RosterPlayer.season == current_season, RosterPlayer.date_removed.is_(None)).order_by(RosterPlayer.salary.desc())
        
        for rp in team_roster:
            # name = rp.Player.fullname
            datarow = [team.owner.teamname, rp.player.full_name, rp.player.position, rp.salary]
            csv_writer.writerow(datarow)
            export_count += 1
    
    # outputWriter.writerow(sample_data)

    print("Test")
    response = Response(output.getvalue())
    response.headers['Content-Disposition']= 'attachment; filename="testloggpt.csv"'
    response.headers['Content-Type']='text/csv'
        # outputFile.close()
    print("returning")
    return response


    # teams = Team.query.order_by(Team.id)
    # for team in teams:
    #     print(team.id)
    # # # team_roster = RosterPlayer.query.filter_by(team_id = id).order_by(RosterPlayer.salary.desc())
    #     team_roster = RosterPlayer.query.filter(RosterPlayer.team_id == team.id, RosterPlayer.date_removed.is_(None)).order_by(RosterPlayer.salary.desc())
    

        # for rp in team_roster:
        #     rp_new = RosterPlayer()
        #     rp_new.player_id = rp.player_id
        #     rp.date_removed = datetime.utcnow()
        #     rp.date_updated = datetime.utcnow()
        #     #set season, make sure value is updated before this happens
        #     rp_new.season = current_season
        #     if rp.unadjusted_salary:
        #         rp_new.salary = round_half_up(rp.unadjusted_salary * year_over_year_multiplier)
        #     else:
        #         rp_new.salary = round_half_up(rp.salary * year_over_year_multiplier)
        #     rp_new.unadjusted_salary = 0
        #     rp_new.date_added = datetime.utcnow()
        #     rp_new.date_updated = datetime.utcnow()
        #     rp_new.team_id = rp.team_id
        #     rp_new.is_franchised = False
        #     rp_new.is_ir = False
        #     rp_new.note = f'Offseason processing July 2023'

        #     db.session.add(rp)
        #     db.session.add(rp_new)
        #     db.session.commit()
        #     player_migrated_count += 1

    # flash(f"Exported {export_count} players to CSV")
    # return redirect("/")

@app.route('/exportcurrentrostersexcel/')
def export_current_rosters_excel():
    export_count = 0
    today = date.today().isoformat()
    filename = f"Rosters{today}.xlsx"

    wb = Workbook()


    # outputFile = open(filename, 'w', newline='')
    # outputWriter = csv.writer(outputFile)
    headers = ['Team Name','Player Name', 'Position', '2023 Salary', 'IR Salary', 'Unadjusted Salary']
    # outputWriter.writerow(headers)
    # sample_data = ['Resident Stevil','Lamar Jackson', 'QB', '23']
        
    # output = StringIO()
    # csv_writer = csv.writer(output)
    # csv_writer.writerow(headers)
    teams = Team.query.order_by(Team.id)
    current_sheet = 1
    for team in teams:   
        salary_total = 0
        team_roster = RosterPlayer.query.filter(RosterPlayer.team_id == team.id, RosterPlayer.season == current_season, RosterPlayer.date_removed.is_(None)).order_by(RosterPlayer.salary.desc())
        if current_sheet ==1:
            ws1 = wb.active
            ws1.title = team.owner.teamname
            ws1.append(headers)
            for rp in team_roster:
            # name = rp.Player.fullname
                if rp.is_ir:
                    datarow = [team.owner.teamname, rp.player.full_name, rp.player.position, '', rp.salary, rp.unadjusted_salary]
                else:
                    datarow = [team.owner.teamname, rp.player.full_name, rp.player.position, rp.salary, '',rp.unadjusted_salary]
                    salary_total += rp.salary
                ws1.append(datarow)
                # csv_writer.writerow(datarow)
            ws1.append(['Total','','',salary_total])
            export_count += 1
        else:
            ws2 = wb.create_sheet(title=team.owner.teamname)
            ws2.append(headers)
            for rp in team_roster:
            # name = rp.Player.fullname
                if rp.is_ir:
                    datarow = [team.owner.teamname, rp.player.full_name, rp.player.position, '', rp.salary, rp.unadjusted_salary]
                else:
                    datarow = [team.owner.teamname, rp.player.full_name, rp.player.position, rp.salary, '',rp.unadjusted_salary]
                    salary_total += rp.salary
                ws2.append(datarow)
                # csv_writer.writerow(datarow)
            ws2.append(['Total','','',salary_total])
            export_count += 1
        current_sheet += 1
    
    excel_data = BytesIO()
    wb.save(excel_data)
    excel_data.seek(0)

    
    # outputWriter.writerow(sample_data)

    # Prepare the HTTP response
    response = Response(excel_data.read())
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    print("returning")
    return response


@app.route('/rosterplayersactive/')
def view_active_roster_players():
    update_roster_ir_and_taxi()
    active_roster_players = RosterPlayer.query.filter(RosterPlayer.date_removed == None).order_by(RosterPlayer.team_id.asc(), RosterPlayer.date_added.asc(), RosterPlayer.salary.desc())
    return render_template('roster_players.html', roster_players = active_roster_players)

@app.route('/rosterplayersfranchised/')
def view_franchised_roster_players():
    update_roster_ir_and_taxi()
    active_roster_players = RosterPlayer.query.filter(RosterPlayer.date_removed == None, RosterPlayer.is_franchised == True).order_by(RosterPlayer.team_id.asc(), RosterPlayer.date_added.asc(), RosterPlayer.salary.desc())
    return render_template('franchised_players.html', roster_players = active_roster_players)

@app.route('/rosterplayersall/')
def view_all_roster_players():
    update_roster_ir_and_taxi()
    all_roster_players = RosterPlayer.query.filter().order_by(RosterPlayer.team_id.asc(), RosterPlayer.date_added.desc(), RosterPlayer.salary.desc())
    return render_template('roster_players.html', roster_players = all_roster_players)

@app.route('/rosterhistory/<int:id>')
def view_roster_history(id):
    update_roster_ir_and_taxi()
    roster_history = RosterPlayer.query.filter(RosterPlayer.team_id == id).order_by(RosterPlayer.team_id.asc(), RosterPlayer.date_added.desc(), RosterPlayer.salary.desc())
    return render_template('roster_players.html', roster_players = roster_history)

@app.route('/transactionsall/')
def view_all_transactions():
    # update_roster_ir_and_taxi()
    all_transactions = Transactions.query.filter().order_by(Transactions.id.desc())
    return render_template('transactions.html', transactions = all_transactions)


# @app.route('/rosters/<int:id>')
# def view_roster_history(id):
#     team = Team.query.filter_by(id = id).first()
#     team_roster = RosterPlayer.query.filter_by(team_id = id).all()
#     return render_template('team_roster.html', team=team, team_roster = team_roster)

# @app.route('/rosterplayers/')
# def update_roster_players():
#     response = requests.get(rosters_url)
#     rosters = response.json()
#     updated_player_count = 0
#     for r in rosters:
#         # team_id = r['owner_id']
#         team_id = r['roster_id']
#         for playerid in r['players']:
#             # check if player exists in Database
#             playerindb = Player.query.filter_by(id = playerid).first()
#             if playerindb == None:
#                 print(f"player id {playerid} not found")
#             else:
#                 #check if it already exists first
#                 rp = RosterPlayer.query.filter_by(player_id = playerid).first()
#                 if rp == None:                    
#                     player = RosterPlayer()
#                     player.player_id = playerid
#                     player.team_id = team_id
#                     player.season = current_season
#                     player.salary = 0
#                     player.date_added = "2022-10-01"
#                     player.date_updated = datetime.utcnow()
#                     player.is_Franchised = False
#                     db.session.add(player)
#                     db.session.commit()
#                     updated_player_count += 1
#                 #TODO: If player exists, update IR status
#     flash(f"Added {updated_player_count} players")
#     return redirect("/")
    

@app.route('/rosterplayers/csvload')
def load_initial_rosters_from_csv():
    rosterplayers = RosterPlayer.query.first()
    if rosterplayers != None:
        flash("You can't import from CSVs with rosters already in the system. please delete rosters first.")
    else:    
        with open('initial_rosters_with_salary_for_import.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    print(f'\t player_id:{row[0]}, roster_id:{row[1]}, owner_id:{row[2]}, player:{row[5]}, salary:{row[6]}, unadjusted_salary:{row[7]}, is_Franchised:{row[8]}, is_ir:{row[9]}')
                    line_count += 1
                    rp = RosterPlayer()
                    rp.team_id = row[1]
                    rp.player_id = row[0]
                    rp.season = current_season
                    rp.salary = row[6]
                    if row[7]:
                        rp.unadjusted_salary = row[7]
                    if row[8]:
                        rp.is_franchised = True
                    else:
                        rp.is_franchised = False
                    if row[9]:
                        rp.is_ir = True
                    else:
                        rp.is_ir = False
                    rp.date_added = "2022-09-01"
                    db.session.add(rp)
                    db.session.commit()


            print(f'Processed {line_count} lines.')
        
        flash(f"Processed {line_count} players")
    return redirect("/")

# @app.route('/roster_csv/')
# def load_roster_from_csv():
#     response = requests.get(rosters_url)
#     rosters = response.json()
#     updated_player_count = 0
#     for r in rosters:
#         # team_id = r['owner_id']
#         team_id = r['roster_id']
#         for playerid in r['players']:
#             # check if player exists in Database
#             playerindb = Player.query.filter_by(id = playerid).first()
#             if playerindb == None:
#                 print(f"player id {playerid} not found")
#             else:
#                 # eventually we should check if it already exists first
#                 rp = RosterPlayer.query.filter_by(player_id = playerid).first()
#                 if rp == None:                    
#                     player = RosterPlayer()
#                     player.player_id = playerid
#                     player.team_id = team_id
#                     player.season = current_season
#                     player.salary = 0
#                     player.date_added = "2022-10-01"
#                     player.date_updated = datetime.utcnow()
#                     player.is_franchised = False
#                     db.session.add(player)
#                     db.session.commit()
#                     updated_player_count += 1
#     flash(f"Added {updated_player_count} players")
#     return redirect("/")

@app.route('/rosterplayer/update/<int:id>', methods = ['GET', 'POST'])
@login_required
def updateRosterPlayer(id):
    form = PlayerRosterForm()
    rp_to_update = RosterPlayer.query.get_or_404(id)
    # print(rp_to_update.full_name)
    if request.method == "POST":
        rp_to_update.salary = request.form['salary']
        rp_to_update.unadjusted_salary = request.form['unadjusted_salary']
        rp_to_update.team_id = request.form['team']
        if request.form['date_added'] == '':
            rp_to_update.date_added = None
        else:
            rp_to_update.date_added = request.form['date_added']
        if request.form['date_removed'] == '':
            rp_to_update.date_removed = None
        else:
            rp_to_update.date_removed = request.form['date_removed']
        
        try:
            db.session.commit()
            flash("Roster Player updated successfully.")
            return redirect(url_for('view_all_roster_players'))
        except:
            flash("Oops, that didn't work.")
            return render_template('update_roster_player.html', form=form, player_to_update = rp_to_update)
    else:
        my_choice = [(team.id, team.owner.teamname) for team in Team.query.filter(Team.id == rp_to_update.team_id)]
        other_choices = [(team.id, team.owner.teamname) for team in Team.query.filter(Team.id != rp_to_update.team_id).order_by(Team.id)]
        my_choice.extend(other_choices)
        form.team.choices = my_choice
        print(rp_to_update.date_removed)
        form.date_removed.data = rp_to_update.date_removed
        form.date_added.data = rp_to_update.date_added

        return render_template('update_roster_player.html', form=form, player_to_update = rp_to_update)
    
@app.route('/rosterplayer/add/', methods = ['GET', 'POST'])
@login_required
def addRosterPlayer():
    form = AddPlayerRosterForm()
    rp_to_add = RosterPlayer()
    # print(rp_to_update.full_name)
    if request.method == "POST":
        rp_to_add.player_id = request.form['player_id']
        rp_to_add.salary = request.form['salary']
        rp_to_add.season = request.form['season']
        rp_to_add.team_id = request.form['team']
        rp_to_add.note = request.form['note']
        if request.form['date_added'] == '':
            rp_to_add.date_added = None
        else:
            rp_to_add.date_added = request.form['date_added']
        if request.form['date_removed'] == '':
            rp_to_add.date_removed = None
        else:
            rp_to_add.date_removed = request.form['date_removed']
        db.session.add(rp_to_add)

        try:
            db.session.commit()
            flash("Roster Player added successfully.")
            return redirect(url_for('view_all_roster_players'))
        except:
            flash("Oops, that didn't work.")
            return render_template('add_roster_player.html', form=form)
    else:
        team_choices = [(team.id, team.owner.teamname) for team in Team.query.order_by(Team.id).all()]
        form.team.choices = team_choices
        player_choices = [(player.id, f"{player.last_name}, {player.first_name}") for player in Player.query.order_by(Player.last_name, Player.first_name).all()]
        form.player_id.choices = player_choices
        last_season = int(current_season) - 1
        seasons = [current_season, last_season]
        form.season.choices = seasons   
        form.note.data = "Added by commissioner"
        return render_template('add_roster_player.html', form=form)
    
@app.route('/rosterplayer/franchise/', methods = ['GET', 'POST'])
@login_required
def franchiseRosterPlayer():
    form = FranchisePlayerRosterForm()
    # print(rp_to_update.full_name)
    if request.method == "POST":
        rp = RosterPlayer.query.filter(RosterPlayer.player_id == request.form['player_id'] , RosterPlayer.date_removed.is_(None)).first()
        #set unadjusted salary first, then set new salary
        rp.unadjusted_salary = rp.salary
        rp.salary = request.form['salary']
        rp.season = request.form['season']
        rp.note = request.form['note']
        # if request.form['date_added'] == '':
        #     rp_to_franchise.date_added = None
        # else:
        #     rp_to_franchise.date_added = request.form['date_added']
        rp.is_franchised = True
        # if request.form['date_removed'] == '':
        #     rp_to_add.date_removed = None
        # else:
        #     rp_to_add.date_removed = request.form['date_removed']
        try:
            db.session.commit()
            flash("Player franchised successfully.")
            return redirect(url_for('view_franchised_roster_players'))
        except:
            flash("Oops, that didn't work.")
            return render_template('franchise_roster_player.html', form=form)
    else:
        #removing team since it can automatically pick the right one
        # team_choices = [(team.id, team.owner.teamname) for team in Team.query.order_by(Team.id).all()]
        # form.team.choices = team_choices
        # player_choices = [(player.id, f"{player.last_name}, {player.first_name}") for player in Player.query.order_by(Player.last_name, Player.first_name).all()]
        players_on_rosters = Player.query.join(RosterPlayer).filter(RosterPlayer.date_removed.is_(None)).order_by(Player.last_name, Player.first_name)
        # player_choices = [(player.id, f"{player.last_name}, {player.first_name}") for player in RosterPlayer.query.filter(RosterPlayer.date_removed.is_(None)).order_by(Player.last_name, Player.first_name).all()]
        player_choices = [(player.id, f"{player.last_name}, {player.first_name}") for player in players_on_rosters]

        form.player_id.choices = player_choices
        last_season = int(current_season) - 1
        seasons = [current_season, last_season]
        form.season.choices = seasons   
        form.note.data = "Added by commissioner"
        form.date_added.data = datetime.today()
        return render_template('franchise_roster_player.html', form=form)


    
@app.route('/rosterplayer/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def deleteRosterPlayer(id):
    rp = RosterPlayer.query.get_or_404(id)
    #try to find related caphold and delete
    # caphold = CapHold.query.filter(CapHold.associated_transaction_id == rp.close_transaction_id, CapHold.player_id == rp.player_id, CapHold.team_id == rp.team_id)
    try:
        # if caphold == None:
        #     db.session.delete(caphold)
        #     db.session.commit()
        #     flash("Caphold successfully deleted.")
        db.session.delete(rp)
        db.session.commit()
        flash("Roster player successfully deleted.")
        return redirect(url_for('view_all_roster_players'))
    except:
        flash("Deletion failed.")
        return redirect(url_for('view_all_roster_players'))
    
@app.route('/transaction/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def deleteTransaction(id):
    #first find the player who was closed and reopen:
    closed_players = RosterPlayer.query.filter(RosterPlayer.close_transaction_id == id)
    for cp in closed_players:
        #try to find related caphold and delete
        # caphold = CapHold.query.filter(CapHold.associated_transaction_id == id, CapHold.player_id == cp.player_id, CapHold.team_id == cp.team_id).first()
        # if (caphold != None):
        #     db.session.delete(caphold)
        #     db.commit()        
        #remove the removed date and transaction id from closed player
        cp.date_removed = None
        cp.close_transaction_id = None
        db.session.add(cp)
        db.session.commit()
        p = Player.query.filter(Player.id == cp.player_id).first()
        print(f'successfully restored {p.full_name}')
    
    #find and delete new player
    opened_roster_players = RosterPlayer.query.filter(RosterPlayer.open_transaction_id == id)
    for op in opened_roster_players:
        db.session.delete(op)
        db.session.commit()
        p = Player.query.filter(Player.id == op.player_id).first()
        print(f'successfully deleted {p.full_name}')
    
    #delete the transaction
    transaction = Transactions.query.get_or_404(id)

    print(f'trying to delete transaction {id}')
    print(transaction)
    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction player successfully deleted.")
    return redirect(url_for('view_all_transactions'))
    # try:
    #     # if caphold == None:
    #     #     db.session.delete(caphold)
    #     #     db.session.commit()
    #     #     flash("Caphold successfully deleted.")
    #     db.session.delete(transaction)
    #     db.session.commit()
    #     flash("Transaction player successfully deleted.")
    #     return redirect(url_for('view_all_transactions'))
    # except:
    #     flash("Deletion failed.")
    #     return redirect(url_for('view_all_transactions'))
    

@app.route('/caphold/add/', methods = ['GET', 'POST'])
@login_required
def addCapHold():
    form = CapHoldForm()
    cp_to_add = CapHold()
    # print(rp_to_update.full_name)
    if request.method == "POST":
        cp_to_add.player_id = request.form['player_id']
        cp_to_add.caphold = request.form['caphold']
        cp_to_add.season = request.form['season']
        cp_to_add.team_id = request.form['team']
        cp_to_add.note = request.form['note']
        cp_to_add.reason = request.form['reason']
        if request.form['effective_date'] == '':
            cp_to_add.effective_date = None
        else:
            cp_to_add.effective_date = request.form['effective_date']
        cp_to_add.date_updated = date.today()
        db.session.add(cp_to_add)

        try:
            db.session.commit()
            flash("Cap Hold added successfully.")
            return redirect(url_for('view_active_cap_holds'))
        except:
            flash("Oops, that didn't work.")
            return render_template('add_roster_player.html', form=form)
    else:
        team_choices = [(team.id, team.owner.teamname) for team in Team.query.order_by(Team.id).all()]
        form.team.choices = team_choices
        player_choices = [(player.id, f"{player.last_name}, {player.first_name}") for player in Player.query.order_by(Player.last_name, Player.first_name).all()]
        form.player_id.choices = player_choices
        last_season = int(current_season) - 1
        seasons = [current_season, last_season]
        form.season.choices = seasons   
        form.note.data = "Added by commissioner"
        return render_template('add_cap_hold.html', form=form)

@app.route('/caphold/update/<int:id>', methods = ['GET', 'POST'])
@login_required
def updateCapHold(id):
    form = CapHoldForm()
    ch_to_update = CapHold.query.get_or_404(id)

    if request.method == "POST":
        ch_to_update.caphold = request.form['caphold']
        ch_to_update.team_id = request.form['team']
        ch_to_update.season = request.form['season']
        ch_to_update.reason = request.form['reason']
        ch_to_update.note = request.form['note']
        if request.form['effective_date'] == '':
            ch_to_update.effective_date = None
        else:
            ch_to_update.effective_date = request.form['effective_date']
        try:
            db.session.commit()
            flash("Roster Player updated successfully.")
            return redirect(url_for('index'))
        except:
            flash("Oops, that didn't work.")
            return render_template('update_cap_hold.html', form=form, caphold_to_update = ch_to_update)
    else:
        my_choice = [(team.id, team.owner.teamname) for team in Team.query.filter(Team.id == ch_to_update.team_id)]
        other_choices = [(team.id, team.owner.teamname) for team in Team.query.filter(Team.id != ch_to_update.team_id).order_by(Team.id)]
        my_choice.extend(other_choices)
        form.team.choices = my_choice
        form.effective_date.data = ch_to_update.effective_date
        form.note.data = ch_to_update.note

        return render_template('update_cap_hold.html', form=form, caphold_to_update = ch_to_update)

@app.route('/caphold/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def deleteCapHold(id):
    ch = CapHold.query.get_or_404(id)
    try:
        db.session.delete(ch)
        db.session.commit()
        flash("Cap Hold successfully deleted.")
        return redirect(url_for('index'))
    except:
        flash("Deletion failed.")
        return redirect(url_for('index'))

@app.route('/players/editsalary', methods=['GET', 'POST'])
def editSalary():
    form = PlayerRosterForm()
    if form.validate_on_submit():
        # we actually need to check the roster here
        matches = Player.query.filter_by(full_name = form.playername.data).count()
        if matches == 1:
            flash("unique match found.")
            myplayer = Player.query.filter_by(full_name = form.playername.data).first()
            roster_to_update = Roster.query.filter_by(player_id = myplayer.id).first()
            if roster_to_update == None:
                roster_to_add = Roster()
                roster_to_add.player_id = myplayer.id
                roster_to_add.salary = form.salary.data
                roster_to_add.team_id = 10
                # roster_to_add.team_id = form. calculate team id based on name
                # player_to_update.full_name = form.playername.data
                db.session.add(roster_to_add)
                db.session.commit()
                flash("player added")
                print(f"added player {form.playername.data} to roster {roster_to_add.team_id} with salary {roster_to_add.salary}")

        else:
            flash("No unique match found")
    playername = form.playername.data
    form.playername.data = ''    
    our_players = Player.query.order_by(Player.id)                   

    return render_template("edit_salary.html", form=form, playername = playername, our_players = our_players)
        
# @app.route('/players/editsalary', methods=['GET', 'POST'])
# def editSalary():
#     form = PlayerRosterForm()
#     if form.validate_on_submit():
#         # we actually need to check the roster here
#         matches = Player.query.filter_by(full_name = form.playername.data).count()
#         if matches == 1:
#             flash("unique match found.")
#             myplayer = Player.query.filter_by(full_name = form.playername.data).first()
#             roster_to_update = Roster.query.filter_by(player_id = myplayer.id).first()
#             if roster_to_update == None:
#                 roster_to_add = Roster()
#                 roster_to_add.player_id = myplayer.id
#                 roster_to_add.salary = form.salary.data
#                 roster_to_add.team_id = 10
#                 # roster_to_add.team_id = form. calculate team id based on name
#                 # player_to_update.full_name = form.playername.data
#                 db.session.add(roster_to_add)
#                 db.session.commit()
#                 flash("player added")
#                 print(f"added player {form.playername.data} to roster {roster_to_add.team_id} with salary {roster_to_add.salary}")

#         else:
#             flash("No unique match found")
#     playername = form.playername.data
#     form.playername.data = ''    
#     our_players = Player.query.order_by(Player.id)                   

#     return render_template("edit_salary.html", form=form, playername = playername, our_players = our_players)

# add code to call sleeper API
@app.route('/nflstate')
def getNFLState():
    nfl_state_url = f'https://api.sleeper.app/v1/state/{Sport}'
    nfl_state = requests.get(nfl_state_url).json()
    week = nfl_state['week']
    season = nfl_state['season']
    
    return render_template('nflstate.html', week=week, season=season)

def getNFLWeek():
    MySys = GetSystemSettings()
    processed_date = date.today()

    if (MySys.last_nfl_state_update_date):
        difference = processed_date - MySys.last_nfl_state_update_date
        if difference.days == 0:
            return MySys.current_week
    
    nfl_state_url = f'https://api.sleeper.app/v1/state/{Sport}'
    nfl_state = requests.get(nfl_state_url).json()
    week = int(nfl_state['leg'])
    MySys.current_week = week
    db.session.add(MySys)
    db.session.commit()
    return week

# simple api route to return basic player info by ID
@app.route('/player/info/<int:id>')
def get_player_info(id):
    player_to_find = Player.query.filter_by(id=id).first()
    mydict = {
        "Name": player_to_find.full_name,
        "Position": player_to_find.position, 
        "PlayerId": player_to_find.id
    }
    # for attribute, value in player_to_find.__dict__.items():
    #     mydict[attribute] = value
    # print(mydict)
    # return player_to_find.full_name
    return mydict

# simple api route to return basic player info by ID
@app.route('/player/info/limit/<int:limit>')
def get_player_info_limit(limit):
    players_to_find = Player.query.limit(limit)
    my_dict = {}
    for player in players_to_find:
        player_dict = {
            "Name": player.full_name,
            "Position": player.position, 
            "PlayerId": player.id
        }
        my_dict[player.id] = player_dict
    return my_dict

def GetAllowTransactionProcessing():
    mysys = SystemSettings.query.filter_by(id = 1).first()
    return mysys.allow_transaction_processing

def GetAllowCapholdsForDrops():
    mysys = SystemSettings.query.filter_by(id = 1).first()
    return mysys.allow_capholds_for_drops

def GetRosterMax():
    mysys = SystemSettings.query.filter_by(id = 1).first()
    return mysys.roster_max

def GetCurrentSeason():
    mysys = SystemSettings.query.filter_by(id = 1).first()
    return mysys.current_season

def GetSystemSettings():
    mysys = SystemSettings.query.filter_by(id = 1).first()
    return mysys

@app.route('/')
def index():
    return view_rosters()

@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id in admin_user_list:
        return render_template('admin.html')
    else: 
        flash("You must be an admin to access that area.")
        return redirect(url_for('index'))

# Add Post Page
@app.route('/add-post', methods=['GET', 'POST'])
#@login_required
def add_post():
	form = PostForm()

	if form.validate_on_submit():
		poster = current_user.id
		post = Posts(title=form.title.data, content=form.content.data, poster_id=poster, slug=form.slug.data)
		# post = Posts(title=form.title.data, content=form.content.data, author = form.author.data, slug=form.slug.data)

        # Clear The Form
		form.title.data = ''
		form.content.data = ''
		form.slug.data = ''

		# Add post data to database
		db.session.add(post)
		db.session.commit()

		# Return a Message
		flash("Blog Post Submitted Successfully!")

	# Redirect to the webpage
	return render_template("add_post.html", form=form)

@app.route('/posts')
def posts():
	posts = Posts.query.order_by(Posts.date_posted)
	return render_template("posts.html", posts=posts)

@app.route('/post/<int:id>')
def post(id):
	post = Posts.query.get_or_404(id)
	return render_template("post.html", post=post)


@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
            post.title = form.title.data
            # post.author = form.author.data
            post.slug = form.slug.data
            post.content = form.content.data
            # Update Database
            db.session.add(post)
            db.session.commit()
            flash("Post Has Been Updated!")
            return redirect(url_for('post', id=post.id))

    if current_user.id == post.poster.id:    
        form.title.data = post.title
        # form.author.data = post.author
        form.slug.data = post.slug
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You can only edit your own posts.")
        return redirect(url_for('posts'))

@app.route('/posts/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    post = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post.poster.id or id in admin_user_list:
        try:
            db.session.delete(post)
            db.session.commit()
            flash("Post successfully deleted.")
            return redirect(url_for('posts'))
        except:
            flash("Deletion failed.")
            return redirect(url_for('posts'))
    else:
        flash("You can't delete someone else's post.")
        return redirect(url_for('posts'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = Users.query.filter_by(username=form.username.data).first()
		if user:
			# Check the hash
			if check_password_hash(user.password_hash, form.password.data):
				login_user(user)
				flash("Login Succesfull!")
				return redirect(url_for('dashboard'))
			else:
				flash("Wrong Password - Try Again!")
		else:
			flash("That User Doesn't Exist! Try Again...")


	return render_template('login.html', form=form)

def send_reset_email(user):
    token = user.get_reset_token()
    message = f'''
Password Reset

You requested a password reset. Visit the following link to complete the reset. The link will expire after 1 hour. 
{url_for('reset_password', token=token, _external=True)}
'''
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(gmail_address, gmail_pwd)
    server.sendmail(gmail_address, user.email, message)



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    email = form.email.data
    message = "This is an automated test message from the Troy Siade Dynasty Football League."
    print(email)
    if form.validate_on_submit():
        user = Users.query.filter_by(email = email).first()

        # server = smtplib.SMTP("smtp.gmail.com", 587)
        # server.starttls()
        # print(gmail_pwd)
        # server.login('sleepersalarytracker@gmail.com', gmail_pwd)
        # server.sendmail('sleepersalarytracker@gmail.com', email, message)
        send_reset_email(user)
        flash("Reset email sent")

        return redirect(url_for('login'))
    else:
        return render_template('forgot_password.html', form=form)

@app.route('/reset_password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    print("we made it back here!")
    user = Users.verify_reset_token(token)
    if not user:
        flash("Reset token invalid or expired", 'warning')
        return redirect(url_for('forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        ## Hash the password!!!
        hashed_pw = generate_password_hash(form.password_hash.data, 'pbkdf2:sha256')
        user.password_hash = hashed_pw
        db.session.commit()
        flash("Password successfully updated!")
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	flash("You Have Been Logged Out!")
	return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        # name_to_update.teamname = request.form['teamname']
        name_to_update.username = request.form['username']
        # name_to_update.about_author = request.form['about_author']
        # name_to_update.profile_pic = request.files['profile_pic']


		# Check for profile pic
        if request.files['profile_pic']:
            name_to_update.profile_pic = request.files['profile_pic']

            # Grab Image Name
            pic_filename = secure_filename(name_to_update.profile_pic.filename)
            # Set UUID
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            # Save That Image
            saver = request.files['profile_pic']
			
            # Change it to a string to save to db
            name_to_update.profile_pic = pic_name
            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                flash("User Updated Successfully!")
                return render_template("dashboard.html", 
                    form=form,
                        name_to_update = name_to_update)
            except:
                flash("Error!  Looks like there was a problem...try again!")
                return render_template("dashboard.html", 
    				form=form,
    				name_to_update = name_to_update)
        else:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("dashboard.html", 
                form=form, 
                name_to_update = name_to_update)
    else:
        return render_template("dashboard.html", 
				form=form,
				name_to_update = name_to_update,
				id = id)

    return render_template('dashboard.html')

#pass stuff to navbar
@app.context_processor
def base():
    form = SearchForm()
    #pass in admin user list
    alist = admin_user_list
    # TODO: Add teams for dropdown 
    teams = db.session.query(Team).join(Team.owner).order_by(Owners.teamname)
    # owners = Owners.query.order_by(Owner.teamname)
    # teams = Team.query.order_by(Team.id)
    return dict(form=form, alist=alist, dropdown_teams = teams)


#search function
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    players = Player.query
    if form.validate_on_submit():
        searched = form.searched.data
        #search for matching name
        search_string = searched.replace(" ", "").lower()
        print(search_string)

        players = players.filter(Player.search_full_name.like('%' + search_string + '%'))
        players = players.order_by(Player.last_name).all()

        return render_template("search_results.html", form=form, searched = searched, players = players)


@app.route('/transactions/')
def process_transactions(source="Process Transactions", method = "all"):
    MySys = GetSystemSettings()
    processed_date = date.today()
    print(f'transaction processing method: {method}')
    print(f'System flag: allow system processing: {MySys.allow_transaction_processing}')
    print(f'System flag: allow capholds for drops: {MySys.allow_capholds_for_drops}')
    print(f'System flag: allow taxi processing: {MySys.allow_taxi_processing}')


    if method == "week":
        if (MySys.last_transaction_update_date):
            difference = processed_date - MySys.last_transaction_update_date
            print(f"last process transactions on {processed_date}")
            if difference.days == 0:
                #if already updated today, return true
                print("skipped processing transactions, already did them today")
                return True

    #TODO: Change this to use value from system_Settings
    if MySys.allow_transaction_processing:
        week = getNFLWeek()
        league_status = getLeagueStatus()
        print(week)
        
        missing_player_ids = []

        for i in range(week + 2):
            print(f'current week: {week}, currently processing leg {i}')
            transaction_dates_list = []
            transaction_date_id_dict = {}
            transaction_week = i #this may not be a reliable number later in the year?
            if method == "week" and i not in [week, week+1]:
                print(f'only processing transactions for week {week}, skipping week {i}')
                continue
            else:
                print(f'current week {week}, processing transactions for week {i}')



            print(f'week {transaction_week} transactions-------------------------------------------------------------------------')

            transactions_url = f'https://api.sleeper.app/v1/league/{LeagueId}/transactions/{transaction_week}'
            print(transactions_url)
            response = requests.get(transactions_url)
            transactions = response.json()
            added_transaction_count = 0
            added_roster_player_count = 0
            added_cap_hold_count = 0
            transaction_counter = 0

            for t in transactions:
                # transaction_status = t['status']
                # transaction_type = t['type']
                # roster_id = t['roster_ids'][0]
                tid = t['transaction_id']
                # if tid == '875193377745268736' or tid == 875193377745268736:
                #     print('------------------------------------------------------------------------------------------------------------------------------')
                #     print('FOUND IT. TRANSACTION 875193377745268736 -------------------------------------------------------------------------------------')
                #     print('------------------------------------------------------------------------------------------------------------------------------')
                transaction_dt_milli = t['status_updated']
                
                # increment millisecond date if needed for simultaneous transactions
                date_already_used = True
                while date_already_used:
                    if transaction_dt_milli in transaction_dates_list:
                        transaction_dt_milli += 1
                    else:
                        date_already_used = False
                transaction_dates_list.append(transaction_dt_milli)
                temp_list = [transaction_counter, tid]
                transaction_date_id_dict[transaction_dt_milli] = temp_list
                transaction_counter += 1

            #we need to sort transactions by date first and then process so that they're in the right order for adds/drops in close succession
            transaction_dates_list.sort()
            print(f'transactions sorted by date:{transaction_dates_list}')
            print(f'transactions dict:{transaction_date_id_dict}')
            # if len(transaction_dates_list) > 0:
            #     print(transaction_date_id_dict[transaction_dates_list[0]])
            #     print(transactions[transaction_date_id_dict[transaction_dates_list[0]][0]]['transaction_id'])
            
            for i in transaction_dates_list:
                t = transactions[transaction_date_id_dict[i][0]]
                transaction_status = t['status']
                transaction_type = t['type']
                roster_id = t['roster_ids'][0]
                tid = t['transaction_id']

                # if tid == '875193377745268736' or tid == 875193377745268736:
                #     print('------------------------------------------------------------------------------------------------------------------------------')
                #     print('FOUND IT. TRANSACTION 875193377745268736 -------------------------------------------------------------------------------------')
                #     print('------------------------------------------------------------------------------------------------------------------------------')
                
                #check if we already have this transaction
                transaction = Transactions.query.filter_by(id=tid).first()

                if transaction == None: #transaction not processed previously, proceed
                    week = t['leg']
                    dropped_player_id = None
                    added_player_id = None
                    salary = 0 #default is 0

                    transaction_dt = pd.to_datetime(t['status_updated'], unit='ms')
                    
                    csv_load_date = pd.to_datetime("2022-09-01")

                    # print(f"status: {transaction_status}, type: {transaction_type}, roster_id:{roster_id}, week:{week}")
                    if transaction_status == 'complete' and transaction_dt < csv_load_date:
                        print(f'transaction with {tid}, dt:{transaction_dt} before transaction load date')
                    if transaction_status == 'complete' and transaction_dt > csv_load_date:
                        # print(f'transaction_datetime: {transaction_dt}')
                        transaction_to_save = Transactions()
                        transaction_to_save.id = tid
                        transaction_to_save.transaction_type = transaction_type
                        transaction_to_save.roster_id = roster_id
                        transaction_to_save.transaction_date = transaction_dt
                        transaction_to_save.status_updated = datetime.utcnow()
                        transaction_to_save.season = MySys.current_season
                        db.session.add(transaction_to_save)
                        db.session.commit()
                        added_transaction_count += 1
                                                            
                    
                        #handle waiver pickups
                        if transaction_type == 'waiver':
                            added_player_id = list(t['adds'].keys())[0]
                            added_player = Player.query.filter_by(id=added_player_id).first()
                            if added_player == None:
                                missing_player_ids.append(added_player_id)
                            else:                                
                                # print(t['settings'])
                                if (t['settings'] != None):
                                    salary = t['settings']['waiver_bid']
                                                
                                print(f'added player id: {added_player_id}')                        
                                #TODO:ADD CODE HERE TO ADD PLAYERS
                                new_rp = RosterPlayer()
                                new_rp.player_id = added_player_id
                                new_rp.team_id = roster_id
                                new_rp.season = current_season
                                new_rp.salary = salary
                                new_rp.is_Franchised = False
                                new_rp.is_ir = False
                                new_rp.date_added = transaction_dt
                                new_rp.date_updated = datetime.utcnow()
                                new_rp.open_transaction_id = tid
                                db.session.add(new_rp)
                                db.session.commit()

                                added_roster_player_count += 1

                                # print(f'salary: {salary}')
                        if transaction_type != "trade":
                            #for dropped players, close that roster player and add to capholds
                            if t['drops'] != None:
                                    dropped_player_found = False
                                    dropped_player_id = list(t['drops'].keys())[0]
                                    id = 0
                                    try:
                                        id = int(dropped_player_id)
                                    except:
                                        print(f"dropped_player_id {dropped_player_id} not valid.") #this happens for dsts
                                        dropped_player_id = None
                                    print(f'dropped_player_id:{dropped_player_id}, dropped_id: {id}')
                                    if id:
                                        dropped_player = Player.query.filter_by(id=id).first()
                                        if dropped_player != None:
                                            print(f"Dropped player:{dropped_player.full_name}")
                                            dropped_player_found = True
                                        else:
                                            dropped_player_id = None #not found in DB, don't add to transactions
                                    if dropped_player_found:
                                        #find open rosterplayer
                                        # rp = RosterPlayer.query.filter(RosterPlayer.team_id == roster_id, RosterPlayer.player_id == id, RosterPlayer.date_removed == None).first()
                                        rp = RosterPlayer.query.filter(RosterPlayer.team_id == roster_id, RosterPlayer.player_id == id, RosterPlayer.date_removed.is_(None)).first()
                                        if rp != None:
                                            print(f"successfully found dropped player {rp.player.full_name} in roster players")
                                            rp.date_removed = transaction_dt
                                            rp.close_transaction_id = tid
                                            # if league_status != "pre_draft": #don't add caphold for predraft drops
                                            # changing this logic to set dates
                                            if MySys.allow_capholds_for_drops:
                                                cp = CapHold()
                                                cp.team_id = rp.team_id
                                                cp.player_id = rp.player_id
                                                cp.season = MySys.current_season
                                                if rp.salary > 0:
                                                    cp.caphold = rp.salary * caphold_multiplier
                                                else:
                                                    cp.caphold = 0
                                            #TODO: double check that this logic is ok for franchised players as well
                                                cp.reason = "Dropped by owner"
                                                cp.effective_date = transaction_dt
                                                cp.date_updated = datetime.utcnow()
                                                cp.associated_transaction_id = tid
                                                db.session.add(cp)
                                                if cp:
                                                    print(f'capholdid: {cp.id}')
                                                    print(f"added player {rp.player.full_name} to caphold with hold of {cp.caphold}----------------------------")
                                                    added_cap_hold_count += 1
                                            else:
                                                print(f'No caphold added, transaction date {transaction_dt} before season start')
                                            db.session.add(rp)                                        
                                            db.session.commit()

                                            # all_roster_players = RosterPlayer.query.filter(RosterPlayer.date_removed == None).order_by(RosterPlayer.salary.desc())
                                    
                                    #TODO: figure out why it's showing drops from AUgust    
                                    # dropped_player = getPlayerFullNameByPlayerId(dropped_player)
                                    print(f'dropped player_id: {dropped_player_id}')  
                            if added_player_id:
                                transaction_to_save.added_player_id = added_player_id
                            if dropped_player_id:
                                transaction_to_save.dropped_player_id = dropped_player_id
                            transaction_to_save.added_salary = salary
                            transaction_to_save.transaction_date = transaction_dt
                            transaction_to_save.status_updated = datetime.utcnow()
                            transaction_to_save.season = MySys.current_season
                            db.session.add(transaction_to_save)
                            db.session.commit()

                        #process trades
                        if transaction_type == "trade":
                            # save each part of the trade
                            dropped_players = t['drops']
                            added_players = t['adds']

                            trade_partners_drops = {}
                            trade_partners_adds = {}
                            trade_adds_salaries = {}

                            if (dropped_players):
                                for i in dropped_players.keys():
                                    trade_roster_id = dropped_players[i]
                                    if trade_roster_id in trade_partners_drops:
                                        trade_partners_drops[trade_roster_id].append(i) #add to the list
                                    else:
                                        trade_partners_drops[trade_roster_id] = [i]
                            if (added_players):
                                
                                for i in added_players.keys():
                                    trade_roster_id = added_players[i]
                                    if trade_roster_id in trade_partners_adds:
                                        trade_partners_adds[trade_roster_id].append(i)
                                    else:
                                        trade_partners_adds[trade_roster_id] = [i]

                                    #get salaries for adds
                                    rp = RosterPlayer.query.filter(RosterPlayer.player_id == i, RosterPlayer.date_removed.is_(None)).first()
                                    if rp != None:
                                        salary = 0
                                        if rp.is_franchised:
                                            salary = rp.unadjusted_salary
                                        else:
                                            salary = rp.salary
                                        trade_adds_salaries[i] = salary           

                            print(f'trade_partner_drops:{trade_partners_drops}, trade_partner_adds:{trade_partners_adds}')
                            print(f'trade_adds_salaries:{trade_adds_salaries}')
                
                            
                            trade_teams = trade_partners_adds.keys()
                            for i in trade_teams:
                                roster_adds = []
                                roster_drops = []
                                if i in trade_partners_adds:
                                    roster_adds = trade_partners_adds[i]
                                if i in trade_partners_drops:
                                    roster_drops = trade_partners_drops[i]
                                number_of_adds = len(roster_adds)
                                number_of_drops = len(roster_drops)
                                number_of_transactions = number_of_adds
                                if number_of_drops > number_of_transactions:
                                    number_of_transactions = number_of_drops
                                # add 1 row per add/drop for that roster
                                for x in range(number_of_transactions):
                                    trade_transaction_to_save = TradeTransaction()
                                    trade_transaction_to_save.transaction_id = tid
                                    trade_transaction_to_save.roster_id = i
                                    if number_of_adds > x:
                                        print(f'x={x}, number_of_adds={number_of_adds}')
                                        trade_transaction_to_save.added_player_id = roster_adds[x]
                                    if number_of_drops > x:
                                        print(f'x={x}, number_of_drops={number_of_drops}')
                                        trade_transaction_to_save.dropped_player_id = roster_drops[x]
                                    trade_transaction_to_save.transaction_date = transaction_dt
                                    trade_transaction_to_save.season = MySys.current_season
                                    db.session.add(trade_transaction_to_save)
                                    print(trade_transaction_to_save)
                                    db.session.commit()
                            
                            #drop all players in dropped players
                            for i in dropped_players.keys():
                                roster_id = dropped_players[i]
                                rp = RosterPlayer.query.filter(RosterPlayer.player_id == i, RosterPlayer.team_id == roster_id, RosterPlayer.date_removed.is_(None)).first()
                                if rp == None:
                                    e = ErrorLog()
                                    e.transaction_id = tid
                                    e.player_id = i
                                    e.error_date = datetime.utcnow()
                                    

                                    print(f'Could not find traded dropped player with id {i}. Verify if there was an issue. --------------------')
                                else:
                                    rp.date_removed = transaction_dt
                                    rp.date_updated = datetime.utcnow()
                                    rp.close_transaction_id = tid
                                    db.session.add(rp)
                                    db.session.commit()
                            #add all players in added players
                            for i in added_players.keys():
                                roster_id = added_players[i]
                                rp = RosterPlayer()
                                rp.player_id = i
                                rp.team_id = roster_id
                                rp.season = MySys.current_season
                                rp.open_transaction_id = tid
                                if i in trade_adds_salaries:
                                    rp.salary = trade_adds_salaries[i]
                                else:
                                    print(f"couldn't find salary for id {i}")
                                rp.date_added = transaction_dt
                                rp.date_updated = datetime.utcnow()
                                rp.is_franchised = False
                                db.session.add(rp)
                                db.session.commit()                 

                            print(f'trade_teams: {trade_teams}, drops:{trade_partners_drops}, adds: {trade_partners_adds}')

                                # print(f'player_Dropped_in_Trade:{i}, trade_roster_id:{dropped_players[i]}')


        # flash(f"Added {added_transaction_count} transactions")
        # flash(f"Added {added_roster_player_count} players to rosters")
        # flash(f"Moved {added_cap_hold_count} dropped players to capholds")

        #save time of processing
        MySys.last_transaction_update_date = processed_date
        db.session.add(MySys)
        db.session.commit()

        if source == 'Process Transactions':
            flash(f"Processed transactions for week {transaction_week}: added {added_transaction_count} transactions, added {added_roster_player_count} players to rosters, Moved {added_cap_hold_count} dropped players to capholds")
            return redirect("/")
        else: 
            return True
    else:
        return False


@app.route('/rookiedraft/')
@login_required
def process_rookie_draft():
    draft_id = getLeagueRookieDraft()
    draft_url = f'https://api.sleeper.app/v1/draft/{draft_id}/picks'
    print(draft_url)
    response = requests.get(draft_url)
    rookies = response.json()
    print("rookies:")
    print(rookies)

    filename = f'rookiedraft{current_season}.csv'
    outputFile = open(filename, 'w', newline='')
    outputWriter = csv.writer(outputFile)
    headers = ['Pick Number','Team Name','Player Name', 'Position', f'{current_season} Salary']
    outputWriter.writerow(headers)

    #get owner and teamname data. should probably refactor to pull from DB but this works currently
    owner_dict = {}
    rosters = requests.get(rosters_url).json()
    for roster in rosters:
        owner_dict[roster['roster_id']] = roster['owner_id']
    print(owner_dict)
    teamname_dict = {}
    owners = requests.get(league_users_url).json()
    # owners
    for owner in owners:
        teamname_dict[owner['user_id']] = owner['display_name']
        try:
            teamname_dict[owner['user_id']] = owner['metadata']['team_name']
        except:
            pass
    print("teamnames:")
    print(teamname_dict)        
    
    print("rookies:")
    print(rookies)

    for i in rookies:
        if i['pick_no'] == 1:
            salary = 25
        elif i['pick_no'] in [2,3]:
            salary = 20
        elif i['pick_no'] in [4,5]:
            salary = 15
        elif i['round'] == 1:
            salary = 10
        elif i['round'] == 2:
            salary = 5
        else:
            salary = 1
        name = f"{i['metadata']['first_name']} {i['metadata']['last_name']}"
        datarow = [i['pick_no'], 
                teamname_dict[owner_dict[i['roster_id']]],
                name,
                i['metadata']['position'], 
                salary]
        outputWriter.writerow(datarow)
        print(f"{i['pick_no']}: {teamname_dict[owner_dict[i['roster_id']]]} {i['metadata']['first_name']} {i['metadata']['last_name']} {i['metadata']['position']} (${salary})")
    outputFile.close()

    #for each draft pick, check if already rostered. if so skip and throw error
    for i in rookies:
        rp = RosterPlayer.query.filter(RosterPlayer.player_id == i['player_id']).first()
        if rp == None:
            rp = RosterPlayer()
            rp.player_id = i['player_id']
            
            #get salary
            if i['pick_no'] == 1:
                rp.salary = 25
            elif i['pick_no'] in [2,3]:
                rp.salary = 20
            elif i['pick_no'] in [4,5]:
                rp.salary = 15
            elif i['round'] == 1:
                rp.salary = 10
            elif i['round'] == 2:
                rp.salary = 5
            else:
                rp.salary = 1

            # rp.team_id = GetTeamIdbyOwnerId(i['picked_by'])
            rp.team_id = i['roster_id']
            rp.season = current_season
            rp.is_Franchised = False
            rp.is_ir = False
            rp.date_added = getRookieDraftDate()
            rp.date_updated = datetime.utcnow()
            rp.note = f"added in rookie draft {current_season} with pick {i['pick_no']}"
            # rp.open_transaction_id = tid
            db.session.add(rp)
            db.session.commit()
            flash(f"{i['pick_no']}: {teamname_dict[owner_dict[i['roster_id']]]} {i['metadata']['first_name']} {i['metadata']['last_name']} {i['metadata']['position']} (${rp.salary})")
        else:
            flash(f"Could not add {i['metadata']['first_name']} {i['metadata']['last_name']}, already on a roster")
    return redirect("/")
 


@app.route('/auctiondraft/')
@login_required
def process_auction_draft():
    draft_id = getLeagueAuctionDraft()
    draft_url = f'https://api.sleeper.app/v1/draft/{draft_id}/picks'
    print(draft_url)
    response = requests.get(draft_url)
    auction = response.json()

    filename = f'auctiondraft{current_season}.csv'
    outputFile = open(filename, 'w', newline='')
    outputWriter = csv.writer(outputFile)
    headers = ['Pick Number','Team Name','Player Name', 'Position', f'{current_season} Salary']
    outputWriter.writerow(headers)

    #get owner and teamname data. should probably refactor to pull from DB but this works currently
    owner_dict = {}
    rosters = requests.get(rosters_url).json()
    for roster in rosters:
        owner_dict[roster['roster_id']] = roster['owner_id']
    print(owner_dict)
    teamname_dict = {}
    owners = requests.get(league_users_url).json()
    # owners
    for owner in owners:
        teamname_dict[owner['user_id']] = owner['display_name']
        try:
            teamname_dict[owner['user_id']] = owner['metadata']['team_name']
        except:
            pass
    # print("teamnames:")
    # print(teamname_dict)        
    
    # print("rookies:")
    # print(rookies)

    for i in auction:
        if i['metadata']['position'] in ('QB', 'RB', 'WR', 'TE', 'K'):
            salary = i['metadata']['amount']
            name = f"{i['metadata']['first_name']} {i['metadata']['last_name']}"
            datarow = [i['pick_no'], 
                    teamname_dict[owner_dict[i['roster_id']]],
                    name,
                    i['metadata']['position'], 
                    salary]
            outputWriter.writerow(datarow)
            print(f"{i['pick_no']}: {teamname_dict[owner_dict[i['roster_id']]]} {i['metadata']['first_name']} {i['metadata']['last_name']} {i['metadata']['position']} (${salary})")
    outputFile.close()

    #for each draft pick, check if already rostered. if so skip and throw error
    for i in auction:
        if i['metadata']['position'] in ('QB', 'RB', 'WR', 'TE', 'K'):
            rp = RosterPlayer.query.filter(RosterPlayer.player_id == i['player_id'], RosterPlayer.date_removed.is_(None)).first()
            if rp == None:
                rp = RosterPlayer()
                rp.player_id = i['player_id']
                salary = i['metadata']['amount']

                # rp.team_id = GetTeamIdbyOwnerId(i['picked_by'])
                rp.team_id = i['roster_id']
                rp.salary = salary
                rp.season = current_season
                rp.is_Franchised = False
                rp.is_ir = False
                rp.date_added = getAuctionDraftDate()
                rp.date_updated = datetime.utcnow()
                rp.note = f"added in auction draft {current_season} with salary {i['metadata']['amount']}"
                # rp.open_transaction_id = tid
                db.session.add(rp)
                db.session.commit()
                flash(f"{i['pick_no']}: {teamname_dict[owner_dict[i['roster_id']]]} {i['metadata']['first_name']} {i['metadata']['last_name']} {i['metadata']['position']} (${salary})")
            else:
                flash(f"Could not add {i['metadata']['first_name']} {i['metadata']['last_name']}, already on a roster")
    return redirect("/")

#all models go below here ---------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    # about_author = db.Column(db.Text(), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    profile_pic = db.Column(db.String(), nullable=True)
    # User Can Have Many Posts 
    posts = db.relationship('Posts', backref='poster')
    owner = db.relationship('Owners', backref='user')

    # Do some password stuff!
    password_hash = db.Column(db.String(128))

    # Create A String
    def __repr__(self):
        return '<Name %r>' % self.name

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # def get_reset_token(self, seconds = '3600'):
    #     s = Serializer(secret_key, seconds)
    #     return s.dumps({'user_id':str(self.id)}).decode('utf-8')

    # @staticmethod
    # def verify_reset_token(token):
    #     s = Serializer(secret_key)
    #     try:
    #         user_id = s.loads(token)['user_id']
    #     except:
    #         return None
    #     return Users.query.get(user_id)

    def get_reset_token(self):
        # s = Serializer(secret_key, expires_in = 3600)
        s = Serializer(secret_key)
        print()
        # return s.dumps({'user_id':self.id}).decode('utf-8')
        return s.dumps({'user_id':self.id})


    @staticmethod
    def verify_reset_token(token):
        print("still good")
        s = Serializer(secret_key)
        print("no issues")
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Users.query.get(user_id)

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    # author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255))
    #create foreign key to link to users
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))



class Player(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    full_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(20))
    first_name = db.Column(db.String(20))
    search_full_name = db.Column(db.String(50))
    search_last_name = db.Column(db.String(20))
    search_first_name = db.Column(db.String(20))
    position = db.Column(db.String(20))
    status = db.Column(db.String(50))
    team = db.Column(db.String(20))
    # player can have many roster rows 
    roster_players = db.relationship('RosterPlayer', backref='player')
    caphold_players = db.relationship('CapHold', backref='player')

# rosters = db.relationship('Roster', backref='player', lazy=True)
# date_added
# date_updated
    
class Team(db.Model):
    id = db.Column(db.Integer, primary_key = True) #this is the roster_id (1-12)
    # team has many roster players 
    roster_players = db.relationship('RosterPlayer', backref='team')
    capholds = db.relationship('CapHold', backref='team')
    owner_id = db.Column(db.String(20), db.ForeignKey('owners.id'))
    # last_name = db.Column(db.String(20))
    # first_name = db.Column(db.String(20))
    # search_full_name = db.Column(db.String(40))
    # search_last_name = db.Column(db.String(20))
    # search_first_name = db.Column(db.String(20))
    # position = db.Column(db.String(20))

class RosterPlayer(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    season = db.Column(db.Integer)
    salary = db.Column(db.Numeric)
    unadjusted_salary = db.Column(db.Numeric)
    is_franchised = db.Column(db.Boolean)
    is_ir = db.Column(db.Boolean)
    date_added = db.Column(db.DateTime)
    date_removed = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    open_transaction_id = db.Column(db.BigInteger, db.ForeignKey('transactions.id'))
    close_transaction_id = db.Column(db.BigInteger, db.ForeignKey('transactions.id'))
    note = db.Column(db.String(200))
    is_Taxi = db.Column(db.Boolean)


# player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)

class CapHold(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    season = db.Column(db.Integer)
    caphold = db.Column(db.Numeric)
    reason = db.Column(db.String(20))
    note = db.Column(db.String(200))
    effective_date = db.Column(db.DateTime) #date that the transaction occurred
    date_updated = db.Column(db.DateTime) #date that the transaction got added to DB
    associated_transaction_id = db.Column(db.BigInteger, db.ForeignKey('transactions.id'))


class Transactions(db.Model):
    id = db.Column(db.BigInteger, primary_key = True) #this is so we can use the same ids as sleeper
    transaction_type = db.Column(db.String(20))
    roster_id = db.Column(db.Integer)
    dropped_player_id = db.Column(db.Integer)
    added_player_id = db.Column(db.Integer)
    added_salary = db.Column(db.Numeric)
    transaction_date = db.Column(db.DateTime)
    trade = db.relationship('TradeTransaction', backref='transaction')
    # open_roster_player = db.relationship('RosterPlayer', backref='transaction')
    # close_roster_player = db.relationship('RosterPlayer', backref='transaction')
    caphold = db.relationship('CapHold', backref='transaction')
    season = db.Column(db.Integer)

class ErrorLog(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    transaction_id = db.Column(db.BigInteger)
    roster_player_id = db.Column(db.Integer)
    player_id = db.Column(db.Integer)
    cap_hold_id = db.Column(db.Integer)
    roster_id = db.Column(db.Integer)
    error_description = db.Column(db.String(20))
    error_notes = db.Column(db.String(200))
    error_date = db.Column(db.DateTime)

# this class tracks when last data pulls occurred
class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    last_player_update_date = db.Column(db.Date)
    last_nfl_state_update_date = db.Column(db.Date)
    last_owner_update_date = db.Column(db.Date)
    last_roster_update_date = db.Column(db.Date)
    last_transaction_update_date = db.Column(db.Date)
    last_ir_update_date = db.Column(db.Date)
    last_taxi_update_date = db.Column(db.Date)
    current_season = db.Column(db.Integer)
    roster_max = db.Column(db.Integer)
    allow_transaction_processing = db.Column(db.Boolean)
    allow_capholds_for_drops = db.Column(db.Boolean)
    current_week = db.Column(db.Integer)
    allow_taxi_processing = db.Column(db.Boolean)


#a transaction which is a trade gets stored as multiple rows, 1 or more per team depending on number of players in trade
class TradeTransaction(db.Model):
    id = db.Column(db.Integer, primary_key = True) 
    transaction_id = db.Column(db.BigInteger, db.ForeignKey('transactions.id')) #there can be multiple rows per trade
    roster_id = db.Column(db.Integer)
    dropped_player_id = db.Column(db.Integer)
    added_player_id = db.Column(db.Integer)
    transaction_date = db.Column(db.DateTime)
    season = db.Column(db.Integer)

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(20))
    comment = db.Column(db.String(1000))

class Owners(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    display_name = db.Column(db.String(50))
    teamname = db.Column(db.String(50))
    date_updated = db.Column(db.DateTime, default=datetime.utcnow)
    avatar = db.Column(db.String(), nullable=True)
    #every active owner has a teamroster
    team = db.relationship('Team', backref='owner')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
  





if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))