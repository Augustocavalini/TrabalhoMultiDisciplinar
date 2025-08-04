from mesa import Agent
import random
from mapa.paths import PATHS_CATRACAS2, PATHS_END_CONDESERT, PATHS_END_DESSERT, PATHS_TRAY_JUICE, PATHS_TRAY_NO_JUICE, PATHS_END_NOTHING, PATHS_END_COND, COMMON_PATH_CATRACA
from constants import  WAITING_TIME_THRESHOLD
from mapa.mapa_RU import CellType
from mesa.space import MultiGrid
import math as mt
import os
import json
import numpy as np
# from model import 

CATRACA_MAPPING = {1: (18, 2), 2: (18, 4), 3: (99, 2), 4: (99, 4)}

TRAY_TYPES = {'Rice_tray', 'Brown_Rice_Tray', 'Beans_Tray',
              'Guarn_Tray', 'Veg_Tray', 'Meat_Tray', 'Sal_Tray', 'Talher_Tray', 'Juice', 'Dessert', 'Spices', 'Empty_Tray'}

DEFAULT_TRAY_PORTIONS = 5
DEFAULT_TRAY_PORTIONS_STD = 2
DEFAULT_TRAY_PORTIONS_REFILL = 40
DEFAULT_TRAY_PORTIONS_REFILL_STD = 10
TRAY_INTERACTION_TIME = 6
TRAY_INTERACTION_TIME_STD = 2
JUICE_INTERACTION_TIME = 8
JUICE_INTERACTION_TIME_STD = 2
SPICES_INTERACTION_TIME = 4
SPICES_INTERACTION_TIME_STD = 2
DESSERT_INTERACTION_TIME = 2
DESSERT_INTERACTION_TIME_STD = 1


class StaticAgent(Agent):
    def __init__(self, unique_id, model, pos_x, pos_y, agent_type):
        super().__init__(unique_id, model)
        self.x = pos_x
        self.y = pos_y
        self.type = agent_type
        self.food_count = int(max(10, np.random.normal(DEFAULT_TRAY_PORTIONS, DEFAULT_TRAY_PORTIONS_STD)))
        self.content = self._determine_tray_type()
        self.refill_timer = 0
        self.is_refilling = False


    def _determine_tray_type(self):
        if self.type == "EMPTY_TRAY":
            return "EMPTY"
        elif "Tray" in self.type:
            return self.type.split('_')[0]
        else:
            return None

    def step(self):
        if not self.is_refilling:
            if self.food_count > 0:
                return

            elif  self.food_count <= 0:
                self.is_refilling = True
                self.refill_timer = int(max(2, np.random.normal(DEFAULT_TRAY_PORTIONS_REFILL, DEFAULT_TRAY_PORTIONS_REFILL_STD)))

        else:
            if self.refill_timer > 0:
                self.refill_timer -= 1

                print(f"Refilling {self.type} at position {self.x}, {self.y}. Time left: {self.refill_timer} seconds")

            elif self.refill_timer == 0:
                self.is_refilling = False
                self.food_count = int(max(10, np.random.normal(DEFAULT_TRAY_PORTIONS, DEFAULT_TRAY_PORTIONS_STD)))
                print(f"Refilled {self.type} at position {self.x}, {self.y}")

        
class StudentAgent(Agent):
    def __init__(self, unique_id, model, x, y):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.type = "Student"
        self.waiting_time = 0

        self.waiting_time_until_tray = 0
        self.flag_until_tray = True

        self.window_size_count_time = 60 # seconds

        self.blocked_steps = 0
        self.steps_visited = 0
        self.visited_groups = set()
        # self.current_goal = None
        self.current_path = None
        self.interaction_timer = 0
        self.ta_na_mesa = False
        self.interaction_table_timer = -1
        self.tray_interaction_target = None
        self.move_attempts = []
        # self.path_occupancy = {}
        self._initialize_preferences()
        # self.determine_catraca_id()
        self.catraca_id = None

        self.at_rampa_path = False
        self.at_juice_path = False
        self.at_end_path = False
        self.interacted_w_juice = False


        self.terminou_path_local = False
        self.terminou_path = False
        self.at_common_path = True
        
      # Armazena histórico para gráficos-consultar luiz se ocorreu duvida
        self.collected_data = []
        
    def record_data(self):
        """Armazena os dados do agente a cada step para gerar gráficos depois."""
        self.collected_data.append({
            "step": self.model.schedule.time,
            "agent_id": self.unique_id,
            "waiting_time": self.waiting_time,
            "waiting_time_until_tray": self.waiting_time_until_tray,
            "interaction_timer": self.interaction_timer,
            "tray_interaction_target": self.tray_interaction_target,
            "steps_visited": self.steps_visited,
            "blocked_steps": self.blocked_steps,
            "position": self.pos
        })
        
    def escolher_arroz(self):
        opcoes = ["rice", "brown_rice", "no_rice"]
        probabilidades = [0.8625, 0.13, 0.0075]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]

        
    def pega_feijao(self):
        opcoes = [1, 0]
        probabilidades = [0.8953, 0.1047]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]


    def escolher_dieta(self):
        opcoes = ["vegan", "meat_eater", "no_meat_or_veg"]
        probabilidades = [0.05, 0.95, 0]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def pega_salada(self):
        opcoes = [1, 0]
        probabilidades = [0.6428, 0.3572]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def pega_suco(self):
        opcoes = [1, 0]
        probabilidades = [0.5012468828, 0.4987531172]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def pega_sobremesa(self):
        opcoes = [1, 0]
        probabilidades = [0.8447630923, (1-0.8447630923)]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def pega_condimentos(self):
        opcoes = [1, 0]
        probabilidades = [0.6789276808, (0.3210723192)]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def _initialize_preferences(self):
        self.diet = self.escolher_dieta()
        self.rice_type = self.escolher_arroz()
        self.beans = self.pega_feijao()
        self.salad = self.pega_salada()
        self.juice = self.pega_suco()
        self.sobremesa = self.pega_sobremesa()
        self.condimentos = self.pega_condimentos()

        
    # VISTA
    def check_tray_interaction(self):
        x, y = self.pos
        upper_cell = (x, y - 1)
        lower_cell = (x, y + 1)

        upper_tray = self.get_tray(upper_cell)
        lower_tray = self.get_tray(lower_cell)

        tray = upper_tray or lower_tray
        if not tray:
            return

        # Se não há comida ou está em refill, espera até completar
        if tray.food_count <= 0 or tray.is_refilling:
            # debug
            print(f"Student {self.unique_id} waiting: food={tray.food_count},  refilling={tray.is_refilling}, at {self.pos}")
            self.interaction_timer = -100
            return

        # Há comida disponível: consome e inicia interação
        tray.food_count -= 1
        # nunca deixa ficar negativo
        self.set_tray_interaction_target(tray.type)
        if self.flag_until_tray:
            self.flag_until_tray = False
            self.model.waiting_time_until_tray += self.waiting_time_until_tray
            self.model.num_students_1min_window += 1
            self.model.waiting_time_until_tray_total += self.waiting_time_until_tray
            self.model.num_students_after_tray_total += 1

    def check_juice_interaction(self):
        x, y = self.pos

        lower_cell = (x, y + 1)
        left_cell = (x - 1, y)
        right_cell = (x + 1, y)

        left_station = self.get_tray(left_cell, TRAY_TYPES={'Juice'})
        right_station = self.get_tray(right_cell, TRAY_TYPES={'Juice'})
        
        is_lower_cell_final = lower_cell in [path[-1] for path in PATHS_TRAY_JUICE.values()]

        if len(self.model.grid.get_cell_list_contents([lower_cell])) >= 1:
            is_lower_cell_empty = False
        else:
            is_lower_cell_empty = True

        if self.interacted_w_juice:
            return
        
        elif not is_lower_cell_final and is_lower_cell_empty:
            # self.move_to_next_step()
            return
            
        elif is_lower_cell_final:
            print(f"Agent {self.unique_id} is at the final cell of the juice path: {lower_cell}")
            if (left_station or right_station):
                if left_station:
                    self.tray_interaction_target = 'Juice'
                    self.interaction_timer = int(max(3, np.random.normal(JUICE_INTERACTION_TIME, JUICE_INTERACTION_TIME_STD)))
                    # self.juice = 0
                    self.interacted_w_juice = True

                elif right_station:
                    self.tray_interaction_target = 'Juice'
                    self.interaction_timer = int(max(3, np.random.normal(JUICE_INTERACTION_TIME, JUICE_INTERACTION_TIME_STD)))
                    #self.flag_until_tray = False
                    self.interacted_w_juice = True
            else:
                # self.move_to_next_step()
                return

            

        elif  not is_lower_cell_empty:
            if (left_station or right_station):
                print(f"Agent {self.unique_id} is at a cell with juice stations: {lower_cell}")

                if left_station:
                    self.tray_interaction_target = 'Juice'
                    self.interaction_timer = int(max(3, np.random.normal(JUICE_INTERACTION_TIME, JUICE_INTERACTION_TIME_STD)))
                    #self.flag_until_tray = False
                    self.interacted_w_juice = True

                    # if self.model.is_cell_empty(right_cell):

                elif right_station:
                    self.tray_interaction_target = 'Juice'
                    self.interaction_timer = int(max(3, np.random.normal(JUICE_INTERACTION_TIME, JUICE_INTERACTION_TIME_STD)))
                    #self.flag_until_tray = False
                    self.interacted_w_juice = True

                return
            else:
                # self.move_to_next_step()
                return
                
    def check_end_interaction(self):

        if self.sobremesa and not self.condimentos:
            return

        x, y = self.pos

        lower_cell = (x, y + 1)
        left_cell = (x - 1, y)
        right_cell = (x + 1, y)

        left_station = self.get_tray(left_cell, TRAY_TYPES={'Spices'})
        right_station = self.get_tray(right_cell, TRAY_TYPES={'Spices'})
        bottom_station = self.get_tray(lower_cell, TRAY_TYPES={'Dessert'})

        if left_station or right_station:
            self.tray_interaction_target = 'Spices'
            self.interaction_timer = int(max(2, np.random.normal(SPICES_INTERACTION_TIME, SPICES_INTERACTION_TIME_STD)))

        elif bottom_station:
            self.tray_interaction_target = 'Dessert'
            self.interaction_timer = int(max(1, np.random.normal(DESSERT_INTERACTION_TIME, DESSERT_INTERACTION_TIME_STD)))
        else:
            # self.move_to_next_step()
            return



    def get_tray(self, cell, TRAY_TYPES=TRAY_TYPES):
        tray = next((agent for agent in self.model.grid.get_cell_list_contents([cell]) if
                    isinstance(agent, StaticAgent) and agent.type in TRAY_TYPES), None)
        return tray

    # def set_tray_interaction_target(self, tray_type):
    #     if self.rice_type == "brown_rice":
    #         if tray_type == 'Brown_Rice_Tray':
    #             self.tray_interaction_target = 'brown_rice'
    #             self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))

    #     elif self.rice_type == "rice":
    #         if tray_type == 'Rice_Tray':
    #             self.tray_interaction_target = 'Rice_Tray'
    #             self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))
        
    #     elif self.rice_type == "no_rice":
    #         pass

    #     if self.beans:
    #         if tray_type == 'Beans_Tray':
    #             self.tray_interaction_target = 'Beans_Tray'
    #             self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))

    #     if tray_type == 'Guarn_Tray':
    #         self.tray_interaction_target = 'Guarn_Tray'
    #         self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))
        
    #     if self.diet == "vegan":
    #         if tray_type == 'Veg_Tray':
    #             self.tray_interaction_target = 'Veg_Tray'
    #             self.interaction_timer =  int(max(6, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))

    #     elif self.diet == "meat_eater":
    #         if tray_type == 'Meat_Tray':
    #             self.tray_interaction_target = 'Meat_Tray'
    #             self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))



    #     if tray_type != 'Meat_Tray' and tray_type != 'Veg_Tray' and tray_type != 'Rice_Tray' and tray_type != 'Brown_Rice_Tray':
    #         self.tray_interaction_target = tray_type
    #         # print(max(6, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))
    #         self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))
            

    def set_tray_interaction_target(self, tray_type):
        if tray_type == 'Brown_Rice_Tray':
            if self.rice_type == "brown_rice":
                self.tray_interaction_target = 'brown_rice'
                self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME, TRAY_INTERACTION_TIME_STD)))

        elif tray_type == 'Rice_Tray':
            if self.rice_type == "rice":
                self.tray_interaction_target = 'Rice_Tray'
                self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME, TRAY_INTERACTION_TIME_STD)))

        elif tray_type == 'Beans_Tray':
            if self.beans:
                self.tray_interaction_target = 'Beans_Tray'
                self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME, TRAY_INTERACTION_TIME_STD)))

        elif tray_type == 'Guarn_Tray':
            self.tray_interaction_target = 'Guarn_Tray'
            self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME, TRAY_INTERACTION_TIME_STD)))

        elif tray_type == 'Veg_Tray':
            if self.diet == "vegan":
                self.tray_interaction_target = 'Veg_Tray'
                self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME, TRAY_INTERACTION_TIME_STD)))

        elif tray_type == 'Meat_Tray':
            if self.diet == "meat_eater":
                self.tray_interaction_target = 'Meat_Tray'
                self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME, TRAY_INTERACTION_TIME_STD)))

        elif tray_type == 'Sal_Tray':
            if self.salad:
                self.tray_interaction_target = 'Sal_Tray'
                self.interaction_timer = int(max(6, np.random.normal(TRAY_INTERACTION_TIME, TRAY_INTERACTION_TIME_STD)))

        elif tray_type == 'Talher_Tray':
            self.tray_interaction_target = tray_type
            self.interaction_timer = int(2)

                

    def _choose_common_path(self):
        current_path_chosen = COMMON_PATH_CATRACA.get(self.catraca_id, None)
        if not current_path_chosen:
            print(f"Warning: No common path found for catraca_id {self.catraca_id}, {self.pos}.")
            return None
        
        return current_path_chosen


    def _choose_optimal_path(self):
        if self.catraca_id in [1, 2]:  # Lado esquerdo
            path_keys = list(PATHS_CATRACAS2.keys())[0:6]
        elif self.catraca_id in [3, 4]:  # Lado direito
            path_keys = list(PATHS_CATRACAS2.keys())[6:12]
        else:
            print(f"Warning: Invalid catraca_id {self.catraca_id}.")
            return None

        path_occupancy = []

        for key in path_keys:
            path = PATHS_CATRACAS2.get(key, [])
            if not path:
                continue  # Pula paths vazios

            total_positions = len(path)
            occupied_count = 0

            for cell in path:
                agents_in_cell = self.model.grid.get_cell_list_contents([cell])
                occupied_count += len(agents_in_cell)

            relative_occupancy = occupied_count / total_positions
            path_occupancy.append((key, relative_occupancy))

        if not path_occupancy:
            print(f"Warning: No valid paths found for catraca_id {self.catraca_id}.")
            return None

        # Ordena por menor ocupação relativa
        path_occupancy.sort(key=lambda item: item[1])
        best_path_key = path_occupancy[0][0]


        count_path = path_occupancy.count((best_path_key, path_occupancy[0][1]))
        if count_path > 1:
            # If there are multiple paths with the same occupancy, choose one randomly
            best_path_key = random.choice([key for key, occupancy in path_occupancy if occupancy == path_occupancy[0][1]])

        return best_path_key


    def _choose_juice_path(self):
        return "J" + (str(self.current_path)) if self.juice else "NJ" + (str(self.current_path))


    def _choose_end_path(self):
        
        if self.catraca_id in [1, 2]:  # Lado esquerdo
            if self.sobremesa and not self.condimentos:
                path_key = list(PATHS_END_DESSERT.keys())[0]

            elif self.condimentos and not self.sobremesa:
                path_key = list(PATHS_END_COND.keys())[0]

            elif self.sobremesa and self.condimentos:
                path_key = list(PATHS_END_CONDESERT.keys())[0]
                
            else:
                path_key = list(PATHS_END_NOTHING.keys())[0]

        elif self.catraca_id in [3, 4]:  # Lado direito
            if self.sobremesa and not self.condimentos:
                path_key = list(PATHS_END_DESSERT.keys())[1]

            elif self.condimentos and not self.sobremesa:
                path_key = list(PATHS_END_COND.keys())[1]

            elif self.sobremesa and self.condimentos:
                path_key = list(PATHS_END_CONDESERT.keys())[1]
                
            else:
                path_key = list(PATHS_END_NOTHING.keys())[1]

        else:
            print(f"Warning: Invalid catraca_id {self.catraca_id}.")
            return None

        return path_key

    def determine_catraca_id(self):
        for catraca_id, catraca_position in CATRACA_MAPPING.items():
            if self.pos == catraca_position:
                self.catraca_id = catraca_id

    def move_to_next_step(self):
        if self.current_path:
            if self.at_common_path:
                path_coordinates = COMMON_PATH_CATRACA.get(self.catraca_id, [])

            elif self.at_rampa_path:
                path_coordinates = PATHS_CATRACAS2.get(self.current_path, [])

            elif self.at_juice_path:
                if self.juice:
                    path_coordinates = PATHS_TRAY_JUICE.get(self.current_path, [])

                else:
                    path_coordinates = PATHS_TRAY_NO_JUICE.get(self.current_path, [])

            elif self.at_end_path:
                if self.sobremesa and not self.condimentos:
                    path_coordinates = PATHS_END_DESSERT.get(self.current_path, [])

                elif self.condimentos and not self.sobremesa:
                    path_coordinates = PATHS_END_COND.get(self.current_path, [])

                elif self.sobremesa and self.condimentos:
                    path_coordinates = PATHS_END_CONDESERT.get(self.current_path, [])
                    
                else:
                    path_coordinates = PATHS_END_NOTHING.get(self.current_path, [])
            else:
                path_coordinates = []

            if not path_coordinates:
                print(f"Warning: No coordinates found for path {self.current_path}")
                return

            if self.steps_visited < len(path_coordinates):
                next_step = path_coordinates[self.steps_visited]
                x, y = next_step

                next_step_occupied = any(agent.pos == (x, y) for agent in self.model.schedule.agents)

                if not next_step_occupied:
                    if self.blocked_steps % 2 == 0:
                        self.model.grid.move_agent(self, (x, y))
                        self.move_attempts.append({"from": self.pos, "to": (x, y)})
                        self.steps_visited += 1
                        self.blocked_steps = 0
                    else:
                        self.blocked_steps += 1
                else:
                    self.blocked_steps += 1
            else:
                self.terminou_path_local = True
                self.steps_visited = 0
                self.blocked_steps = 0
        else:
            print(f"Agent {self.unique_id} has no current path to follow.")

    def step(self):
        # --- Lógica original ---
        if not self.flag_until_tray and self.window_size_count_time > 0:
            self.window_size_count_time -= 1
            if self.window_size_count_time == 0:
                self.model.num_students_1min_window -= 1
                self.model.waiting_time_until_tray -= self.waiting_time_until_tray

        if not self.current_path:
            self.determine_catraca_id()
            self.current_path = self._choose_common_path()
            self.at_common_path = True
            self.steps_visited = 0
        else:
            if self.terminou_path:
                if self.interaction_table_timer != -1:
                    self.interaction_table_timer -= 1
                    if self.interaction_table_timer == -1:
                        self.model.num_students -= 1
                        self.model.schedule.remove(self)
                        self.model.grid.remove_agent(self)
                else:
                    table = self.find_nearest_free_table()
                    if table:
                        self.teleport_to_table(table)

            elif self.terminou_path_local:
                self.terminou_path_local = False

                if self.at_common_path:
                    self.current_path = self._choose_optimal_path()
                    if not self.current_path:
                        print(f"Agent {self.unique_id} found no valid path to follow.")
                        return
                    self.at_common_path = False
                    self.at_rampa_path = True
                    self.steps_visited = 0

                elif self.at_rampa_path:
                    self.current_path = self._choose_juice_path()
                    if not self.current_path:
                        print(f"Agent {self.unique_id} found no valid path to follow.")
                        return
                    self.at_rampa_path = False
                    self.at_juice_path = True
                    self.steps_visited = 0
                
                elif self.at_juice_path:
                    self.current_path = self._choose_end_path()
                    if not self.current_path:
                        print(f"Agent {self.unique_id} found no valid path to follow.")
                        return
                    self.at_juice_path = False
                    self.at_end_path = True
                    self.steps_visited = 0

                else:
                    self.terminou_path = True

            elif self.interaction_timer == 0:
                if self.flag_until_tray:
                    self.waiting_time_until_tray += 1
                if self.at_rampa_path and self.blocked_steps == 0:
                    self.check_tray_interaction()
                elif self.at_juice_path and self.blocked_steps == 0:
                    self.check_juice_interaction()
                elif self.at_end_path and self.blocked_steps == 0:
                    self.check_end_interaction()
                    
                if self.interaction_timer == 0:
                    self.move_to_next_step()
                    
            elif self.interaction_timer > 0:
                self.interaction_timer -= 1
                self.waiting_time += 1
                
                if self.interaction_timer == 0:
                    self.move_to_next_step()

            elif self.interaction_timer == -100:
                if self.at_rampa_path:
                    self.check_tray_interaction()

        # --- COLETA DE DADOS ---
        self.record_data()

    def find_nearest_free_table(self):
        tables = self.model.get_free_tables(self.pos)
        if tables:
            chossen_table = random.choice(tables)
            if chossen_table:
                self.set_table_interaction_target(chossen_table)
                return chossen_table

   
    # with open(os.path.join(os.path.dirname(__file__), '..', 'config.json'), 'r') as f:
    #     config = json.load(f)

    def set_table_interaction_target(self, table):
        time_table_delays = [60*10, 60*12, 60*15, 60*17, 60*18, 60*20, 60*23, 60*25, 60*30, 60*35, 60*37, 60*40, 60*40.5, 60*45, 60*50, 60*55, 60*60, 60*70]
        frequencies_table = [15, 1, 26, 1, 2, 100, 1, 26, 133, 7, 1, 58, 1, 5, 13, 1, 6, 2]
        x = np.random.choice(time_table_delays, p=np.array(frequencies_table)/sum(frequencies_table))
        self.table_interaction_target = table
        self.interaction_table_timer = x

    def teleport_to_table(self, table):
        x, y = self.pos

        possible_moves = [(table[0] + dx, table[1]) for dx in [-1, 1]]

        for move in possible_moves:
            if self.model.is_cell_empty(move, self.pos):
                self.model.grid.move_agent(self, move)
                self.ta_na_mesa = True
                return

        new_table = self.find_nearest_free_table()
        if new_table:
            self.teleport_to_table(self, new_table)

    def calculate_distance(self, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        return mt.floor(mt.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2))

class MovementUtils:
    def __init__(self, model):
        self.model = model

    @staticmethod
    def valid_moves(agent, goal):
        x, y = agent.pos
        possible_steps = [(x + dx, y + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                          if 0 <= x + dx < agent.model.grid.width and 0 <= y + dy < agent.model.grid.height
                          and not agent.model.grid.is_cell_occupied((x + dx, y + dy))]

        return possible_steps