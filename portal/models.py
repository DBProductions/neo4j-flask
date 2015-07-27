#!/usr/bin/env python
import os
import uuid
from datetime import datetime
from passlib.hash import bcrypt
from py2neo import Graph, Node, Relationship, authenticate

graph = Graph('http://192.168.10.5:7474/db/data/')

def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%F')

def get_all_languages(email):
    query = """
    MATCH (language:Languages),
          (user:User)
    WHERE NOT (language:Languages)<-[:USE]-(user:User) 
    AND user.email = {email}
    RETURN language.id as id,
           language.name as name    
    """

    return graph.cypher.execute(query, email=email)

def get_last_projects():
    query = """
    MATCH (project:Project {date: {today}}),
          (user:User)-[:PUBLISHED]->(project),
          (tag:Tag)-[:TAGGED]->(project)
    RETURN user.username AS username,
           project.id AS id,
           project.date AS date,
           project.timestamp AS timestamp,
           project.title AS title,
           project.repository AS repository,
           COLLECT(tag.name) AS tags
    ORDER BY timestamp DESC
    LIMIT 5
    """

    return graph.cypher.execute(query, today=date())

def get_users():
    query = """
    MATCH (user:User)-[:PUBLISHED]->(project:Project)
    RETURN user.username AS username
    ORDER BY username DESC
    LIMIT 5
    """

    return graph.cypher.execute(query, today=date())

def get_project_likes(project):
    query = """
    MATCH (user:User)-[:LIKED]->(project:Project)
    WHERE project.id = {id}
    RETURN count(user) as likes
    """

    return graph.cypher.execute(query, id=project)

def get_users_languages(email):
    query = """
    MATCH (user:User)-[:USE]->(language)
    WHERE user.email = {email}
    RETURN language.id AS id,
           language.name AS name
    ORDER BY name DESC
    """

    return graph.cypher.execute(query, email=email)


def get_users_projects(email):
    query = """
    MATCH (user:User)-[:PUBLISHED]->(project:Project),
          (tag:Tag)-[:TAGGED]->(project)
    WHERE user.email = {email}
    RETURN project.id AS id,
           project.date AS date,
           project.timestamp AS timestamp,
           project.title AS title,
           project.repository AS repository,
           COLLECT(tag.name) AS tags
    ORDER BY timestamp DESC
    LIMIT 5
    """

    return graph.cypher.execute(query, email=email)

class Language:
    def __init__(self, name):
        self.name = name

    def find(self):
        language = graph.find_one("Languages", "name", self.name)
        return language

class User:
    def __init__(self, email=None, username=None):
        self.email = email
        self.username = username

    def find(self):
        user = None
        if self.email:
            user = graph.find_one("User", "email", self.email)
            #self.username = user['username']
        elif self.username:
            user = graph.find_one("User", "username", self.username)
            self.email = user['email']
        return user

    def register(self, password):
        if not self.find():
            user = Node("User", email=self.email, username=self.username, password=bcrypt.encrypt(password))
            graph.create(user)
            return True
        else:
            return False

    def verify_password(self, password):
        user = self.find()
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False

    def add_language(self, language):
        user = self.find()
        rel = Relationship(user, "USE", language)
        graph.create(rel)

    def add_project(self, title, tags, repository):
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
        graph.create(rel)

        tags = [x.strip() for x in tags.lower().split(',')]
        for t in set(tags):
            tag = graph.merge_one("Tag", "name", t)
            rel = Relationship(tag, "TAGGED", project)
            graph.create(rel)

    def like_project(self, project_id):
        user = self.find()
        project = graph.find_one("Project", "id", project_id)
        graph.create_unique(Relationship(user, "LIKED", project))

    def get_similar_users(self):
        # Find three users who are most similar to the logged-in user
        # based on tags they've both blogged about.
        query = """
        MATCH (you:User)-[:PUBLISHED]->(:Project)<-[:TAGGED]-(tag:Tag),
              (they:User)-[:PUBLISHED]->(:Project)<-[:TAGGED]-(tag)
        WHERE you.email = {email} AND you <> they
        WITH they, COLLECT(DISTINCT tag.name) AS tags, COUNT(DISTINCT tag) AS len
        ORDER BY len DESC LIMIT 3
        RETURN they.username AS similar_user, tags
        """

        return graph.cypher.execute(query, email=self.email)

    def get_commonality_of_user(self, email):
        # Find how many of the logged-in user's posts the other user
        # has liked and which tags they've both blogged about.
        query = """
        MATCH (they:User {email:{they}}),
              (you:User {email:{you}})
        OPTIONAL MATCH (they)-[:LIKED]->(project:Project)<-[:PUBLISHED]-(you)
        OPTIONAL MATCH (they)-[:PUBLISHED]->(:Project)<-[:TAGGED]-(tag:Tag),
                       (you)-[:PUBLISHED]->(:Project)<-[:TAGGED]-(tag)
        RETURN COUNT(DISTINCT project) AS likes, COLLECT(DISTINCT tag.name) AS tags
        """

        return graph.cypher.execute(query, they=email, you=self.email)[0]


