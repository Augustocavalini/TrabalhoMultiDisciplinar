from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.visualization.modules import TextElement
from mesa.datacollection import DataCollector

from mapa.mapa_RU import CellType
from constants import *
from agents import StudentAgent, StaticAgent, MovementUtils

from openpyxl import Workbook, load_workbook
import datetime

class ModelText(TextElement):
    def __init__(self):
        pass

    def render(self, model):

        student_agents = [
            agent for agent in model.schedule.agents if isinstance(agent, StudentAgent)]
        avg_waiting_time = sum(agent.waiting_time for agent in student_agents) / \
            len(student_agents) if student_agents else 0
        
        # waiting_time_until_tray = sum(agent.waiting_time_until_tray for agent in student_agents if agent.flag_until_tray == True) / \
        #     len(student_agents) if student_agents else 0

        agents_until_tray = [agent for agent in student_agents if agent.flag_until_tray == True]
        waiting_time_until_tray = sum(agent.waiting_time_until_tray for agent in agents_until_tray) / len(agents_until_tray) if agents_until_tray else 0

        avg_waiting_time_total = model.waiting_time_until_tray_total / model.num_students_total if model.num_students_total > 0 else 0
        
        

        # vect_tempo_esp_until_tray = []
        # vect_time_esp_until_tray = []

        # vect_time_esp_until_tray.append(model.time)
        # vect_tempo_esp_until_tray.append(waiting_time_until_tray)

        arquivo = "valores.xlsx"

        if os.path.exists(arquivo):
            wb = load_workbook(arquivo)
            ws = wb.active
        else:
            wb = Workbook()
            ws = wb.active

        # Descobre a última linha usada da coluna A
        ultima_linha = ws.max_row

        # Se a última célula está vazia, não conta como usada
        if ws.cell(row=ultima_linha, column=1).value is not None:
            # Sempre cria um novo arquivo ao iniciar uma nova execução do main.py
            # Usa um nome de arquivo único baseado em timestamp
            if not hasattr(model, 'result_file'):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                model.result_file = f"valores_{timestamp}.xlsx"
            arquivo = model.result_file

            if os.path.exists(arquivo):
                wb = load_workbook(arquivo)
                ws = wb.active
            else:
                wb = Workbook()
                ws = wb.active

            ultima_linha = ws.max_row

            if ws.cell(row=ultima_linha, column=1).value is not None:
                nova_linha = ultima_linha + 1
            else:
                nova_linha = ultima_linha

            ws.cell(row=nova_linha, column=1, value=waiting_time_until_tray)
            ws.cell(row=nova_linha, column=2, value=avg_waiting_time_total)

            wb.save(arquivo)
        
        return f"Current Hour: {model.get_human_readable_time()}  | Estudantes: {model.num_students} |  Tempo de espera medio(pra qualquer coisa): {avg_waiting_time} | Tempo de fila antes da rampa(): {(waiting_time_until_tray)}  | Tempo de espera medio(ao longo de todo o período): {avg_waiting_time_total} "
class RestaurantModel(Model):
    AGENT_TYPE_MAPPING = {
        CellType.TURNSTILE: 'Turnstile',
        CellType.WALL: 'Wall',
        CellType.EXIT: 'Exit',
        CellType.JUICE: 'Juice',
        CellType.SPICES: 'Spices',
        CellType.DESSERT: 'Dessert',
        CellType.TABLE: 'Table',
        CellType.EMPTY_TRAY: 'Empty_tray',
        CellType.RICE_TRAY: 'Rice_tray',
        CellType.BROWN_RICE_TRAY: 'Brown_Rice_Tray',
        CellType.BEANS_TRAY: 'Beans_Tray',
        CellType.GUARN_TRAY: 'Guarn_Tray',
        CellType.VEG_TRAY: 'Veg_Tray',
        CellType.MEAT_TRAY: 'Meat_Tray',
        CellType.SAL_TRAY: 'Sal_Tray',
        CellType.TALHER_TRAY: 'Talher_Tray',
    }

    def __init__(self, external_grid, day, meal, hour, filtered_df):
        super().__init__()  # inicializa a superclasse Model do Mesa
        self.height = len(external_grid)
        self.width = len(external_grid[0])
        self.external_grid = external_grid
        self.movement_utils = MovementUtils(self)
        self.steps_since_last_student = 0
        self.datacollector = DataCollector({
            "Average_Waiting_Time": lambda m: sum([agent.waiting_time for agent in m.schedule.agents if isinstance(agent, StudentAgent)]) / (len([agent for agent in m.schedule.agents if isinstance(agent, StudentAgent)]) or 1)
        })

        self.grid = MultiGrid(self.width, self.height, True)
        self.schedule = RandomActivation(self)
        self.day = day
        self.meal = meal
        self.hour = int(hour.split(":")[0]) * 3600  # Convert to seconds
        self.time = self.hour
        self.error_message = None
        self.next_id = 0
        self.num_students = 0

        self.num_students_total = 0 # calcula o número total de estudantes que entraram no modelo
        self.waiting_time_until_tray_total = 0 # calcula o tempo total de espera até a bandeja, por todos os estudantes que passsaram pelo modelo

        self.filtered_df = filtered_df
        self.locations_cache = {
            'empty_trays': self.find_cell_positions(CellType.EMPTY_TRAY),
            'rice_trays': self.find_cell_positions(CellType.RICE_TRAY),
            'brown_rice_trays': self.find_cell_positions(CellType.BROWN_RICE_TRAY),
            'beans_trays': self.find_cell_positions(CellType.BEANS_TRAY),
            'guarn_trays': self.find_cell_positions(CellType.GUARN_TRAY),
            'veg_trays': self.find_cell_positions(CellType.VEG_TRAY),
            'meat_trays': self.find_cell_positions(CellType.MEAT_TRAY),
            'sal_trays': self.find_cell_positions(CellType.SAL_TRAY),
            'talher_trays': self.find_cell_positions(CellType.TALHER_TRAY),
            'juices': self.find_cell_positions(CellType.JUICE),
            'spices': self.find_cell_positions(CellType.SPICES),
            'desserts': self.find_cell_positions(CellType.DESSERT),
            'tables': self.find_cell_positions(CellType.TABLE),
            'exits': self.find_cell_positions(CellType.EXIT)
        }

        # self.linha_fora_RU_1 = []
        # self.linha_fora_RU_2 = []
        # self.linha_fora_RU_3 = []
        # self.linha_fora_RU_4 = []
        self.linha_fora_RU_dir = []  # Linha de estudantes fora do RU, entrada direita
        self.linha_fora_RU_esq = []  # Linha de estudantes fora do RU, entrada esquerda

        for y, row in enumerate(external_grid):
            for x, cell_value in enumerate(row):
                if cell_value in self.AGENT_TYPE_MAPPING:
                    agent_type = self.AGENT_TYPE_MAPPING[cell_value]
                    agent = StaticAgent((x, y), self, x, y, agent_type)
                    self.grid.place_agent(agent, (x, y))

    def step(self):
        """Defines the action taken in each time step of the simulation."""
        current_time = self.get_human_readable_time()
        print(f"Step method called! Current time: {current_time}")

        # If there is an error message, stop the simulation.
        if self.error_message:
            print(self.error_message)
            return

        self.time += 1
        self.schedule.step()

        # Add a new student on the first step or every 8 steps.
        matching_rows = self.filtered_df[self.filtered_df['seconds_from_start'] == self.time]
        for _, row in matching_rows.iterrows():
            self.add_new_student(catraca_id=row['IDCatraca'])
        
        self.put_students_in_line() # colocar um estudante depois da catraca, se houver um na fila

        self.datacollector.collect(self)

    def get_next_id(self):
        self.next_id += 1
        return self.next_id

    def find_cell_positions(self, cell_type):
        return [(j, i) for i, row in enumerate(self.external_grid)
                for j, cell in enumerate(row) if cell == cell_type]

    def update_cache(self, cell_type):
        """To be called whenever there's a change in a specific type of cell."""
        self.locations_cache[cell_type] = self.find_cell_positions(cell_type)

    def get_human_readable_time(self):
        hours = self.time // 3600
        minutes = (self.time % 3600) // 60
        seconds = self.time % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def add_new_student(self, catraca_id):

        if self.num_students >= 10000:
            return

        #1 é a catraca inferior da direita
        #2 é a catraca superior da direita
        #3 é a catraca inferior da esquerda
        #4 é a catraca superior da esquerda
        catraca_mapping = {1: (18, 2), 2: (18, 4), 3: (99, 2), 4: (99, 4)}
        entry_coords = [(18, 2), (18, 4), (99, 2), (99, 4)]

        chosen_entry = catraca_mapping.get(catraca_id)
        if not chosen_entry:
            print(
                f"Warning: Catraca ID {catraca_id} not found in mapping. Choosing random entry.")
            chosen_entry = self.random.choice(entry_coords)
        
        print(f"Estudante Chegou na fila da catraca {catraca_id} ({chosen_entry})")
        student_id = self.get_next_id()
        student = StudentAgent(student_id, self, *chosen_entry)

        if chosen_entry == (99, 2) or chosen_entry == (99, 4):
            self.linha_fora_RU_dir.append(student)

        elif chosen_entry == (18, 2) or chosen_entry == (18, 4):
            self.linha_fora_RU_esq.append(student)
        
        self.num_students += 1
        self.num_students_total += 1

        print(f"Trying to add a new student at {chosen_entry}")


    def put_students_in_line(self):
        for idx, line in enumerate([self.linha_fora_RU_dir, self.linha_fora_RU_esq]):
            if line:
                if idx == 0: # linha_fora_RU_dir
                    pos_x = 99
                elif idx == 1: # linha_fora_RU_esq
                    pos_x = 18

                if self.grid.is_cell_empty((pos_x, 2)) and self.grid.is_cell_empty((pos_x, 4)):
                    pos_y = np.random.choice([2, 4])
                    student = line.pop(0)
                    student.pos = (pos_x, pos_y)

                    print(f"Placing student {student.unique_id} at ({student.pos})")
                    self.grid.place_agent(student, (student.pos))
                    self.schedule.add(student)
                    print(f"Student {student.unique_id} placed in the grid at ({student.pos})")
                elif self.grid.is_cell_empty((pos_x, 2)):
                    student = line.pop(0)
                    student.pos = (pos_x, 2)

                    print(f"Placing student {student.unique_id} at ({student.pos})")
                    self.grid.place_agent(student, (student.pos))
                    self.schedule.add(student)
                    print(f"Student {student.unique_id} placed in the grid at ({student.pos})")
                elif self.grid.is_cell_empty((pos_x, 4)):
                    student = line.pop(0)
                    student.pos = (pos_x, 4)

                    print(f"Placing student {student.unique_id} at ({student.pos})")
                    self.grid.place_agent(student, (student.pos))
                    self.schedule.add(student)
                    print(f"Student {student.unique_id} placed in the grid at ({student.pos})")
                else:
                    waiting_student = line[0]  # referência ao primeiro da fila sem remover
                    print(f"Cell ({waiting_student.pos}) is not empty, cannot place student {waiting_student.unique_id}.")

                for student in line:    
                    #print(f"Student {student.unique_id} is still waiting in line.")
                    student.waiting_time_until_tray += 1

            else:
                print("No students in line to place.")
    def get_free_tables(self, student_pos):
        tables = []
        for table in self.locations_cache['tables']:
            if self.is_table_free(table, student_pos):
                tables.append(table)
        return tables

    def is_table_free(self, table, student_pos):
        left_cell = (table[0] - 1, table[1])
        right_cell = (table[0] + 1, table[1])

        if self.is_cell_empty(left_cell, student_pos):
            return True
        if self.is_cell_empty(right_cell, student_pos):
            return True

        return False

    def is_cell_empty(self, cell, excluding_agent=None):
        x, y = cell
        cell_contents = self.grid.get_cell_list_contents([(x, y)])
        if excluding_agent is not None:
            cell_contents = [
                agent for agent in cell_contents if agent is not excluding_agent]

        return not any(cell_contents)


def agent_portrayal(agent):
    """Defines the visual portrayal of agents in the simulation."""
    if isinstance(agent, StudentAgent):
        if agent.waiting_time > WAITING_TIME_THRESHOLD:
            color = "orange"
        elif agent.model.error_message:
            color = "red"
        else:
            if agent.diet == "vegan":
                color = "green"
            elif agent.diet == "meat_eater":
                color = "blue"
            else:
                color = "blue"
        return {
            "Shape": "circle",
            "Color": color,
            "Filled": "true",
            "Layer": 0,
            "r": 0.5
        }
    else:
        tray_colors = {
            "Rice": "pink",
            "Brown": "brown",
            "Beans": "black",
            "Guarn": "blue",
            "Veg": "purple",
            "Meat": "red",
            "Sal": "yellow",
            "Talher": "orange",
            "EMPTY": "green"
        }
        shape_colors = {
            "Turnstile": "gray",
            "Wall": "black",
            "Exit": "red",
            "Juice": "blue",
            "Spices": "purple",
            "Dessert": "gold",
            "Table": "#766c6a",
            "EMPTY_TRAY": tray_colors["EMPTY"]
        }

        if "Tray" in agent.type and agent.content:
            return {
                "Shape": "rect",
                "Color": tray_colors.get(agent.content, "green"),
                "Filled": "true",
                "Layer": 1,
                "w": 1,
                "h": 1
            }
        else:
            return {
                "Shape": "rect",
                "Color": shape_colors.get(agent.type, "green"),
                "Filled": "true",
                "Layer": 1,
                "w": 1,
                "h": 1
            }