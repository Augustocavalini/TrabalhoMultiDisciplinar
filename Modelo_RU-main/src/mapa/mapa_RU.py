import json
from enum import Enum
import os

class CellType(Enum):
    STUDENT = 'E'
    TURNSTILE = 'C'
    EMPTY = '0'
    WALL = 'P'
    EMPTY_TRAY = 'B'
    RICE_TRAY = 'B1'
    BROWN_RICE_TRAY = 'B2'
    BEANS_TRAY = 'B3'
    GUARN_TRAY = 'B4'
    VEG_TRAY = 'B5'
    MEAT_TRAY = 'B6'
    SAL_TRAY = 'B7'
    TALHER_TRAY = 'B8'
    EXIT = 'S'
    JUICE = 'A'
    SPICES = 'T'
    DESSERT = 'D'
    TABLE = 'M'

class GridConfig:

    @staticmethod
    def get_grid():
        data = json.load(open(os.path.join(os.path.dirname(__file__), 'grid_config.json')))
        raw_grid = data['grid']
        return [[CellType(cell) for cell in row] for row in raw_grid]
        # retorna o tipo de cada célula do grid
