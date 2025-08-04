from model import RestaurantModel
from mapa.mapa_RU import GridConfig
import pandas as pd
from datetime import datetime, timedelta
from agents import StudentAgent
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# --------------------------
# Configuração inicial
# --------------------------
DATAFRAME = pd.read_csv('logentrada.csv')
DATAFRAME['Entrada'] = pd.to_datetime(DATAFRAME['Entrada'])

desired_day = '2023-01-05'
desired_meal = 'Almoco'
desired_hour = '11:00'

# Filtrando dataframe
filtered_df = DATAFRAME[
    (DATAFRAME['Entrada'].dt.date == datetime.strptime(desired_day, '%Y-%m-%d').date()) &
    (DATAFRAME['Refeicao'] == desired_meal)
].copy()

filtered_df['seconds_from_start'] = (
    filtered_df['Entrada'].dt.hour * 3600 +
    filtered_df['Entrada'].dt.minute * 60 +
    filtered_df['Entrada'].dt.second
)
filtered_df = filtered_df.sort_values(by='seconds_from_start')

# Criar grid externo
external_grid = GridConfig.get_grid()

# Criar modelo
model = RestaurantModel(
    external_grid=external_grid,
    day=desired_day,
    meal=desired_meal,
    hour=desired_hour,
    filtered_df=filtered_df
)

# --------------------------
# Determinar tempo máximo de simulação
# --------------------------
max_time = filtered_df['seconds_from_start'].max()
simulation_steps = int(max_time + 3600)  # adiciona 1h extra para garantir que todos terminem

print(f"⏳ Rodando simulação até {simulation_steps} steps (~{simulation_steps//60} min)")

# Rodar simulação
for i in range(simulation_steps):
    model.step()

# --------------------------
# Função de gráficos
# --------------------------
def gerar_graficos(model):
    all_data = []
    for agent in model.schedule.agents:
        if isinstance(agent, StudentAgent):
            all_data.extend(agent.collected_data)

    if not all_data:
        print("Nenhum dado coletado para os agentes.")
        return

    df = pd.DataFrame(all_data)

    # Selecionar 5 agentes com intervalo de 30min
    checkpoints = np.arange(df["time_from_start"].min(), df["time_from_start"].max(), 1800)
    selected_agents = []

    for cp in checkpoints:
        subset = df[df["time_from_start"] >= cp]
        if not subset.empty:
            agent_id = subset.iloc[0]["agent_id"]
            if agent_id not in selected_agents:
                selected_agents.append(agent_id)
        if len(selected_agents) >= 5:
            break

    # Caso não tenha 5 agentes suficientes, completa com IDs únicos
    if len(selected_agents) < 5:
        for aid in df["agent_id"].unique():
            if aid not in selected_agents:
                selected_agents.append(aid)
            if len(selected_agents) == 5:
                break

    # Conversão para horário
    start_time = datetime.strptime(desired_hour, "%H:%M")
    def format_time(x, _):
        return (start_time + timedelta(seconds=int(x))).strftime("%H:%M:%S")

    formatter = mticker.FuncFormatter(format_time)

    # 1 - Tempo de espera acumulado
    plt.figure(figsize=(10, 5))
    for aid in selected_agents:
        subdf = df[df["agent_id"] == aid]
        plt.plot(subdf["time_from_start"], subdf["waiting_time"], label=f"Agente {aid}")
    plt.title("📈 Evolução do Tempo de Espera por Agente")
    plt.xlabel("Horário no modelo (HH:MM:SS)")
    plt.ylabel("Tempo de Espera (s)")
    plt.gca().xaxis.set_major_formatter(formatter)
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 2 - Tempo até bandeja
    plt.figure(figsize=(10, 5))
    for aid in selected_agents:
        subdf = df[df["agent_id"] == aid]
        plt.plot(subdf["time_from_start"], subdf["waiting_time_until_tray"], label=f"Agente {aid}")
    plt.title("⏳ Tempo até pegar a bandeja")
    plt.xlabel("Horário no modelo (HH:MM:SS)")
    plt.ylabel("Tempo até bandeja (s)")
    plt.gca().xaxis.set_major_formatter(formatter)
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 3 - Distribuição final de bandejas interagidas (todos agentes)
    plt.figure(figsize=(8, 4))
    df_last = df.groupby("agent_id").last()
    df_last["tray_interaction_target"].value_counts().plot(kind="bar")
    plt.title("🍽️ Distribuição final de bandejas interagidas (todos os agentes)")
    plt.ylabel("Número de agentes")
    plt.xticks(rotation=45)
    plt.grid(axis="y")
    plt.tight_layout()
    plt.show()

    # 4 - Passos bloqueados
    plt.figure(figsize=(10, 5))
    for aid in selected_agents:
        subdf = df[df["agent_id"] == aid]
        plt.plot(subdf["time_from_start"], subdf["blocked_steps"], label=f"Agente {aid}")
    plt.title("🚧 Evolução de passos bloqueados")
    plt.xlabel("Horário no modelo (HH:MM:SS)")
    plt.ylabel("Passos bloqueados")
    plt.gca().xaxis.set_major_formatter(formatter)
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Chama a função
gerar_graficos(model)
