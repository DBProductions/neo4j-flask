#!/usr/bin/env python
from models import User, Language, get_last_projects, get_users, get_users_projects, get_project_likes, get_all_languages, get_users_languages
from flask import Flask, request, redirect, session, abort, url_for, render_template

app = Flask(__name__)

@app.route('/')
def index():
    projects = get_last_projects()
    users = get_users()
    return render_template('index.html', projects=projects, users=users)

@app.route('/register', methods=['GET','POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        if len(email) < 1:
            error = 'You must send us an email.'
        elif len(password) < 5:
            error = 'Your password must be at least 5 characters.'
        elif not User(email=email, username=username).register(password):
            error = 'A user with that email already exists.'
        else:
            session['email'] = email
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not User(email=email).verify_password(password):
            error = 'Invalid login.'
        else:
            user = User(email=email).find()
            session['email'] = email
            session['username'] = user['username']
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/add_language', methods=['POST'])
def add_language():
    language = request.form['language']
    User(session['email']).add_language(Language(language).find())
    return redirect(url_for('profile', username=session['username']))

@app.route('/add_project', methods=['POST'])
def add_project():
    title = request.form['title']
    tags = request.form['tags']
    repository = request.form['repository']

    if not title:
        abort(400, 'You must give your post a title.')
    if not tags:
        abort(400, 'You must give your post at least one tag.')
    if not repository:
        abort(400, 'You must give your post a repository.')

    User(session['email']).add_project(title, tags, repository)
    return redirect(url_for('profile', username=session['username']))

@app.route('/like_project/<project_id>')
def like_project(project_id):
    email = session.get('email')
    username = session.get('username')
    if not username:
        abort(400, 'You must be logged in to like a project.')
    User(email).like_project(project_id)
    return redirect(request.referrer)

@app.route('/profile/<username>')
def profile(username):
    _user = User(username=username)
    user = _user.find()
    email = user['email']

    all_languages = get_all_languages(email)
    languages = get_users_languages(email)
    projects = get_users_projects(email)

    similar = []
    common = []

    viewer_email = session.get('email')
    if viewer_email:
        viewer = User(viewer_email)
        if viewer.email == email:
            similar = viewer.get_similar_users()
        else:
            common = viewer.get_commonality_of_user(email)

    return render_template(
        'profile.html',
        email=email,
        username=user['username'],
        languages=languages,
        all_languages=all_languages,
        projects=projects,
        similar=similar,
        common=common
    )

