import json
import numpy as np
import os

# with open('config.json', 'r') as f:
#     config = json.load(f)
# config = json.load(open(os.path.join(os.path.dirname(__file__), '..\config.json')))

with open(os.path.join(os.path.dirname(__file__), '..', 'config.json'), 'r') as f:
    config = json.load(f)
      
MAX_BLOCKED_STEPS = config["MAX_BLOCKED_STEPS"]
WAITING_TIME_THRESHOLD = config["WAITING_TIME_THRESHOLD"]
TRAY_INTERACTION_TIME =config["TRAY_INTERACTION_TIME"]
DISTANCE_THRESHOLD = config["DISTANCE_THRESHOLD"]
DEFAULT_TRAY_PORTIONS = config["DEFAULT_TRAY_PORTIONS"]
TABLE_INTERACTION_TIME = config['TABLE_INTERACTION_TIME']