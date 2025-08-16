import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

arquivo = r'C:\Users\mangu\Documents\GitHub\TrabalhoMultiDisciplinar\Modelo_RU_main\src\valores.xlsx'
df = pd.read_excel(arquivo)

# Cria o eixo do tempo iniciando em 0 (0 -> 11:00:00)
tempo = range(len(df))

def segundos_para_hhmmss(segundos):
    return str(timedelta(seconds=int(segundos)))

def segundos_para_mmss(segundos):
    m, s = divmod(int(segundos), 60)
    return f"{m:02d}:{s:02d}"

# Colunas numéricas (ex.: B e C se precisar)
col_b = pd.to_numeric(df.iloc[:, 3], errors='coerce')

plt.figure(figsize=(12, 6))

# Linha principal
plt.plot(tempo, col_b, label='Tempo médio de fila do modelo')

# Hardcode dos pontos de scatter:
# 12:00 → 00:03:00
# 12:10 → 00:06:00
# 12:20 → 00:08:00
# 12:30 → 00:11:00
offset_segundos = 11 * 3600
hard_times = [
    '11:00', '11:10', '11:20', '11:30', '11:40', '11:50',
    '12:00', '12:10', '12:20', '12:30', '12:40', '12:50',
    '13:00', '13:10', '13:20', '13:30', '13:40', '13:50', '14:00'
]
scatter_x = [
    (int(h)*3600 + int(m)*60) - offset_segundos
    for h, m in (t.split(':') for t in hard_times)
]
hard_values = [
    '00:01:00', '00:01:00', '00:02:00', '00:03:00', '00:01:00',
    '00:02:00', '00:03:00', '00:06:00', '00:08:00', '00:11:00',
    '00:12:00', '00:10:00', '00:08:00', '00:06:00', '00:04:00',
    '00:01:00', '00:01:00', '00:00:00', '00:00:00'
]
def tempo_para_segundos(tempo_str):
    h, m, s = map(int, tempo_str.split(':'))
    return h*3600 + m*60 + s

scatter_y = [tempo_para_segundos(v) for v in hard_values]

plt.scatter(scatter_x, scatter_y,
            color='red', label='Média dos tempos observados', zorder=5)

plt.xlabel('Tempo (h:m:s)')
plt.ylabel('Valor (mm:ss)')
plt.title('Tempos de fila médio em janelas deslizantes de 30 segundos')
plt.legend()
plt.grid(True)
plt.tight_layout()

# Eixo X formatado de 11:00 em diante
xticks = list(range(0, len(df)+1, 600))
xticklabels = [segundos_para_hhmmss(x + offset_segundos) for x in xticks]
plt.xticks(xticks, xticklabels, rotation=45)

# Eixo Y somente >= 0 e formatado em mm:ss
plt.ylim(bottom=0)
yticks = plt.gca().get_yticks()
yticklabels = [segundos_para_mmss(y) for y in yticks]
plt.yticks(yticks, yticklabels)

plt.show()