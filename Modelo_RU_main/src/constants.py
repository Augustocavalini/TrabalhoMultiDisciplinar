import json
import numpy as np
import os

# with open('config.json', 'r') as f:
#     config = json.load(f)
with open(os.path.join(os.path.dirname(__file__), '..', 'config.json'), 'r') as f:
    config = json.load(f)

time_table_delays = [60*10, 60*12, 60*15, 60*17, 60*18, 60*20, 60*23, 60*25, 60*30, 60*35, 60*37, 60*40, 60*40.5, 60*45, 60*50, 60*55, 60*60, 60*70]
frequencies_table = [15, 1, 26, 1, 2, 100, 1, 26, 133, 7, 1, 58, 1, 5, 13, 1, 6, 2]

def sample_from_distribution():
    return np.random.choice(time_table_delays, p=np.array(frequencies_table)/sum(frequencies_table))


WAITING_TIME_THRESHOLD = config["WAITING_TIME_THRESHOLD"]
MAX_BLOCKED_STEPS = config["MAX_BLOCKED_STEPS"]
TRAY_INTERACTION_TIME = max(10, np.random.normal(config["TRAY_INTERACTION_TIME"], config["TRAY_INTERACTION_TIME_STD"]))
DISTANCE_THRESHOLD = config["DISTANCE_THRESHOLD"]
DEFAULT_TRAY_PORTIONS = max(85, np.random.normal(config["DEFAULT_TRAY_PORTIONS"], config["DEFAULT_TRAY_PORTIONS_STD"]))
TABLE_INTERACTION_TIME = sample_from_distribution()