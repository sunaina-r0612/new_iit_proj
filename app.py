from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime

app = Flask(__name__)

import config

import models

import routes

if __name__ == '__main__':
    app.run(debug=True)