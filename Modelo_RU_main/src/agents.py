
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
              'Guarn_Tray', 'Veg_Tray', 'Meat_Tray', 'Sal_Tray', 'Talher_Tray'}

DEFAULT_TRAY_PORTIONS = 100
DEFAULT_TRAY_PORTIONS_STD = 15
TRAY_INTERACTION_TIME = 6
TRAY_INTERACTION_TIME_STD = 2
JUICE_INTERACTION_TIME = 8
JUICE_INTERACTION_TIME_STD = 2


class StaticAgent(Agent):
    def __init__(self, unique_id, model, pos_x, pos_y, agent_type):
        super().__init__(unique_id, model)
        self.x = pos_x
        self.y = pos_y
        self.type = agent_type
        self.content = self._determine_content()

    def _determine_content(self):
        if self.type == "EMPTY_TRAY":
            return "EMPTY"
        elif "Tray" in self.type:
            self.food_count = max(85, np.random.normal(DEFAULT_TRAY_PORTIONS, DEFAULT_TRAY_PORTIONS_STD))
            return self.type.split('_')[0]
        else:
            return None

    def refill(self):
        if "Tray" in self.type:
            self.food_count = max(85, np.random.normal(DEFAULT_TRAY_PORTIONS, DEFAULT_TRAY_PORTIONS_STD))
            print(f"Refilled {self.type} at position {self.x}, {self.y}")

class StudentAgent(Agent):
    def __init__(self, unique_id, model, x, y):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.type = "Student"
        self.waiting_time = 0

        self.waiting_time_until_tray = 0
        self.flag_until_tray = True

        self.blocked_steps = 0
        self.steps_visited = 0
        self.visited_groups = set()
        self.current_goal = None
        self.current_path = None
        self.interaction_timer = 0
        self.ta_na_mesa = False
        self.interaction_table_timer = -1
        self.tray_interaction_target = None
        self.move_attempts = []
        self.path_occupancy = {}
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
        
    def escolher_arroz(self):
        opcoes = ["rice", "brown_rice", "no_rice"]
        probabilidades = [0.8625, 0.13, 0.0075]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]

    def escolher_dieta(self):
        opcoes = ["vegan", "meat_eater", "no_meat_or_veg"]
        probabilidades = [0.05, 0.95, 0]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def escolher_suco(self):
        opcoes = [1, 0]
        probabilidades = [0.5012468828, 0.4987531172]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def escolher_sobremesa(self):
        opcoes = [1, 0]
        probabilidades = [0.8447630923, (1-0.8447630923)]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def escolher_condimentos(self):
        opcoes = [1, 0]
        probabilidades = [0.6789276808, (0.3210723192)]
        return random.choices(opcoes, weights=probabilidades, k=1)[0]
    
    def _initialize_preferences(self):
        self.diet = self.escolher_dieta()
        self.rice_type = self.escolher_arroz()
        self.juice = self.escolher_suco()
        self.sobremesa = self.escolher_sobremesa()
        self.condimentos = self.escolher_condimentos()

        
    # VISTA
    def check_tray_interaction(self):
        
        x, y = self.pos
        upper_cell = (x, y - 1)
        lower_cell = (x, y + 1)

        upper_tray = self.check_tray_type(upper_cell)
        lower_tray = self.check_tray_type(lower_cell)

        if upper_tray:
            self.set_tray_interaction_target(upper_tray)
            self.flag_until_tray = False
        elif lower_tray:
            self.set_tray_interaction_target(lower_tray)
            self.flag_until_tray = False
        else:
            self.move_to_next_step()

    def check_juice_interaction(self):
        x, y = self.pos

        lower_cell = (x, y + 1)
        left_cell = (x - 1, y)
        right_cell = (x + 1, y)

        left_station = self.check_tray_type(left_cell, TRAY_TYPES={'Juice'})
        right_station = self.check_tray_type(right_cell, TRAY_TYPES={'Juice'})
        
        is_lower_cell_final = lower_cell in [path[-1] for path in PATHS_TRAY_JUICE.values()]
        is_lower_cell_empty = len(self.model.grid.get_cell_list_contents([lower_cell])) == 0

        if self.interacted_w_juice:
            return
        
        elif not is_lower_cell_final and is_lower_cell_empty:
            self.move_to_next_step()
            
        elif is_lower_cell_final:
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
                self.move_to_next_step()

            

        elif is_lower_cell_empty > 0:
            if (left_station or right_station):

                current_juice_path = self.current_path
                no_juice_path = 'N' + current_juice_path
                nj_path_coords = PATHS_TRAY_NO_JUICE.get(no_juice_path, [])
                # Procura o primeiro ponto livre no path de no juice a direita ou a esquerda

                if left_station:
                    self.tray_interaction_target = 'Juice'
                    self.interaction_timer = int(max(3, np.random.normal(JUICE_INTERACTION_TIME, JUICE_INTERACTION_TIME_STD)))
                    #self.flag_until_tray = False
                    self.interacted_w_juice = True

                    # if self.model.is_cell_empty(right_cell):
                    self.model.grid.move_agent(self, right_cell)
                    self.pos = right_cell
                    self.current_path = no_juice_path
                    self.steps_visited = nj_path_coords.index(right_cell) + 1

                elif right_station:
                    self.tray_interaction_target = 'Juice'
                    self.interaction_timer = int(max(3, np.random.normal(JUICE_INTERACTION_TIME, JUICE_INTERACTION_TIME_STD)))
                    #self.flag_until_tray = False
                    self.interacted_w_juice = True

                    # if self.model.is_cell_empty(left_cell):
                    self.pos = left_cell
                    self.current_path = no_juice_path
                    self.steps_visited = nj_path_coords.index(left_cell) + 1

                return
            else:
                self.move_to_next_step()
                



    def check_tray_type(self, cell, TRAY_TYPES=TRAY_TYPES):
        tray = next((agent for agent in self.model.grid.get_cell_list_contents([cell]) if
                    isinstance(agent, StaticAgent) and agent.type in TRAY_TYPES), None)
        return tray.type if tray else None

    def set_tray_interaction_target(self, tray_type):
        if self.diet == "vegan":
            if tray_type == 'Veg_Tray':
                self.tray_interaction_target = 'Veg_Tray'
                self.interaction_timer =  int(max(10, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))

        elif self.diet == "meat_eater":
            if tray_type == 'Meat_Tray':
                self.tray_interaction_target = 'Meat_Tray'
                self.interaction_timer = int(max(10, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))

        else:
            self.tray_interaction_target = 'Sal_Tray'

        if self.rice_type == "brown_rice":
            if tray_type == 'Brown_Rice_Tray':
                self.tray_interaction_target = 'brown_rice'
                self.interaction_timer = int(max(10, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))
        elif self.rice_type == "rice":
            if tray_type == 'Rice_Tray':
                self.tray_interaction_target = 'Rice_Tray'
                self.interaction_timer = int(max(10, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))
        else:
            self.tray_interaction_target = 'Beans_Tray'

        if tray_type != 'Meat_Tray' and tray_type != 'Veg_Tray' and tray_type != 'Rice_Tray' and tray_type != 'Brown_Rice_Tray':
            self.tray_interaction_target = tray_type
            # print(max(10, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))
            self.interaction_timer = int(max(10, np.random.normal(TRAY_INTERACTION_TIME,TRAY_INTERACTION_TIME_STD)))
            
                

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

        print(path_occupancy)

        count_path = path_occupancy.count((best_path_key, path_occupancy[0][1]))
        if count_path > 1:
            print("Warning: Multiple paths with the same occupancy found.")
            # If there are multiple paths with the same occupancy, choose one randomly
            best_path_key = random.choice([key for key, occupancy in path_occupancy if occupancy == path_occupancy[0][1]])

        print(f"Agent {self.unique_id} escolheu path '{best_path_key}' com ocupação relativa {path_occupancy[0][1]:.2f}")
        return best_path_key


    def _choose_juice_path(self):

        # if self.juice:
        #     if self.catraca_id in [1, 2]:  # Lado esquerdo
        #         path_keys = list(PATHS_TRAY_JUICE.keys())[0:6]
        #     elif self.catraca_id in [3, 4]:  # Lado direito
        #         path_keys = list(PATHS_CATRACAS2.keys())[6:12]
        #     else:
        #         print(f"Warning: Invalid catraca_id {self.catraca_id}.")
        #         return None
        # else:
        #     if self.catraca_id in [1, 2]:  # Lado esquerdo
        #         path_keys = list(PATHS_TRAY_NO_JUICE.keys())[0:6]
        #     elif self.catraca_id in [3, 4]:  # Lado direito
        #         path_keys = list(PATHS_TRAY_NO_JUICE.keys())[6:12]
        #     else:
        #         print(f"Warning: Invalid catraca_id {self.catraca_id}.")
        #         return None

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


    # VISTA 
    # def _choose_empty_path(self):
    #     self.update_path_occupancy()

    #     catraca_id_str = str(self.catraca_id)
    #     valid_paths = [path for path in self.path_occupancy.keys() if str(path).startswith(catraca_id_str)]
        
    #     if not valid_paths:
    #         print('Student found no valid path! FIX THIS URGENT')
    #         return None
        
    #     min_occupancy = min(self.path_occupancy[path] for path in valid_paths)
    #     least_occupied_paths = [
    #         path for path in valid_paths if self.path_occupancy[path] == min_occupancy]

    #     if len(least_occupied_paths) == len(valid_paths):
    #         return random.choice(least_occupied_paths)

    #     return random.choice(least_occupied_paths)

    # # VISTA
    # def update_path_occupancy(self):
    #     self.path_occupancy = {}
    #     for path_name in COMMOM_PATH_CATRACA.keys():
    #         occupancy = len([agent for agent in self.model.schedule.agents if isinstance(
    #             agent, StudentAgent) and agent.current_path == path_name])
    #         self.path_occupancy[path_name] = occupancy

    # VISTA
    def determine_catraca_id(self):
        for catraca_id, catraca_position in CATRACA_MAPPING.items():
            if self.pos == catraca_position:
                self.catraca_id = catraca_id
                

    # VISTA
    # def move_to_next_step(self):
        
    #     if self.current_path:
    #         if self.at_common_path:
    #             path_coordinates = COMMOM_PATH_CATRACA.get(self.catraca_id, None)
                
    #             print(f"Agent {self.unique_id} is at common path {self.current_path} with coordinates {path_coordinates}")

    #             if not path_coordinates:
    #                 print(f"Warning: No common path found for catraca_id {self.catraca_id}, {self.pos}.")
    #                 return

    #             if not path_coordinates:
    #                 print(f"Warning: No common path found for catraca_id {self.catraca_id}.")

    #         else:
    #             path_coordinates = PATHS_CATRACAS2.get(self.current_path, [])

    #         if path_coordinates:
    #             if len(path_coordinates) > self.steps_visited:
    #                 next_step = path_coordinates[self.steps_visited]
    #                 x, y = next_step

    #                 next_step_occupied = any(agent.pos == (x, y) for agent in self.model.schedule.agents)
                    
    #                 if not next_step_occupied:
    #                     # Check if it's time to move (every 3 seconds)
    #                     if self.blocked_steps % 3 == 0:
    #                         self.model.grid.move_agent(self, (x, y))
    #                         self.move_attempts.append({
    #                             "from": self.pos,
    #                             "to": (x, y),
    #                         })
    #                         print(f"Agent {self.unique_id} moved to {x, y} after three attempts.")
                            
    #                         self.steps_visited += 1
    #                         self.blocked_steps = 0
    #                     else:
    #                         self.blocked_steps += 1 
                            
    #                 else:
    #                     if self.pos == (99, 2):
    #                             print(f'\n  ESTUDANTE PRESO na posição {x,y} com path {self.current_path} e com nextstep {next_step}\n')
    #                     self.blocked_steps += 1
    #             else:
    #                 print(f"Agent {self.unique_id} has reached the end of path {self.current_path}")
    #                 self.terminou_path_local = True
    #                 self.steps_visited = 0
    #                 self.blocked_steps = 0
    #                     # self.current_path = None
    #                 # quando chegar ao final do último path do modelo:
    #                 # self.terminou_path = True
    #         else:
    #             print(f"Agent {self.unique_id} has no more steps to follow in path {self.current_path}")
        
    #     else:
    #         print(f"Agent {self.unique_id} has no current path to follow.")

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

            if not path_coordinates:
                print(f"Warning: No coordinates found for path {self.current_path}")
                return

            if self.steps_visited < len(path_coordinates):
                next_step = path_coordinates[self.steps_visited]
                x, y = next_step

                next_step_occupied = any(agent.pos == (x, y) for agent in self.model.schedule.agents)

                if not next_step_occupied:
                    if self.blocked_steps % 1 == 0:
                        self.model.grid.move_agent(self, (x, y))
                        self.move_attempts.append({"from": self.pos, "to": (x, y)})
                        self.steps_visited += 1
                        self.blocked_steps = 0
                    else:
                        self.blocked_steps += 1
                else:
                    self.blocked_steps += 1
            else:
                print(f"Agent {self.unique_id} has reached the end of path {self.current_path}")
                self.terminou_path_local = True
                self.steps_visited = 0
                self.blocked_steps = 0
        else:
            print(f"Agent {self.unique_id} has no current path to follow.")



    # def step(self):
    #     if not self.current_path:
    #         self.determine_catraca_id()
    #         # self.current_path = self._choose_empty_path()
    #         self.current_path = self._choose_common_path()
    #         print(f"Agent {self.unique_id} chose path {self.current_path} at position {self.pos}")
    #     else:
    #         if self.terminou_path:
    #             if self.interaction_table_timer != -1:
    #                 self.interaction_table_timer -= 1
    #                 if self.interaction_table_timer == -1:
    #                     self.model.num_students -= 1
    #                     self.model.schedule.remove(self)
    #                     self.model.grid.remove_agent(self)
    #             else:
    #                 table = self.find_nearest_free_table()
    #                 if table:
    #                     self.model.waiting_time_until_tray_total += self.waiting_time_until_tray
    #                     self.teleport_to_table(table)

    #         elif self.terminou_path_local:
    #             # escolher o novo path local
    #             self.terminou_path_local = False
  
    #             if self.at_common_path:
    #                 self.current_path = self._choose_optimal_path()
  
    #                 # self.current_path = self._choose_empty_path()
  
    #                 if not self.current_path:
    #                     print(f"Agent {self.unique_id} found no valid path to follow.")
    #                     return
                        

    #                 self.at_common_path = False
            
    #         elif self.interaction_timer > 0:
    #             self.interaction_timer -= 1
    #             self.waiting_time += 1
            
    #         elif self.interaction_timer == 0:
    #             print(f"Agent {self.unique_id} has interaction timer at 0, checking tray interaction.")
    #             self.waiting_time += 1

    #             if self.flag_until_tray:
    #                 self.waiting_time_until_tray += 1

    #             self.check_tray_interaction()
    #             print(f"Agent {self.unique_id} ENTRARA NA FUNÇÃO MOVE TO NEXT STEP")
    #             self.move_to_next_step()
    def step(self):
        if not self.current_path:
            self.determine_catraca_id()
            self.current_path = self._choose_common_path()
            self.at_common_path = True
            self.steps_visited = 0
            print(f"Agent {self.unique_id} chose common path {self.current_path} at position {self.pos}")
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
                        self.model.waiting_time_until_tray_total += self.waiting_time_until_tray
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
                    self.steps_visited = 0  # Reset aqui!

                elif self.at_rampa_path:
                    self.current_path = self._choose_juice_path()
                    if not self.current_path:
                        print(f"Agent {self.unique_id} found no valid path to follow.")
                        return
                    self.at_rampa_path = False
                    self.at_juice_path = True
                    self.steps_visited = 0  # Reset aqui!
                
                elif self.at_juice_path:
                    self.current_path = self._choose_end_path()
                    if not self.current_path:
                        print(f"Agent {self.unique_id} found no valid path to follow.")
                        return
                    self.at_juice_path = False
                    self.at_end_path = True
                    self.steps_visited = 0  # Reset aqui!

                else:
                    self.terminou_path = True  # sinaliza fim do movimento no segundo path


            elif self.interaction_timer > 0:
                self.interaction_timer -= 1
                self.waiting_time += 1

            elif self.interaction_timer == 0:
                if self.flag_until_tray:
                    self.waiting_time_until_tray += 1
                if self.at_rampa_path:
                    self.check_tray_interaction()
                elif self.at_juice_path:
                    self.check_juice_interaction()
                # elif self.at_end_path:
                #     self.check_end_interaction()
                self.move_to_next_step()



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