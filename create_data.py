#!/usr/bin/env python
""" create languages for app """

from py2neo import Graph, Node

languages = [
    "PHP",
    "Python",
    "Ruby",
    "Erlang",
    "Elixir",
    "Haskell",
    "Go",
    "Java",
    "Scala",
    "Groovy",
    "JavaScript",
    "C#",
    "C++",
    "Swift"
]

graph = Graph('http://neo4j:neo4j@127.0.0.1:7474/db/data/')

for i in languages:
    language = graph.find_one("Language", "name", i)
    if None == language:
        lang = Node("Language",
                    name=i)
        graph.create(lang)
