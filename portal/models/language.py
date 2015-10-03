#!/usr/bin/env python
""" language model """

class Language(object):
    """ language object """
    def __init__(self, graph, name):
        self.graph = graph
        self.name = name

    def find(self):
        """ find a language by name """
        language = self.graph.find_one("Language", "name", self.name)
        return language
