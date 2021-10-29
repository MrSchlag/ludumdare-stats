import requests
from datetime import date

max_page_size = 250
event_category = 'jam'

def get_event_node_id(ld_number):
    payload = {'offset': 0, 'limit': max_page_size}
    r = requests.get('https://api.ldjam.com/vx/node/feed/1/all/event/ld', params=payload)
    json = r.json()
    ids = [event['id'] for event in json['feed']]
    r = requests.get('https://api.ldjam.com/vx/node/get/' + "+".join([str(id) for id in ids]))
    json = r.json()
    for event in json['node']:
        if event['slug'] == str(ld_number):
            return event
    raise Exception("LD " + str(ld_number) + " not found")

def get_game_node_ids(min_date):
    date_index = date.max
    offset = 0
    ids = []
    while date_index > min_date:
        payload = {'offset': offset, 'limit': offset + max_page_size}
        r = requests.get('https://api.ldjam.com/vx/node/feed/1/all/item/game', params=payload)
        json = r.json()
        [ids.append(id) for id in [node['id'] for node in json['feed']]]
        dates = [date.fromisoformat(node['modified'][0:10]) for node in json['feed']]
        date_index = min(i for i in dates)
        offset += max_page_size
        print(offset)
    return ids

def game_filter(game, event_id, category):
    return game['parent'] == event_id and game['subsubtype'] == category

def get_games(ids, event_id):
    offset = 0
    games = []
    while offset < len(ids):
        ids_slice = ids[offset:offset + max_page_size]
        request = 'https://api.ldjam.com/vx/node/get/' + "+".join([str(id) for id in ids_slice])
        print(request)
        r = requests.get(request)
        json = r.json()
        [games.append(game) for game in json['node'] if game_filter(game, event_id, event_category)]
        offset += max_page_size
    return games


event = get_event_node_id(49)
print(event)
ids = get_game_node_ids(date.fromisoformat(event['meta']['event-start'][0:10]) )
games = get_games(ids, event['id'])

print(len(games))