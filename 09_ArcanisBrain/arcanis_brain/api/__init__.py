from arcanis_brain.api.rest import RestAPI
from arcanis_brain.api.graphql import GraphQLAPI
from arcanis_brain.api.websocket import WebSocketAPI


class APILayer:
    def __init__(self, brain):
        self.brain = brain
        self.rest = RestAPI(brain)
        self.graphql = GraphQLAPI(brain)
        self.websocket = WebSocketAPI(brain)


__all__ = ["APILayer", "RestAPI", "GraphQLAPI", "WebSocketAPI"]
