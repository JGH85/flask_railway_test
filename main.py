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
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import csv
from decimal import Decimal
import math
from datetime import date  
import pandas as pd

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))