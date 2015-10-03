#!/usr/bin/env python
""" db queries """

from datetime import datetime

def date():
    """ get formated date """
    return datetime.now().strftime('%F')

def get_all_languages(graph, email):
    """ get all languages of a specific user """
    query = """
    MATCH (language:Language),
          (user:User)
    WHERE NOT (language:Language)<-[:USE]-(user:User)
    AND user.email = {email}
    RETURN language.id as id,
           language.name as name
    """

    return graph.cypher.execute(query, email=email)

def get_last_projects(graph):
    """ get last five projects ordered by date """
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

def get_users(graph):
    """ get last five users ordered by username """
    query = """
    MATCH (user:User)-[:PUBLISHED]->(project:Project)
    RETURN user.username AS username
    ORDER BY username DESC
    LIMIT 5
    """

    return graph.cypher.execute(query, today=date())

def get_project_likes(graph, project):
    """ get project likes of a project """
    query = """
    MATCH (user:User)-[:LIKED]->(project:Project)
    WHERE project.id = {id}
    RETURN count(user) as likes
    """

    return graph.cypher.execute(query, id=project)

def get_users_languages(graph, email):
    """ get languages of a specific user """
    query = """
    MATCH (user:User)-[:USE]->(language)
    WHERE user.email = {email}
    RETURN language.id AS id,
           language.name AS name
    ORDER BY name DESC
    """

    return graph.cypher.execute(query, email=email)

def get_users_projects(graph, email):
    """ get projects of a specific user """
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
    """

    return graph.cypher.execute(query, email=email)
