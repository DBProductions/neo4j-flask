#!/usr/bin/env python
""" application file """
from flask import Flask, request, redirect, session, abort, url_for, render_template
from models import queries, user, language
from py2neo import Graph

APP = Flask(__name__)

graph = Graph('http://neo4j:neo4j@192.168.99.100:7474/db/data/')

@APP.route('/')
def index():
    """ index handler """
    projects = queries.get_last_projects(graph)
    users = queries.get_users(graph)
    languages = queries.get_languages(graph)
    return render_template('index.html',
                           projects=projects,
                           users=users,
                           languages=languages)

@APP.route('/register', methods=['GET', 'POST'])
def register():
    """ register handler """
    error = None
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        if len(email) < 1:
            error = 'You must send us an email.'
        elif len(password) < 5:
            error = 'Your password must be at least 5 characters.'
        elif not user.User(graph=graph, email=email, username=username).register(password):
            error = 'A user with that email already exists.'
        else:
            session['email'] = email
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('register.html', error=error)

@APP.route('/login', methods=['GET', 'POST'])
def login():
    """ login handler """
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not user.User(graph=graph, email=email).verify_password(password):
            if not user.User(graph=graph, username=email).verify_password(password):
                error = 'Invalid login.'
        if error ==  None:
            _user = user.User(graph=graph, email=email).find()
            if _user == None:
                _user = user.User(graph=graph, username=email).find()
            session['email'] = email
            session['username'] = _user['username']
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@APP.route('/logout')
def logout():
    """ logout handler """
    session.pop('email', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@APP.route('/add_language', methods=['POST'])
def add_language():
    """ add language handler """
    _language = request.form['language']
    user.User(graph, session['email']).add_language(language.Language(graph, _language).find())
    return redirect(url_for('profile', username=session['username']))

@APP.route('/add_project', methods=['POST'])
def add_project():
    """ add project handler """
    title = request.form['title']
    tags = request.form['tags']
    repository = request.form['repository']

    if not title:
        abort(400, 'You must give your post a title.')
    if not tags:
        abort(400, 'You must give your post at least one tag.')
    if not repository:
        abort(400, 'You must give your post a repository.')

    user.User(graph, session['email']).add_project(title, tags, repository)
    return redirect(url_for('profile', username=session['username']))

@APP.route('/like_project/<project_id>')
def like_project(project_id):
    """ like project handler """
    email = session.get('email')
    username = session.get('username')
    if not username:
        abort(400, 'You must be logged in to like a project.')
    user.User(graph, email).like_project(project_id)
    return redirect(request.referrer)

@APP.route('/profile/<username>')
def profile(username):
    """ profile handler """
    _user = user.User(graph=graph, username=username)
    curuser = _user.find()
    email = curuser['email']

    all_languages = queries.get_all_languages(graph, email)
    languages = queries.get_users_languages(graph, email)
    projects = queries.get_users_projects(graph, email)

    similar = []
    common = []

    viewer_email = session.get('email')
    if viewer_email:
        viewer = user.User(graph=graph, email=viewer_email)
        if viewer.email == email:
            similar = viewer.get_similar_users()
        else:
            common = viewer.get_commonality_of_user(email)

    return render_template(
        'profile.html',
        email=email,
        username=curuser['username'],
        languages=languages,
        all_languages=all_languages,
        projects=projects,
        similar=similar,
        common=common
    )
