from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, SelectField, IntegerField, DateTimeLocalField, DateTimeField, DecimalField, DateField
from wtforms.validators import DataRequired, EqualTo, Length, Email, ValidationError
from wtforms.widgets import TextArea
from flask_ckeditor import CKEditorField
# from app import Users


#Form for Blog Posts
class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    # content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    content = CKEditorField('Content', validators=[DataRequired()])
    # author = StringField("Author")
    slug = StringField("Slug", validators=[DataRequired()])
    submit = SubmitField("Submit")

class PasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
        # email = StringField("Email", validators=[DataRequired(), Email()])
    password_hash = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired()])
        # email = StringField("Email", validators=[DataRequired(), Email()])

    teamname = StringField("Teamname")
    password_hash = PasswordField('Password', validators = [DataRequired(), EqualTo('password_hash2', "Passwords must match.")])
    password_hash2 = PasswordField('Confirm Password', validators = [DataRequired()])
    profile_pic = FileField("Profile Pic")
    submit = SubmitField("Submit")

    # def validate_username(self, username):
    #     user = Users.query.filter_by(username=username.data).first()
    #     if user:
    #         raise ValidationError('That username is taken. Please choose a different one.')

    # def validate_email(self, email):
    #     user = Users.query.filter_by(email=email.data).first()
    #     if user:
    #         raise ValidationError('That email is taken. Please choose a different one.')

class OwnerForm(FlaskForm):
    displayname = StringField("Owner", validators=[DataRequired()])
    user = SelectField("User", choices = [])
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Submit")

class ForgotPasswordForm(FlaskForm):
    # email = StringField("Please provide your email to receive a reset password link:", validators=[DataRequired(), Email()])
    email = StringField("Please provide your email to receive a reset password link:", validators=[DataRequired()])

    submit = SubmitField("Submit")

    # def validate_email(self, email):
    #     user = Users.query.filter_by(email=email.data).first()
    #     if user is None:
    #         raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password_hash = PasswordField('Password', validators = [DataRequired(), EqualTo('password_hash2', "Passwords must match.")])
    password_hash2 = PasswordField('Confirm Password', validators = [DataRequired()])
    submit = SubmitField('Reset Password')

class PlayerForm(FlaskForm):
    playername = StringField("Player")
    salary = DecimalField("Salary", validators=[DataRequired()])
    teamname = StringField("Team Name")
    submit = SubmitField("Submit")

class PlayerRosterForm(FlaskForm):
    playername = StringField("Player")
    salary = DecimalField("Salary", validators=[DataRequired()])
    team = SelectField("Team", choices = [], coerce = int)
    date_added = DateTimeLocalField("Date Added", format = "%Y-%m-%d %H:%M")
    date_removed = DateTimeLocalField("Date Removed", format = "%Y-%m-%d %H:%M")
    submit = SubmitField("Submit")

class AddPlayerRosterForm(FlaskForm):
    player_id = SelectField("Player", choices = [])
    salary = DecimalField("Salary", validators=[DataRequired()])
    team = SelectField("Team", choices = [], coerce = int)
    season = SelectField("Season", choices = [], coerce = int)
    note = StringField("Note")
    date_added = DateTimeLocalField("Date Added", format = "%Y-%m-%d %H:%M")
    date_removed = DateTimeLocalField("Date Removed", format = "%Y-%m-%d %H:%M")
    submit = SubmitField("Submit")

class FranchisePlayerRosterForm(FlaskForm):
    player_id = SelectField("Player", choices = [])
    salary = DecimalField("Franchised Salary", validators=[DataRequired()])
    team = SelectField("Team", choices = [], coerce = int)
    season = SelectField("Season", choices = [], coerce = int)
    note = StringField("Note")
    date_added = DateField("Date Added", format = "%Y-%m-%d")
    # date_removed = DateField("Date Removed", format = "%Y-%m-%d")
    submit = SubmitField("Submit")

class CapHoldForm(FlaskForm):
    playername = StringField("Player")
    team = SelectField("Team", choices = [], coerce = int)
    caphold = DecimalField("Cap Hold", validators=[DataRequired()])
    season = IntegerField("Season", validators=[DataRequired()])
    reason = StringField("Reason", validators=[Length(max=20)])
    note = CKEditorField('Note')
    effective_date = DateTimeField("Effective Date", format = "%Y-%m-%d")
    submit = SubmitField("Submit")

class SearchForm(FlaskForm):
    searched = StringField("searched", validators=[DataRequired()])
    submit = SubmitField("Submit")