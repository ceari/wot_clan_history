import datetime
import json
import time

from pymongo import MongoClient
from flask import Flask, make_response, render_template
import flask_restful as restful
from flask_restful import abort

from .config import MONGO_URI

app = Flask(__name__)
api = restful.Api(app)

client = MongoClient(MONGO_URI)
db = client['clan_history']
clans = db['clans']
players = db['players']


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(time.mktime(obj.timetuple()))
        return json.JSONEncoder.default(self, obj)


@api.representation('application/json')
def json_bson(data, code, headers={}):
    resp = make_response(json.dumps(data, cls=JSONEncoder), code)
    resp.headers.extend(headers)
    return resp


class Player(restful.Resource):
    @staticmethod
    def get(player_name):
        return players.find_one({
            'account_name': player_name,
        }) or players.find_one({
            'account_name': {
                '$regex': '^' + player_name + '$',
                '$options': 'i'}
        }) or abort(404)


class Clan(restful.Resource):
    @staticmethod
    def get(clan_id):
        return clans.find_one({
            '_id': clan_id
        }) or abort(404)

class PlayerCount(restful.Resource):
    def get(self):
        return {'count': players.count()}


class ClanCount(restful.Resource):
    def get(self):
        return {'count': clans.count()}


@app.route('/')
def index():
    return render_template('index.html')


api.add_resource(Player, '/player/<string:player_name>')
api.add_resource(Clan, '/clan/<int:clan_id>')
api.add_resource(PlayerCount, '/player/count')
api.add_resource(ClanCount, '/clan/count')
