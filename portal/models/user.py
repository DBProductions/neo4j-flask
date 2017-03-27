#!/usr/bin/env python
""" user model """

import uuid
from datetime import datetime
from passlib.hash import bcrypt
from py2neo import Node, Relationship

def timestamp():
    """ create a timestamp """
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    """ get formated date """
    return datetime.now().strftime('%F')

class User(object):
    """ user object """
    def __init__(self, graph, email=None, username=None):
        """ set values """
        self.graph = graph
        self.email = email
        self.username = username

    def find(self):
        """ find a user by email or username """
        user = None
        if self.email != None:
            user = self.graph.find_one("User", "email", self.email)
            if user:
                self.username = user['username']
        elif self.username != None:
            user = self.graph.find_one("User", "username", self.username)
            if user:
                self.email = user['email']
        return user

    def register(self, password):
        """ register a new user if not exists """
        if not self.find():
            user = Node("User",
                        email=self.email,
                        username=self.username,
                        password=bcrypt.encrypt(password))
            self.graph.create(user)
            return True
        else:
            return False

    def verify_password(self, password):
        """ return if password is right """
        user = self.find()
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False

    def add_language(self, language):
        """ create relationship between user and language """
        user = self.find()
        rel = Relationship(user, "USE", language)
        self.graph.create(rel)

    def add_project(self, title, tags, repository):
        """ create project and create relationship between user and project """
        user = self.find()
        project = Node(
            "Project",
            id=str(uuid.uuid4()),
            title=title,
            repository=repository,
            timestamp=timestamp(),
            date=date()
        )
        rel = Relationship(user, "PUBLISHED", project)
        self.graph.create(rel)

        tags = [x.strip() for x in tags.lower().split(',')]
        for _tag in set(tags):
            tag = self.graph.merge_one("Tag", "name", _tag)
            rel = Relationship(tag, "TAGGED", project)
            self.graph.create(rel)

    def like_project(self, project_id):
        """ create relationship between user and project """
        user = self.find()
        project = self.graph.find_one("Project", "id", project_id)
        self.graph.create_unique(Relationship(user, "LIKED", project))

    def get_similar_users(self):
        """Find three users who are most similar to the logged-in user
        based on tags they've both blogged about."""
        query = """
        MATCH (you:User)-[:PUBLISHED]->(:Project)<-[:TAGGED]-(tag:Tag),
              (they:User)-[:PUBLISHED]->(:Project)<-[:TAGGED]-(tag)
        WHERE you.email = {email} AND you <> they
        WITH they, COLLECT(DISTINCT tag.name) AS tags, COUNT(DISTINCT tag) AS len
        ORDER BY len DESC LIMIT 3
        RETURN they.username AS similar_user, tags
        """

        return self.graph.cypher.execute(query, email=self.email)

    def get_similar_users_lang(self):
        """Find three users who are most similar to the logged-in user
        based on languages they've both use."""
        query = """
        MATCH (you:User)-[:USE]->(l:Language)<-[:USE]-(u:User)
        WHERE you.email = {email} AND you <> u
        WITH u, COLLECT(l.name) as langs
        RETURN u.username AS similar_user, langs
        """

        return self.graph.cypher.execute(query, email=self.email)

    def get_commonality_of_user(self, email):
        """Find how many of the logged-in user's posts the other user
        has liked and which tags they've both blogged about. """
        query = """
        MATCH (they:User {email:{they}}),
              (you:User {email:{you}})
        OPTIONAL MATCH (they)-[:LIKED]->(project:Project)<-[:PUBLISHED]-(you)
        OPTIONAL MATCH (they)-[:PUBLISHED]->(:Project)<-[:TAGGED]-(tag:Tag),
                       (you)-[:PUBLISHED]->(:Project)<-[:TAGGED]-(tag)
        RETURN COUNT(DISTINCT project) AS likes, COLLECT(DISTINCT tag.name) AS tags
        """

        return self.graph.cypher.execute(query, they=email, you=self.email)[0]
