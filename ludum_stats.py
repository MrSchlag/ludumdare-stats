from matplotlib import colors
import requests
from datetime import date
import numpy as np
import matplotlib.pyplot as plt

max_page_size = 250
event_category = 'jam'
grade_category = 'grade-01-average'

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
    while date_index > min_date: #and offset < 250:
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
    return game['parent'] == event_id and game['subsubtype'] == category and 'grade' in game['magic'] and game['magic']['grade'] >= 20 and grade_category in game['magic'] and 'given' in game['magic']

def get_games(ids, event_id):
    offset = 0
    games = []
    while offset < len(ids):
        ids_slice = ids[offset:offset + max_page_size]
        r = requests.get('https://api.ldjam.com/vx/node/get/' + "+".join([str(id) for id in ids_slice]))
        json = r.json()
        [games.append(game) for game in json['node'] if game_filter(game, event_id, event_category)]
        offset += max_page_size
        print(offset)
    return games

def select_average_grade(grade_name, games):
    return [game['magic'][grade_name] for game in games if grade_name in game['magic']]

def is_game_in_slice(bins, n_bins, i, game):
    if i + 1 < n_bins:
        return game['magic'][grade_category] >= bins[i] and game['magic'][grade_category] < bins[i + 1]
    return game['magic'][grade_category] >= bins[i]


def get_average_grade_slices(games, bins):
    i = 0
    n_bins = len(bins)
    slices = []
    slices_given = []
    slices_stdev = []
    grade_slice_raw = []
    while i < n_bins:
        slice = [game for game in games if is_game_in_slice(bins, n_bins, i, game)]
        grades = [game['magic']['grade'] for game in slice]
        given = [game['magic']['given'] for game in slice]
        
        grade_slice_raw.append(grades)
        slices.append(np.mean(grades))
        slices_stdev.append(np.std(grades))
        slices_given.append(np.mean(given))
        
        i += 1
    return slices, slices_stdev, grade_slice_raw, slices_given

def create_plots(games):
    n_bins = 16
    fig, axs = plt.subplots()

    n, bins, patches = axs.hist(np.array(select_average_grade(grade_category, games)), bins=n_bins)
    average_grades_slices, average_grades_slices_std, grade_slice_raw, slices_given = get_average_grade_slices(games, bins)
    
    axs.plot(bins, average_grades_slices, label='avg grade')
    given_avg_lines = axs.plot(bins, slices_given, label='avg given')
    axs.plot(bins, average_grades_slices_std, '--', label='stdev grade')
    bplot = axs.boxplot(grade_slice_raw, positions=bins, widths=0.05, manage_ticks=False, patch_artist=True)
    for patch in bplot['boxes']:
        patch.set_facecolor('lightgreen')

    [line.set_color('cyan') for line in given_avg_lines]
    #axs.tick_params(bottom=False)
    #axs[2].hist(np.array(select_average_grade('grade-03-average', games)), bins=n_bins, density=True)
    #axs[3].hist(np.array(select_average_grade('grade-04-average', games)), bins=n_bins, density=True)
    #axs[4].hist(np.array(select_average_grade('grade-05-average', games)), bins=n_bins, density=True)
    #axs[5].hist(np.array(select_average_grade('grade-06-average', games)), bins=n_bins, density=True)
    #axs[6].hist(np.array(select_average_grade('grade-07-average', games)), bins=n_bins, density=True)
    #axs[7].hist(np.array(select_average_grade('grade-08-average', games)), bins=n_bins, density=True)
    axs.legend()
    plt.show()

#create_plots(10)
print("get event...")
event = get_event_node_id(49)
print("get nodes...")
ids = get_game_node_ids(date.fromisoformat(event['meta']['event-start'][0:10]))
print("get games...")
games = get_games(ids, event['id'])
create_plots(games)
print(len(games))