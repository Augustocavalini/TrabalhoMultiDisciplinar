from mesa import Agent
import random
from mapa.paths import PATHS_CATRACAS
from constants import DEFAULT_TRAY_PORTIONS, WAITING_TIME_THRESHOLD, TRAY_INTERACTION_TIME, TABLE_INTERACTION_TIME
from mapa.mapa_RU import CellType
from mesa.space import MultiGrid
import math as mt

CATRACA_MAPPING = {1: (18, 2), 2: (18, 4), 3: (99, 2), 4: (99, 4)}

TRAY_TYPES = {'Rice_tray', 'Brown_Rice_Tray', 'Beans_Tray',
              'Guarn_Tray', 'Veg_Tray', 'Meat_Tray', 'Sal_Tray', 'Talher_Tray'}

# Representa os recursos que são interagíveis com os estudantes
# 
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
            self.food_count = DEFAULT_TRAY_PORTIONS
            return self.type.split('_')[0]
        else:
            return None

    def refill(self):
        if "Tray" in self.type:
            self.food_count = DEFAULT_TRAY_PORTIONS
            print(f"Refilled {self.type} at position {self.x}, {self.y}")

class StudentAgent(Agent):
    def __init__(self, unique_id, model, x, y):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.type = "Student"
        self.waiting_time = 0
        self.blocked_steps = 0
        self.steps_visited = 0
        self.visited_groups = set()
        self.current_goal = None
        self.current_path = None
        self.interaction_timer = 0
        self.terminou_path = False
        self.ta_na_mesa = False
        self.interaction_table_timer = -1
        self.tray_interaction_target = None
        self.move_attempts = []
        self.path_occupancy = {}
        self._initialize_preferences()
        self.determine_catraca_id()

    # seleciona de maneira aleatória as preferências do estudante
    # !! avaliar criar uma distribuição para essas preferências
    def _initialize_preferences(self):
        self.diet = random.choice(["vegan", "meat_eater", "no_meat_or_veg"])
        self.rice_type = random.choice(["rice", "brown_rice", "no_rice"])

    # verifica se o estudante está com com uma tray na sua frente
    # método chamado no step
    def check_tray_interaction(self):
        x, y = self.pos
        upper_cell = (x, y - 1)
        lower_cell = (x, y + 1)

        # preenche upper_tray ou lower_tray com o tipo da tray
        # caso não esteja na posição para a interação, retorna null
        upper_tray = self.check_tray_type(upper_cell)
        lower_tray = self.check_tray_type(lower_cell)

        # caso o estudante esteja para interagir com uma tray, chama o método
        # tray_interaction_target, passando o tray.type para o método
        if upper_tray:
            self.set_tray_interaction_target(upper_tray)
        elif lower_tray:
            self.set_tray_interaction_target(lower_tray)
        
        else: # move para a próxima etapa caso não tenha interação com a tray
            self.move_to_next_step()

    def check_tray_type(self, cell):
        tray = next((agent for agent in self.model.grid.get_cell_list_contents([cell]) if
                    isinstance(agent, StaticAgent) and agent.type in TRAY_TYPES), None)
        return tray.type if tray else None

    # define qual o tipo de interação irá ocorrer entre o estudante e a tray
    # em que ele está posicionado à frente
    def set_tray_interaction_target(self, tray_type):
        # caso a dieta do estudante seja vegana
        # vai fazer a verificação com as trey veganas
        if self.diet == "vegan":
            if tray_type == 'Veg_Tray':
                self.tray_interaction_target = 'Veg_Tray'
                self.interaction_timer = TRAY_INTERACTION_TIME
        elif self.diet == "meat_eater":
            if tray_type == 'Meat_Tray':
                self.tray_interaction_target = 'Meat_Tray'
                self.interaction_timer = TRAY_INTERACTION_TIME
        else: # !! só é acessado caso a dieta do estudante seja no_meat_or_veg
            # verificar se ele salta direto para a 'sal_tray'
            self.tray_interaction_target = 'Sal_Tray'


        if self.rice_type == "brown_rice":
            if tray_type == 'Brown_Rice_Tray':
                self.tray_interaction_target = 'brown_rice'
                self.interaction_timer = TRAY_INTERACTION_TIME
        elif self.rice_type == "rice":
            if tray_type == 'Rice_Tray':
                self.tray_interaction_target = 'Rice_Tray'
                self.interaction_timer = TRAY_INTERACTION_TIME
        else:
            self.tray_interaction_target = 'Beans_Tray'


        if tray_type != 'Meat_Tray' and tray_type != 'Veg_Tray' and tray_type != 'Rice_Tray' and tray_type != 'Brown_Rice_Tray':
            self.tray_interaction_target = tray_type
            self.interaction_timer = TRAY_INTERACTION_TIME

    # método chamado caso a verificação:
    # if not self.current_path: dê verdadeira no step
    # !! verificar função
    def _choose_empty_path(self):
        self.update_path_occupancy()
        catraca_id_str = str(self.catraca_id)
        valid_paths = [path for path in self.path_occupancy.keys() if str(
            path).startswith(catraca_id_str)]
        if not valid_paths:
            print('Student found no valid path! FIX THIS URGENT')
            return None
        min_occupancy = min(self.path_occupancy[path] for path in valid_paths)
        least_occupied_paths = [
            path for path in valid_paths if self.path_occupancy[path] == min_occupancy]

        if len(least_occupied_paths) == len(valid_paths):
            return random.choice(least_occupied_paths)

        return random.choice(least_occupied_paths)

    # marca o número de estudante que estão ocupando posições do path
    # retorna a ocupação para todos os paths
    def update_path_occupancy(self):
        self.path_occupancy = {}
        for path_name in PATHS_CATRACAS.keys():
            occupancy = len([agent for agent in self.model.schedule.agents if isinstance(
                agent, StudentAgent) and agent.current_path == path_name])
            self.path_occupancy[path_name] = occupancy

    # caso a posição do estudante seja igual a uma das posições das catracas
    # marca o catraca_id do estudante com o id (chave) da CATRACA_MAPPING
    def determine_catraca_id(self):
        for catraca_id, catraca_position in CATRACA_MAPPING.items():
            if self.pos == catraca_position:
                self.catraca_id = catraca_id

    def move_to_next_step(self):
        if self.current_path:
            path_coordinates = PATHS_CATRACAS.get(self.current_path, [])
            if path_coordinates:
                if len(path_coordinates) > self.steps_visited:
                    next_step = path_coordinates[self.steps_visited]
                    x, y = next_step 

                    # verifica a ocupação da prox pos da malha usando o model
                    next_step_occupied = any(agent.pos == (x, y) for agent in self.model.schedule.agents)
                    
                    # Calculate the number of steps for 1-meter movement 
                    steps_per_meter = 1
                    
                    if not next_step_occupied:
                        # Check if it's time to move (every 3 seconds)
                        # mesmo estando desocupado a movimentação só ocorre após
                        # três tentativas de movimentação
                        if self.blocked_steps % 3 == 0:
                            ## MOVIMENTA O AGENTE NO MODEL
                            self.model.grid.move_agent(self, (x, y))
                            self.move_attempts.append({
                                "from": self.pos,
                                "to": (x, y),
                            })
                            
                            self.steps_visited += 1
                            self.blocked_steps = 0
                        else:
                            self.blocked_steps += 1 
                            
                    else:
                        if self.pos == (99, 2):
                                print(f'\n  ESTUDANTE PRESO na posição {x,y} com path {self.current_path} e com nextstep {next_step}\n')
                        self.blocked_steps += 1
                else: # chega ao final do path quando if len(path_coordinates) <= self.steps_visited:
                    print(f"Agent {self.unique_id} has reached the end of path {self.current_path}")
                    self.terminou_path = True
            else:
                print(f"Agent {self.unique_id} has no more steps to follow in path {self.current_path}")
        else:
            print(f"Agent {self.unique_id} has no current path to follow.")

    # função que comanda as interações dos estudantes com o ambientetray, marcando a espera
    # no ponto de atividade
    def step(self):
        if not self.current_path:
            # não está em um path
            self.current_path = self._choose_empty_path()
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
            elif self.interaction_timer > 0: # interage com o ambiente/tray até que o timer chegue a 0
                self.interaction_timer -= 1
                self.waiting_time += 1
            elif self.interaction_timer == 0: # verifica a posição atual do estudante
                # e chama o método check_tray_interaction para marcar o tempo de interação
                # ou tempo que ficará parado naquela posição caso tenha que interagir com o ambiente/tray
                self.waiting_time += 1
                self.check_tray_interaction() # o self.interaction_timer é setado para TRAY_INTERACTION_TIME
                self.move_to_next_step()


    
    def find_nearest_free_table(self):
        tables = self.model.get_free_tables(self.pos)
        if tables:
            chossen_table = random.choice(tables)
            if chossen_table:
                self.set_table_interaction_target(chossen_table)
                return chossen_table

    def set_table_interaction_target(self, table):
        self.table_interaction_target = table
        self.interaction_table_timer = TABLE_INTERACTION_TIME

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
