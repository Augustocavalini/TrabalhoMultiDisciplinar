import json
import os
import numpy as np

# Carregar o arquivo JSON
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

def generate_normal_value(mean_value):
    lower_bound = mean_value * 0.5  
    upper_bound = mean_value * 1.5  
    std_dev = (upper_bound - lower_bound) / 6  
    
    while True:
        sample = np.random.normal(mean_value, std_dev)
        if lower_bound <= sample <= upper_bound:
            return sample
        
time_table_delays = [10, 12, 15, 17, 18, 20, 23, 25, 30, 35, 37, 40, 40.5, 45, 50, 55, 60, 70]
frequencies_table = [15, 1, 26, 1, 2, 100, 1, 26, 133, 7, 1, 58, 1, 5, 13, 1, 6, 2]

def sample_from_distribution():
    return np.random.choice(time_table_delays, p=np.array(frequencies_table)/sum(frequencies_table))

MAX_BLOCKED_STEPS = generate_normal_value(config["MAX_BLOCKED_STEPS"])
WAITING_TIME_THRESHOLD = generate_normal_value(config["WAITING_TIME_THRESHOLD"])
TRAY_INTERACTION_TIME = generate_normal_value(config["TRAY_INTERACTION_TIME"])
DISTANCE_THRESHOLD = generate_normal_value(config["DISTANCE_THRESHOLD"])
DEFAULT_TRAY_PORTIONS = generate_normal_value(config["DEFAULT_TRAY_PORTIONS"])
TABLE_INTERACTION_TIME = sample_from_distribution()

print("MAX_BLOCKED_STEPS:", MAX_BLOCKED_STEPS)
print("WAITING_TIME_THRESHOLD:", WAITING_TIME_THRESHOLD)
print("TRAY_INTERACTION_TIME:", TRAY_INTERACTION_TIME)
print("DISTANCE_THRESHOLD:", DISTANCE_THRESHOLD)
print("DEFAULT_TRAY_PORTIONS:", DEFAULT_TRAY_PORTIONS)
print("TABLE_INTERACTION_TIME:", TABLE_INTERACTION_TIME)