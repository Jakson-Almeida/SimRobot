import pygame
import pygame.sndarray
import math
import random
import heapq
import numpy as np
from typing import List, Tuple, Dict, Optional

# Definições de cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Tamanho da célula
CELL_SIZE = 100
MARGIN = 5
ANIMATION_SPEED = 5  # Velocidade de animação do robô
RECHARGE_SPEED = 60  # Segundos para recarregar de 0% a 100%
STATION_WAIT_TIME = 3000  # Tempo em milissegundos para iniciar recarga (3 segundos)

# Sistema de itens
MAX_ITEMS_PER_CELL = 2  # Máximo de itens por célula tipo '1'
ROBOT_CAPACITY = 3  # Capacidade máxima do robô
ITEM_TYPES = ['TYPE_A', 'TYPE_B']  # Dois tipos de itens
ITEM_COLORS = {
    'TYPE_A': (255, 100, 100),  # Vermelho claro
    'TYPE_B': (100, 100, 255),  # Azul claro
}

# Matriz do ambiente
#matriz2 = [
#    ['A', '1', '1', 'R', 'A', '1'],
#    ['1', '1', '1', '1', '1', '1'],
#    ['1', '1', '1', '0', '1', '1'],
#    ['1', 'S', '1', '1', '1', '1'],
#]

#matriz2 = [
#    ['A', '1', '1', 'R', 'A', '1', '1'],
#    ['1', '1', '1', '1', '1', '1', '0'],
#    ['1', '1', '1', '0', '0', '1', '1'],
#    ['1', 'S', '1', '1', '1', '1', '1'],
#    ['1', '0', '1', '1', '0', '1', '1'],
#]

matriz2 = [
    ['A', '1', '1', 'R', '1', '1', '1', '1'],
    ['1', '1', '1', '1', '1', '1', '1', '0'],
    ['1', '1', '1', '0', '0', '0', '0', 'A'],
    ['1', 'S', '1', '1', '1', '1', '0', '1'],
    ['1', '0', '1', '1', '0', '1', '1', '1'],
    ['1', '0', '0', '1', '0', '1', '1', 'R'],
]

# Definir a posição inicial do robô (encontra o 'S')
for row_idx, row in enumerate(matriz2):
    for col_idx, cell in enumerate(row):
        if cell == 'S':
            robot_grid_pos = [col_idx, row_idx]  # (x, y)

# Inicializar pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.mixer.set_num_channels(8)  # Permite 8 sons simultâneos

# Configurar a tela
GRID_WIDTH = len(matriz2[0]) * CELL_SIZE
GRID_HEIGHT = len(matriz2) * CELL_SIZE
PANEL_WIDTH = 350  # Largura do painel lateral
WIDTH = GRID_WIDTH + PANEL_WIDTH  # Largura total da tela
HEIGHT = GRID_HEIGHT
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulador de Robô com Bateria e Gradiente")

# Fonte para exibição de texto
font = pygame.font.Font(None, 32)       # Reduzido de 36
font_small = pygame.font.Font(None, 24)  # Reduzido de 28
font_tiny = pygame.font.Font(None, 18)   # Reduzido de 22

# Sistema de scroll do painel lateral
panel_scroll_offset = 0  # Offset de scroll do painel
panel_max_scroll = 0     # Máximo de scroll possível

# Sistema de sons
SOUND_ENABLED = True  # Toggle para habilitar/desabilitar sons
sounds = {}
sounds_failed = set()  # Nomes de sons que falharam ao criar (evita tentar de novo)

# Posição real do robô (para animação)
robot_real_pos = [robot_grid_pos[0] * CELL_SIZE, robot_grid_pos[1] * CELL_SIZE]
battery = 100  # Bateria inicial (100%)

# Variáveis de recarga automática
is_recharging = False
time_at_station = 0  # Tempo em milissegundos que está parado na estação
recharge_start_time = 0  # Tempo em milissegundos quando começou a recarregar
battery_at_recharge_start = 100  # Bateria quando começou a recarregar
last_position = robot_grid_pos.copy()  # Última posição para detectar movimento

# Sistema de itens
# items_on_grid: {(x, y): [{'type': 'TYPE_A'}, {'type': 'TYPE_B'}, ...]}
items_on_grid = {}
robot_inventory = []  # Lista de itens carregados pelo robô

# Variáveis de entrega automática
WAREHOUSE_WAIT_TIME = 3000  # Tempo em milissegundos para iniciar entrega (3 segundos)
DELIVERY_INTERVAL = 1000  # Intervalo entre entregas (1 segundo = 1000ms)
is_delivering = False
time_at_warehouse = 0  # Tempo em milissegundos que está parado no almoxarifado
last_delivery_time = 0  # Último tempo que entregou um item
items_delivered_count = 0  # Contador de itens entregues

# Variáveis de estado do jogo
game_state = "playing"  # "playing", "victory", "game_over"
total_items_initial = 0  # Total de itens no início do jogo

# Sistema de automação
AUTO_MODE_OFF = 0
AUTO_MODE_FULL = 1
AUTO_MODE_SEMI = 2
auto_mode = AUTO_MODE_OFF
current_path = []  # Caminho atual a seguir
current_path_index = 0  # Índice no caminho atual
current_action = None  # Ação atual: 'move', 'collect', 'deliver', 'recharge'
waiting_for_action = False  # Se está esperando ação automática completar
just_collected = False  # Flag para evitar processar próxima ação imediatamente após coleta
action_completed = False  # Flag para indicar que ação foi completada e pode avançar no plano

# Configurações do modo automático total
AUTO_ACTION_DELAY = 300  # Pausa de 300ms entre ações no modo automático total
last_action_time = 0  # Tempo da última ação completada
RECHARGE_THRESHOLD = 85  # Porcentagem de bateria suficiente para parar de recarregar

# Cache para recarga dinâmica
cached_target_battery = None  # Cache do target calculado
last_battery_calculation_time = 0  # Última vez que calculou

# Sistema de logs
showLogs = True  # Controla se os logs são exibidos no terminal


def generate_beep(frequency=440, duration=0.1, volume=0.5, wave_type='sine'):
    """Gera um beep sintético. Retorna None em caso de erro (não lança exceção)."""
    try:
        sample_rate = 22050
        n_samples = int(round(duration * sample_rate))
        if n_samples <= 0:
            return None
        
        # Gera diferentes tipos de onda
        t = np.arange(n_samples, dtype=np.float64) / sample_rate
        if wave_type == 'square':
            buf = np.sign(np.sin(2 * np.pi * frequency * t))
        else:
            buf = np.sin(2 * np.pi * frequency * t)
        
        # Aplica envelope para evitar clicks
        fade_samples = max(1, int(sample_rate * 0.01))
        fade_samples = min(fade_samples, len(buf) // 4)
        if fade_samples > 0:
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            buf[:fade_samples] *= fade_in
            buf[-fade_samples:] *= fade_out
        
        # Converte para formato stereo e aplica volume (array contíguo para compatibilidade)
        buf = (buf * volume * 32767).astype(np.int16)
        stereo_buf = np.ascontiguousarray(np.column_stack((buf, buf)))
        
        sound = pygame.sndarray.make_sound(stereo_buf)
        if hasattr(sound, 'set_volume'):
            sound.set_volume(1.0)
        return sound
    except Exception as e:
        log(f"generate_beep falhou (freq={frequency}): {e}", "SOUND")
        return None


# Parâmetros de cada som para inicialização e criação sob demanda
SOUND_DEFINITIONS = {
    'move': {'frequency': 300, 'duration': 0.08, 'volume': 0.6, 'wave_type': 'square'},
    'collect': {'frequency': 800, 'duration': 0.15, 'volume': 0.7, 'wave_type': 'square'},
    'deliver': {'frequency': 1000, 'duration': 0.2, 'volume': 0.8, 'wave_type': 'sine'},
    'recharge_start': {'frequency': 500, 'duration': 0.25, 'volume': 0.7, 'wave_type': 'sine'},
    'recharge_complete': {'frequency': 900, 'duration': 0.35, 'volume': 0.8, 'wave_type': 'sine'},
    'victory': {'frequency': 1200, 'duration': 0.5, 'volume': 0.9, 'wave_type': 'sine'},
    'gameover': {'frequency': 150, 'duration': 0.6, 'volume': 0.8, 'wave_type': 'square'},
    'mode_change': {'frequency': 600, 'duration': 0.18, 'volume': 0.7, 'wave_type': 'square'},
    'test': {'frequency': 440, 'duration': 0.3, 'volume': 0.8, 'wave_type': 'sine'},
}

# Sons que falharam ao criar (não tentar de novo)
sounds_failed = set()


def ensure_sound(sound_name):
    """Cria o som sob demanda se existir definição e ainda não tiver falhado. Retorna True se disponível."""
    global sounds, sounds_failed
    
    if sound_name in sounds and sounds[sound_name] is not None:
        return True
    if sound_name in sounds_failed:
        return False
    if sound_name not in SOUND_DEFINITIONS:
        return False
    
    try:
        snd = generate_beep(**SOUND_DEFINITIONS[sound_name])
        if snd is not None:
            sounds[sound_name] = snd
            log(f"Som '{sound_name}' criado sob demanda.", "SOUND")
            return True
    except Exception as e:
        log(f"Erro ao criar som '{sound_name}': {e}", "ERROR")
    
    sounds_failed.add(sound_name)
    return False


def init_sounds():
    """Inicializa todos os sons do jogo. Um falha não impede os demais."""
    global sounds, sounds_failed
    
    sounds_failed.clear()
    
    for name, kwargs in SOUND_DEFINITIONS.items():
        try:
            snd = generate_beep(**kwargs)
            if snd is not None:
                sounds[name] = snd
            else:
                sounds_failed.add(name)
        except Exception as e:
            log(f"Erro ao criar som '{name}': {e}", "ERROR")
            sounds_failed.add(name)
    
    loaded = len(sounds)
    total = len(SOUND_DEFINITIONS)
    log(f"Sistema de sons: {loaded}/{total} carregados.", "SOUND")
    
    if loaded == 0:
        log("Nenhum som pôde ser carregado. Verifique numpy e pygame.mixer.", "ERROR")
        return
    
    # Toca som de teste se disponível
    if SOUND_ENABLED and 'test' in sounds and sounds['test'] is not None:
        try:
            sounds['test'].play()
            log("Som de teste tocado (440 Hz).", "SOUND")
        except Exception as e:
            log(f"Erro ao tocar teste: {e}", "ERROR")


def play_sound(sound_name, debug=False):
    """Toca um som se o sistema de som estiver habilitado."""
    if not SOUND_ENABLED:
        if debug:
            log(f"Som '{sound_name}' não tocado (SOUND_ENABLED = False)", "SOUND")
        return
    
    # Se o som não está carregado, tenta criar sob demanda (apenas uma vez por nome)
    if sound_name not in sounds or sounds[sound_name] is None:
        if not ensure_sound(sound_name):
            if debug:
                log(f"Som '{sound_name}' indisponível.", "SOUND")
            return
    
    try:
        snd = sounds[sound_name]
        if snd is None:
            return
        channel = snd.play()
        if debug and channel:
            log(f"♪ Som '{sound_name}' tocando.", "SOUND")
    except Exception as e:
        global sounds_failed
        log(f"Erro ao tocar som '{sound_name}': {e}", "ERROR")
        sounds_failed.add(sound_name)


def toggle_sound():
    """Alterna o estado de habilitação dos sons."""
    global SOUND_ENABLED
    SOUND_ENABLED = not SOUND_ENABLED
    status = "LIGADO" if SOUND_ENABLED else "DESLIGADO"
    log(f"========== Som {status} ==========", "SOUND")
    if SOUND_ENABLED:
        log("Tocando som de confirmação...", "SOUND")
        play_sound('mode_change', debug=True)


def log(message, level="INFO"):
    """Exibe log no terminal se showLogs estiver ativo."""
    if showLogs:
        prefix = f"[{level}]"
        print(f"{prefix:10} {message}")


def draw_grid():
    """Desenha a matriz representando o ambiente."""
    for row_idx, row in enumerate(matriz2):
        for col_idx, cell in enumerate(row):
            x = col_idx * CELL_SIZE
            y = row_idx * CELL_SIZE

            # Definir cor baseada no tipo de célula
            if cell == 'S':
                color = (255, 255, 0)  # Amarelo
            elif cell == 'R':
                color = BLUE
            elif cell == 'A':
                color = GREEN
            elif cell == '1':
                color = WHITE
            elif cell == '0':
                color = GRAY
            else:
                color = BLACK  # Caso não identificado

            pygame.draw.rect(screen, color, (x, y, CELL_SIZE - MARGIN, CELL_SIZE - MARGIN))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE - MARGIN, CELL_SIZE - MARGIN), 2)  # Borda


def initialize_items_randomly():
    """Inicializa itens aleatoriamente nas células tipo '1'."""
    global items_on_grid, total_items_initial
    
    log("=== INICIALIZANDO ITENS NO AMBIENTE ===", "INIT")
    items_on_grid = {}
    total_items_initial = 0
    
    # Percorre todas as células tipo '1' e adiciona itens aleatoriamente
    for row_idx, row in enumerate(matriz2):
        for col_idx, cell in enumerate(row):
            if cell == '1':  # Apenas células livres
                # 40% de chance de ter itens nesta célula
                if random.random() < 0.4:
                    num_items = random.randint(1, MAX_ITEMS_PER_CELL)
                    cell_key = (col_idx, row_idx)
                    items_on_grid[cell_key] = []
                    
                    for _ in range(num_items):
                        item_type = random.choice(ITEM_TYPES)
                        items_on_grid[cell_key].append({'type': item_type})
                        total_items_initial += 1
                    
                    log(f"Item criado em ({col_idx}, {row_idx}): {num_items} itens tipo {item_type}", "INIT")
    
    log(f"Total de itens criados: {total_items_initial}", "INIT")
    log(f"Células com itens: {len(items_on_grid)}", "INIT")


def draw_items_on_grid():
    """Desenha os itens nas células do grid."""
    for (x, y), items in items_on_grid.items():
        if items:  # Só desenha se houver itens
            cell_x = x * CELL_SIZE
            cell_y = y * CELL_SIZE
            
            # Desenha pequenos círculos representando os itens
            for i, item in enumerate(items):
                item_color = ITEM_COLORS[item['type']]
                # Posiciona os itens lado a lado
                item_x = cell_x + 20 + (i * 25)
                item_y = cell_y + 20
                pygame.draw.circle(screen, item_color, (item_x, item_y), 8)
                pygame.draw.circle(screen, BLACK, (item_x, item_y), 8, 2)


def draw_robot_item_count():
    """Desenha a quantidade de itens carregados pelo robô (canto superior direito do robô)."""
    if len(robot_inventory) > 0:
        # Posição no canto superior direito do robô
        count_x = robot_real_pos[0] + CELL_SIZE - 30
        count_y = robot_real_pos[1] + 10
        
        # Fundo do contador
        pygame.draw.circle(screen, (50, 50, 50), (count_x, count_y), 15)
        pygame.draw.circle(screen, BLACK, (count_x, count_y), 15, 2)
        
        # Texto com a quantidade
        count_text = font.render(str(len(robot_inventory)), True, WHITE)
        text_rect = count_text.get_rect(center=(count_x, count_y))
        screen.blit(count_text, text_rect)


def collect_item(item_index):
    """Coleta um item específico da célula atual (item_index: 1 ou 2)."""
    global robot_inventory, items_on_grid
    
    x, y = robot_grid_pos
    cell_key = (x, y)
    
    # Verifica se há itens nesta célula e se o robô tem espaço
    if cell_key in items_on_grid and len(items_on_grid[cell_key]) > 0:
        if len(robot_inventory) < ROBOT_CAPACITY:
            # Ajusta o índice (usuário digita 1 ou 2, mas lista começa em 0)
            item_pos = item_index - 1
            
            # Verifica se o índice é válido
            if 0 <= item_pos < len(items_on_grid[cell_key]):
                # Remove o item da célula e adiciona ao inventário
                item = items_on_grid[cell_key].pop(item_pos)
                robot_inventory.append(item)
                
                log(f"Item coletado: tipo {item['type']} em ({x}, {y})", "COLLECT")
                log(f"Inventário: {len(robot_inventory) - 1} -> {len(robot_inventory)}/{ROBOT_CAPACITY}", "INVENTORY")
                
                # Toca som de coleta
                play_sound('collect')
                
                # Remove a célula se não houver mais itens
                if len(items_on_grid[cell_key]) == 0:
                    del items_on_grid[cell_key]
                    log(f"Célula ({x}, {y}) esvaziada", "COLLECT")
                
                return True
            else:
                log(f"Índice de item inválido: {item_index} (disponíveis: {len(items_on_grid[cell_key])})", "ERROR")
        else:
            log(f"Inventário cheio! Capacidade: {ROBOT_CAPACITY}, Atual: {len(robot_inventory)}", "ERROR")
    else:
        log(f"Nenhum item disponível em ({x}, {y})", "ERROR")
    return False


def is_at_warehouse():
    """Verifica se o robô está em um almoxarifado."""
    x, y = robot_grid_pos
    return matriz2[y][x] == 'A'


def update_auto_delivery():
    """Gerencia a entrega automática de itens no almoxarifado."""
    global robot_inventory, is_delivering, time_at_warehouse, last_delivery_time, items_delivered_count, last_position
    global waiting_for_action, current_action, current_path, auto_mode, last_action_time
    
    current_time = pygame.time.get_ticks()
    
    # Verifica se está em um almoxarifado e tem itens
    if is_at_warehouse() and len(robot_inventory) > 0:
        # Verifica se o robô se moveu desde a última verificação
        if robot_grid_pos == last_position:
            # Se não se moveu, incrementa o tempo no almoxarifado
            if not is_delivering:
                # Ainda não está entregando, verifica se já passou o tempo de espera
                if time_at_warehouse == 0:
                    time_at_warehouse = current_time
                    log(f"Robô chegou no almoxarifado com {len(robot_inventory)} itens. Aguardando {WAREHOUSE_WAIT_TIME/1000:.1f}s...", "DELIVERY")
                elif current_time - time_at_warehouse >= WAREHOUSE_WAIT_TIME:
                    # Passou 3 segundos, inicia a entrega
                    is_delivering = True
                    last_delivery_time = current_time
                    log(f"Entrega iniciada! {len(robot_inventory)} itens para entregar", "DELIVERY")
            else:
                # Já está entregando, verifica se passou 1 segundo desde a última entrega
                if current_time - last_delivery_time >= DELIVERY_INTERVAL:
                    # Entrega um item
                    if len(robot_inventory) > 0:
                        robot_inventory.pop(0)  # Remove o primeiro item
                        items_delivered_count += 1
                        last_delivery_time = current_time
                        log(f"Item entregue! Restantes: {len(robot_inventory)}, Total entregue: {items_delivered_count}", "DELIVERY")
                        
                        # Toca som de entrega
                        play_sound('deliver')
                    
                    # Se não há mais itens no inventário, para de entregar
                    if len(robot_inventory) == 0:
                        is_delivering = False
                        time_at_warehouse = 0
                        log(f"Entrega completa! Total de itens entregues: {items_delivered_count}", "DELIVERY")
                        
                        # Verifica se TODOS os itens do jogo foram entregues
                        items_remaining = sum(len(items) for items in items_on_grid.values())
                        
                        # Se estava em ação automática de entrega, marca como completa
                        if waiting_for_action and current_action == 'deliver' and auto_mode == AUTO_MODE_FULL:
                            waiting_for_action = False
                            current_action = None
                            current_path = []
                            last_action_time = current_time  # Marca tempo para delay de 300ms
                            invalidate_battery_cache()  # Invalida cache para recalcular bateria necessária
                            
                            if items_remaining == 0:
                                log("=== AÇÃO AUTOMÁTICA COMPLETA: Todos os itens foram entregues! ===", "AUTO")
                            else:
                                log(f"=== AÇÃO AUTOMÁTICA COMPLETA: Inventário entregue. Restam {items_remaining} itens no ambiente ===", "AUTO")
        else:
            # Robô se moveu ou chegou no almoxarifado, atualiza last_position e reseta entrega
            is_delivering = False
            time_at_warehouse = 0
            last_position = robot_grid_pos.copy()
    else:
        # Não está em almoxarifado ou não tem itens, reseta tudo
        if is_delivering or time_at_warehouse > 0:
            is_delivering = False
            time_at_warehouse = 0
        if not is_at_warehouse():
            last_position = robot_grid_pos.copy()


def get_robot_color():
    """Calcula a cor do robô suavemente do verde (100%) até o vermelho (0%)."""
    green = pygame.Color(0, 255, 0)  # Verde (máxima bateria)
    red = pygame.Color(255, 0, 0)  # Vermelho (sem bateria)

    # Interpolação linear de cor com base na porcentagem de bateria
    return green.lerp(red, 1 - (battery / 100))


def draw_robot5():
    """Desenha o robô na posição real com um design mais detalhado de rover."""
    x, y = robot_real_pos        # assumindo (x, y) como canto superior aproximado do robô
    color = get_robot_color()

    # --- Parâmetros básicos do corpo ---
    body_w, body_h = 60, 40
    body_rect = pygame.Rect(x + 15, y + 25, body_w, body_h)

    # --- Sombra do robô (leve deslocamento) ---
    shadow_rect = body_rect.move(3, 3)
    pygame.draw.rect(screen, (40, 40, 40), shadow_rect, border_radius=12)

    # --- Corpo principal do rover ---
    pygame.draw.rect(screen, color, body_rect, border_radius=12)
    # contorno
    pygame.draw.rect(screen, (0, 0, 0), body_rect, width=2, border_radius=12)

    # --- Rodas laterais grossas ---
    wheel_w, wheel_h = 12, body_h + 6
    left_wheel  = pygame.Rect(body_rect.left  - wheel_w + 3, body_rect.top - 3, wheel_w, wheel_h)
    right_wheel = pygame.Rect(body_rect.right - 3,           body_rect.top - 3, wheel_w, wheel_h)

    pygame.draw.rect(screen, (0, 0, 0), left_wheel,  border_radius=4)
    pygame.draw.rect(screen, (0, 0, 0), right_wheel, border_radius=4)

    # “sulcos” nas rodas para dar textura
    groove_count = 4
    for i in range(groove_count):
        gy = left_wheel.top + (i + 1) * wheel_h / (groove_count + 1)
        pygame.draw.line(screen, (70, 70, 70),
                         (left_wheel.left + 2, gy),
                         (left_wheel.right - 2, gy), 1)
        pygame.draw.line(screen, (70, 70, 70),
                         (right_wheel.left + 2, gy),
                         (right_wheel.right - 2, gy), 1)

    # --- Torre da câmera ---
    mast_rect = pygame.Rect(body_rect.centerx - 5, body_rect.top - 12, 10, 16)
    pygame.draw.rect(screen, color, mast_rect, border_radius=3)
    pygame.draw.rect(screen, (0, 0, 0), mast_rect, width=1, border_radius=3)

    # --- Câmera (olho) ---
    camera_center = (body_rect.centerx, body_rect.top - 16)
    camera_radius = 7
    pygame.draw.circle(screen, (0, 0, 0), camera_center, camera_radius)
    pygame.draw.circle(screen, (80, 180, 255), camera_center, camera_radius - 3)  # lente azul

    # --- Frente do rover (para indicar orientação) ---
    bumper_rect = pygame.Rect(body_rect.left, body_rect.top, body_w, 8)
    pygame.draw.rect(screen, (30, 30, 30), bumper_rect, border_radius=4)

    # Seta apontando para frente
    arrow_points = [
        (body_rect.centerx, body_rect.top - 5),
        (body_rect.centerx - 7, body_rect.top + 7),
        (body_rect.centerx + 7, body_rect.top + 7),
    ]
    pygame.draw.polygon(screen, (255, 255, 255), arrow_points)

    # --- LEDs traseiros ---
    led_w, led_h = 4, 6
    rear_y = body_rect.bottom - led_h - 3
    pygame.draw.rect(screen, (255, 0, 0),
                     (body_rect.left + 6, rear_y, led_w, led_h), border_radius=2)
    pygame.draw.rect(screen, (255, 0, 0),
                     (body_rect.right - 6 - led_w, rear_y, led_w, led_h), border_radius=2)


# Cores do robô e da caixa
ROBOT_BODY_COLOR   = (120, 220, 235)
ROBOT_STROKE_COLOR = (40, 80, 90)
ROBOT_JOINT_COLOR  = (60, 60, 70)
ROBOT_EYE_COLOR    = (70, 170, 255)

BOX_COLOR          = (194, 149, 89)
BOX_BORDER_COLOR   = (130, 95, 60)

def draw_robot(scale=0.5, offset_y=20):
    """Desenha um robô estilo armazém escalado por 'scale'."""
    x, y = robot_real_pos   # ponto de referência

    y += offset_y

    def s(v):
        return int(v * scale)

    # --- Corpo (oval) ---
    body_cx = x + s(80)
    body_cy = y + s(90)
    body_rx = s(35)
    body_ry = s(30)

    body_rect = pygame.Rect(
        body_cx - body_rx,
        body_cy - body_ry,
        2 * body_rx,
        2 * body_ry
    )

    # sombra
    shadow_rect = body_rect.move(s(4), s(6))
    pygame.draw.ellipse(screen, (30, 30, 30), shadow_rect)

    # corpo
    pygame.draw.ellipse(screen, ROBOT_BODY_COLOR, body_rect)
    pygame.draw.ellipse(screen, ROBOT_STROKE_COLOR, body_rect, s(3) or 1)

    # --- Faixa “cabeça” com olhos ---
    head_rect = body_rect.inflate(-s(10), -s(18))
    head_rect.height = head_rect.height // 2
    head_rect.centery = body_rect.centery - s(6)
    pygame.draw.ellipse(screen, (15, 15, 20), head_rect)

    # olhos
    eye_r = s(7)
    eye_dx = s(9)
    eye_y = head_rect.centery

    left_eye_center  = (head_rect.centerx - eye_dx, eye_y)
    right_eye_center = (head_rect.centerx + eye_dx, eye_y)

    pygame.draw.circle(screen, ROBOT_EYE_COLOR, left_eye_center, eye_r)
    pygame.draw.circle(screen, ROBOT_EYE_COLOR, right_eye_center, eye_r)

    # brilho
    pygame.draw.circle(screen, (230, 250, 255),
                       (left_eye_center[0] - s(2), left_eye_center[1] - s(3)), s(2) or 1)
    pygame.draw.circle(screen, (230, 250, 255),
                       (right_eye_center[0] - s(2), right_eye_center[1] - s(3)), s(2) or 1)

    # “boca” / painel
    mouth_rect = pygame.Rect(0, 0, s(26), s(10))
    mouth_rect.centerx = body_cx
    mouth_rect.centery = body_cy + s(8)
    pygame.draw.rect(screen, (20, 20, 25), mouth_rect, border_radius=s(4))
    pygame.draw.rect(screen, (60, 60, 70), mouth_rect, 1, border_radius=s(4))

    # --- Pernas ---
    bottom_y = body_rect.bottom - s(5)
    leg_attach_points = [
        (body_cx - s(22), bottom_y),
        (body_cx - s(8),  bottom_y),
        (body_cx + s(8),  bottom_y),
        (body_cx + s(22), bottom_y),
    ]

    leg_length1 = s(22)
    leg_length2 = s(20)

    for i, (px, py) in enumerate(leg_attach_points):
        # primeira junta
        if i < 2:
            knee1 = (px - s(8), py + leg_length1)   # esquerdas
        else:
            knee1 = (px + s(8), py + leg_length1)   # direitas

        # pé
        if i < 2:
            foot = (knee1[0] - s(6), knee1[1] + leg_length2)
        else:
            foot = (knee1[0] + s(6), knee1[1] + leg_length2)

        # segmentos
        pygame.draw.line(screen, ROBOT_STROKE_COLOR, (px, py), knee1, max(1, s(4)))
        pygame.draw.line(screen, ROBOT_STROKE_COLOR, knee1, foot, max(1, s(4)))

        # juntas
        pygame.draw.circle(screen, ROBOT_JOINT_COLOR, (px, py), s(4) or 1)
        pygame.draw.circle(screen, ROBOT_JOINT_COLOR, knee1, s(4) or 1)

        # pé oval
        foot_rect = pygame.Rect(0, 0, s(12), s(6))
        foot_rect.center = foot
        pygame.draw.ellipse(screen, ROBOT_STROKE_COLOR, foot_rect)

    # --- Braços levantados ---
    arm_left_base  = (body_rect.left + s(6),  body_rect.top + s(5))
    arm_right_base = (body_rect.right - s(6), body_rect.top + s(5))

    arm_left_joint1  = (arm_left_base[0] - s(20), arm_left_base[1] - s(25))
    arm_right_joint1 = (arm_right_base[0] + s(20), arm_right_base[1] - s(25))

    arm_left_joint2  = (arm_left_joint1[0] + s(5), arm_left_joint1[1] - s(25))
    arm_right_joint2 = (arm_right_joint1[0] - s(5), arm_right_joint1[1] - s(25))

    def draw_arm(base, j1, j2, end_x):
        pygame.draw.line(screen, ROBOT_STROKE_COLOR, base, j1, max(1, s(4)))
        pygame.draw.line(screen, ROBOT_STROKE_COLOR, j1, j2, max(1, s(4)))
        end_point = (end_x, j2[1] - s(8))
        pygame.draw.line(screen, ROBOT_STROKE_COLOR, j2, end_point, max(1, s(4)))

        for p in (base, j1, j2):
            pygame.draw.circle(screen, ROBOT_JOINT_COLOR, p, s(4) or 1)

        return end_point

    left_end  = draw_arm(arm_left_base,  arm_left_joint1,  arm_left_joint2,  body_cx - s(26))
    right_end = draw_arm(arm_right_base, arm_right_joint1, arm_right_joint2, body_cx + s(26))

    pygame.draw.circle(screen, ROBOT_STROKE_COLOR, left_end,  s(4) or 1)
    pygame.draw.circle(screen, ROBOT_STROKE_COLOR, right_end, s(4) or 1)

    # --- Caixa ---
    box_w, box_h = s(52), s(38)
    box_rect = pygame.Rect(0, 0, box_w, box_h)
    box_rect.midbottom = ((left_end[0] + right_end[0]) // 2, left_end[1] - s(2))

    pygame.draw.rect(screen, BOX_COLOR, box_rect)
    pygame.draw.rect(screen, BOX_BORDER_COLOR, box_rect, max(1, s(2)))

    pygame.draw.line(screen, BOX_BORDER_COLOR,
                     (box_rect.left + s(8), box_rect.top + s(10)),
                     (box_rect.right - s(6), box_rect.bottom - s(8)), max(1, s(2)))
    pygame.draw.line(screen, BOX_BORDER_COLOR,
                     (box_rect.left + s(6), box_rect.bottom - s(10)),
                     (box_rect.right - s(8), box_rect.top + s(8)), max(1, s(2)))

def draw_robot2():
    """Desenha o robô na posição real com um design de rover."""
    x, y = robot_real_pos
    color = get_robot_color()

    # Desenhar corpo do rover
    pygame.draw.rect(screen, color, (x + 15, y + 30, 60, 40), border_radius=10)

    # Desenhar câmera no topo
    pygame.draw.circle(screen, BLACK, (x + 45, y + 20), 10)

    # Desenhar rodas
    pygame.draw.circle(screen, BLACK, (x + 20, y + 65), 8)
    pygame.draw.circle(screen, BLACK, (x + 70, y + 65), 8)


def move_robot(command):
    """Move o robô baseado nos comandos recebidos e inicia a animação."""
    global robot_grid_pos, battery, is_recharging, time_at_station, last_position
    global is_delivering, time_at_warehouse

    if battery <= 0:
        return  # Se a bateria estiver em 0, o robô não pode se mover

    x, y = robot_grid_pos
    old_pos = robot_grid_pos.copy()

    if command == 'mr' and x + 1 < len(matriz2[0]) and matriz2[y][x + 1] != '0':
        robot_grid_pos = [x + 1, y]
    elif command == 'ml' and x - 1 >= 0 and matriz2[y][x - 1] != '0':
        robot_grid_pos = [x - 1, y]
    elif command == 'mu' and y - 1 >= 0 and matriz2[y - 1][x] != '0':
        robot_grid_pos = [x, y - 1]
    elif command == 'md' and y + 1 < len(matriz2) and matriz2[y + 1][x] != '0':
        robot_grid_pos = [x, y + 1]
    else:
        return  # Se o movimento for inválido, não gasta bateria

    # Se o robô se moveu, interrompe a recarga e entrega, e reseta os tempos
    if robot_grid_pos != old_pos:
        direction_map = {'mr': 'DIREITA', 'ml': 'ESQUERDA', 'mu': 'CIMA', 'md': 'BAIXO'}
        log(f"Robô moveu {direction_map.get(command, command)}: ({old_pos[0]}, {old_pos[1]}) -> ({robot_grid_pos[0]}, {robot_grid_pos[1]})", "MOVE")
        log(f"Bateria: {battery + 2}% -> {battery - 2}%", "BATTERY")
        
        # Toca som de movimento
        play_sound('move')
        
        if is_recharging:
            log("Recarga interrompida por movimento", "RECHARGE")
        if is_delivering:
            log("Entrega interrompida por movimento", "DELIVERY")
        
        is_recharging = False
        time_at_station = 0
        is_delivering = False
        time_at_warehouse = 0
        last_position = robot_grid_pos.copy()
        battery -= 2  # Reduz a bateria em 2% a cada movimento
        
        # Log do tipo de célula atual
        cell_type = matriz2[robot_grid_pos[1]][robot_grid_pos[0]]
        cell_types = {'S': 'INÍCIO', 'R': 'RECARGA', 'A': 'ALMOXARIFADO', '1': 'CAMINHO LIVRE', '0': 'OBSTÁCULO'}
        log(f"Robô está em célula tipo: {cell_types.get(cell_type, cell_type)}", "POSITION")


def is_at_recharge_station():
    """Verifica se o robô está em uma estação de recarga."""
    x, y = robot_grid_pos
    return matriz2[y][x] == 'R'


def update_auto_recharge():
    """Gerencia a recarga automática do robô."""
    global battery, is_recharging, time_at_station, recharge_start_time, battery_at_recharge_start, last_position
    global waiting_for_action, current_action, current_path, current_path_index, auto_mode, last_action_time
    
    current_time = pygame.time.get_ticks()
    
    # Verifica se está em uma estação de recarga
    if is_at_recharge_station():
        # Verifica se o robô se moveu desde a última verificação
        if robot_grid_pos == last_position:
            # Se não se moveu, incrementa o tempo na estação
            # Para modo automático total, calcula dinamicamente. Para manual/semi, carrega até 100%
            if auto_mode == AUTO_MODE_FULL:
                target_battery = calculate_needed_battery()
            else:
                target_battery = 100
            
            if battery >= target_battery:
                # Se atingiu o threshold/100%, mantém a bateria e não faz nada
                if is_recharging:
                    log(f"Recarga COMPLETA! Bateria: {battery:.1f}% (alvo: {target_battery}%)", "RECHARGE")
                    
                    # Toca som de recarga completa
                    play_sound('recharge_complete')
                    
                    # Se está no modo automático total, sempre limpa o estado (independente de waiting_for_action)
                    if auto_mode == AUTO_MODE_FULL:
                        # Força a limpeza completa do estado para evitar loops
                        if current_action == 'recharge':
                            waiting_for_action = False
                            current_action = None
                            current_path = []
                            current_path_index = 0
                            last_action_time = current_time  # Marca tempo para delay de 300ms
                            invalidate_battery_cache()  # Invalida cache para recalcular bateria necessária
                            log("=== AÇÃO AUTOMÁTICA COMPLETA: Recarga finalizada (estado limpo forçadamente) ===", "AUTO")
                
                battery = min(battery, 100)  # Garante que não ultrapasse 100%
                is_recharging = False
                # Não reseta time_at_station para não reiniciar o processo se a bateria baixar
            elif not is_recharging:
                # Ainda não está recarregando, verifica se já passou o tempo de espera
                if time_at_station == 0:
                    time_at_station = current_time
                    log(f"Robô chegou na estação de recarga. Aguardando {STATION_WAIT_TIME/1000:.1f}s...", "RECHARGE")
                elif current_time - time_at_station >= STATION_WAIT_TIME:
                    # Passou 3 segundos, inicia a recarga
                    is_recharging = True
                    recharge_start_time = current_time
                    battery_at_recharge_start = battery
                    log(f"Recarga iniciada! Bateria: {battery:.1f}% -> {target_battery}% (estimado: {((target_battery-battery)/100.0)*RECHARGE_SPEED:.1f}s)", "RECHARGE")
                    
                    # Toca som de início de recarga
                    play_sound('recharge_start')
            else:
                # Já está recarregando, atualiza a bateria
                if battery < target_battery:
                    # Calcula o tempo decorrido desde o início da recarga
                    elapsed_time = (current_time - recharge_start_time) / 1000.0  # em segundos
                    
                    # Calcula quanto tempo levaria para recarregar até o alvo
                    battery_needed = target_battery - battery_at_recharge_start
                    time_needed = (battery_needed / 100.0) * RECHARGE_SPEED
                    
                    # Calcula a porcentagem de recarga baseada no tempo decorrido
                    if time_needed > 0:
                        recharge_progress = min(1.0, elapsed_time / time_needed)
                        battery = battery_at_recharge_start + (battery_needed * recharge_progress)
                        battery = min(target_battery, battery)  # Garante que não ultrapasse o alvo
                    else:
                        battery = target_battery
                else:
                    # Bateria chegou ao threshold/100%, para de recarregar mas mantém na estação
                    if is_recharging:
                        log(f"Recarga completa! Bateria: {battery:.1f}% (alvo: {target_battery}%)", "RECHARGE")
                        
                        # Se estava em ação automática de recarga, marca como completa
                        if waiting_for_action and current_action == 'recharge' and auto_mode == AUTO_MODE_FULL:
                            waiting_for_action = False
                            current_action = None
                            current_path = []
                            last_action_time = current_time  # Marca tempo para delay de 300ms
                            invalidate_battery_cache()  # Invalida cache para recalcular bateria necessária
                            log("=== AÇÃO AUTOMÁTICA COMPLETA: Recarga finalizada ===", "AUTO")
                    
                    is_recharging = False
                    battery = min(battery, 100)  # Garante que não ultrapasse 100%
        else:
            # Robô se moveu ou chegou na estação, atualiza last_position e reseta recarga
            is_recharging = False
            time_at_station = 0
            last_position = robot_grid_pos.copy()
    else:
        # Não está em estação de recarga, reseta tudo
        if is_recharging or time_at_station > 0:
            is_recharging = False
            time_at_station = 0
        last_position = robot_grid_pos.copy()


# ==================== SISTEMA DE AUTOMAÇÃO ====================

def build_graph_from_matrix(matriz):
    """Constrói grafo a partir da matriz do ambiente."""
    graph = {}
    rows = len(matriz)
    cols = len(matriz[0])
    
    for y in range(rows):
        for x in range(cols):
            if matriz[y][x] != '0':  # Não é obstáculo
                node = (x, y)
                neighbors = []
                
                # Verifica 4 direções
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < cols and 0 <= ny < rows:
                        if matriz[ny][nx] != '0':
                            neighbors.append(((nx, ny), 1.0))  # Custo 1 por movimento
                
                graph[node] = neighbors
    
    return graph


def heuristic_manhattan(pos1, pos2):
    """Heurística Manhattan para A*."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def validate_path(path):
    """Valida se um caminho contém apenas células válidas (sem obstáculos)."""
    if not path:
        return False
    obstacle_found = False
    for pos in path:
        x, y = pos
        if not (0 <= x < len(matriz2[0]) and 0 <= y < len(matriz2)):
            log(f"🚫 ERRO: Posição fora dos limites: ({x}, {y})", "ERROR")
            return False
        if matriz2[y][x] == '0':
            log(f"🚫 ERRO: Caminho contém OBSTÁCULO em ({x}, {y})", "ERROR")
            obstacle_found = True
            return False
    if not obstacle_found:
        log(f"✓ Validação de caminho: {len(path)} passos, SEM obstáculos", "AUTO")
    return True


def a_star(graph, start, goal):
    """
    A* para encontrar caminho entre start e goal.
    Retorna lista de posições do caminho.
    """
    if start == goal:
        return [start]
    
    open_set = [(0, start)]  # (f_score, node)
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic_manhattan(start, goal)}
    
    while open_set:
        current = heapq.heappop(open_set)[1]
        
        if current == goal:
            # Reconstrói caminho
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]
        
        for neighbor, cost in graph.get(current, []):
            tentative_g = g_score[current] + cost
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic_manhattan(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return []  # Sem caminho


def find_all_positions():
    """Encontra todas as posições importantes no ambiente."""
    items = list(items_on_grid.keys())
    warehouses = []
    recharge_stations = []
    
    for y in range(len(matriz2)):
        for x in range(len(matriz2[0])):
            if matriz2[y][x] == 'A':
                warehouses.append((x, y))
            elif matriz2[y][x] == 'R':
                recharge_stations.append((x, y))
    
    return items, warehouses, recharge_stations


def find_nearest(target_pos, positions):
    """Encontra a posição mais próxima de target_pos."""
    if not positions:
        return None
    
    graph = build_graph_from_matrix(matriz2)
    min_dist = float('inf')
    nearest = None
    
    for pos in positions:
        path = a_star(graph, tuple(target_pos), pos)
        if path:
            dist = len(path) - 1
            if dist < min_dist:
                min_dist = dist
                nearest = pos
    
    return nearest


def estimate_battery_cost(path):
    """Estima custo de bateria para um caminho."""
    return (len(path) - 1) * 2  # 2% por movimento


def calculate_route_cost(from_pos, to_pos):
    """Calcula custo de bateria para ir de uma posição a outra."""
    graph = build_graph_from_matrix(matriz2)
    path = a_star(graph, from_pos, to_pos)
    if path:
        return estimate_battery_cost(path)
    return float('inf')  # Sem caminho


def invalidate_battery_cache():
    """Invalida o cache de bateria necessária."""
    global cached_target_battery
    cached_target_battery = None


def calculate_needed_battery():
    """
    Calcula dinamicamente quanta bateria o robô precisa para as próximas ações.
    Simula as próximas 2 ações e calcula o custo total + retorno à estação.
    Retorna: bateria necessária (mínimo 30%, máximo 100%)
    
    Usa cache para evitar recalcular constantemente.
    """
    global cached_target_battery, last_battery_calculation_time
    
    current_time = pygame.time.get_ticks()
    
    # Se calculou recentemente (< 1 segundo), usa cache (sem log para evitar poluição)
    if cached_target_battery is not None and (current_time - last_battery_calculation_time) < 1000:
        return cached_target_battery
    
    robot_pos = tuple(robot_grid_pos)
    items, warehouses, recharge_stations = find_all_positions()
    
    SAFETY_MARGIN = 8  # Margem de segurança reduzida (era 15%)
    MIN_BATTERY = 20  # Mínimo de bateria reduzido (era 30%)
    
    log("=== CALCULANDO BATERIA NECESSÁRIA ===", "RECHARGE")
    
    # Se não há estações de recarga, retorna 100%
    if not recharge_stations:
        log("Sem estações de recarga, recarregando até 100%", "RECHARGE")
        return 100
    
    nearest_recharge = find_nearest(robot_pos, recharge_stations)
    total_cost = 0
    simulated_pos = robot_pos
    actions_simulated = 0
    max_actions_to_simulate = 4  # Aumentado de 2 para 4 ações
    
    # Simula as próximas ações
    while actions_simulated < max_actions_to_simulate:
        # Verifica o que o robô faria a partir da posição simulada
        
        # Se tem itens no inventário ou capacidade cheia, vai entregar
        if len(robot_inventory) >= ROBOT_CAPACITY or (len(robot_inventory) > 0 and not items):
            if warehouses:
                nearest_warehouse = find_nearest(simulated_pos, warehouses)
                cost = calculate_route_cost(simulated_pos, nearest_warehouse)
                if cost != float('inf'):
                    total_cost += cost
                    simulated_pos = nearest_warehouse
                    log(f"  Ação {actions_simulated + 1}: Entregar em {nearest_warehouse} (custo: {cost:.1f}%)", "RECHARGE")
                    actions_simulated += 1
                    # Após entregar, inventário fica vazio (simulação)
                    if actions_simulated < max_actions_to_simulate and items:
                        continue
                    else:
                        break
                else:
                    break
        # Se não tem itens, vai coletar
        elif items and len(robot_inventory) < ROBOT_CAPACITY:
            nearest_item = find_nearest(simulated_pos, items)
            cost = calculate_route_cost(simulated_pos, nearest_item)
            if cost != float('inf'):
                total_cost += cost
                simulated_pos = nearest_item
                log(f"  Ação {actions_simulated + 1}: Coletar em {nearest_item} (custo: {cost:.1f}%)", "RECHARGE")
                actions_simulated += 1
            else:
                break
        else:
            # Não há mais ações a fazer
            break
    
    # Calcula custo para voltar à estação de recarga da posição final simulada
    cost_back_to_recharge = calculate_route_cost(simulated_pos, nearest_recharge)
    if cost_back_to_recharge != float('inf'):
        total_cost += cost_back_to_recharge
        log(f"  Retorno à estação de {simulated_pos} -> {nearest_recharge} (custo: {cost_back_to_recharge:.1f}%)", "RECHARGE")
    
    # Bateria necessária = custo total + margem de segurança
    needed_battery = total_cost + SAFETY_MARGIN
    
    # Garante mínimo e máximo
    needed_battery = max(needed_battery, MIN_BATTERY)
    needed_battery = min(needed_battery, 100)
    
    log(f"  Total de {actions_simulated} ações simuladas", "RECHARGE")
    log(f"  Custo total estimado: {total_cost:.1f}%", "RECHARGE")
    log(f"  Bateria necessária (com margem): {needed_battery:.1f}%", "RECHARGE")
    
    # Atualiza cache
    cached_target_battery = needed_battery
    last_battery_calculation_time = current_time
    
    return needed_battery


def decide_next_action_intelligent():
    """
    Decide a próxima ação de forma inteligente para modo semi-automático.
    Considera custos de bateria e planeja antecipadamente.
    Retorna: ('action_type', target_pos, description) ou None
    """
    robot_pos = tuple(robot_grid_pos)
    items, warehouses, recharge_stations = find_all_positions()
    graph = build_graph_from_matrix(matriz2)
    
    SAFETY_MARGIN = 6  # Margem de segurança reduzida (era 10%)
    
    log("=== ANÁLISE INTELIGENTE (MODO SEMI-AUTOMÁTICO) ===", "DECISION")
    log(f"Estado atual: Posição: ({robot_pos[0]}, {robot_pos[1]}), Bateria: {battery:.1f}%, Inventário: {len(robot_inventory)}/{ROBOT_CAPACITY}, Itens restantes: {len(items)}", "DECISION")
    
    # Caso 1: Está no almoxarifado com itens -> ENTREGA
    if is_at_warehouse() and len(robot_inventory) > 0:
        log(f"Decisão: ENTREGAR (já está no almoxarifado com {len(robot_inventory)} itens)", "DECISION")
        return ('deliver', robot_pos, 'Entregar itens no almoxarifado')
    
    # Caso 2: Está na estação de recarga com bateria baixa -> RECARGA
    # No modo automático total, calcula dinamicamente. No manual/semi, até 100%
    if auto_mode == AUTO_MODE_FULL:
        target_battery = calculate_needed_battery()
    else:
        target_battery = 100
    
    if is_at_recharge_station() and battery < target_battery:
        log(f"Decisão: RECARREGAR (já está na estação, bateria: {battery:.1f}%, alvo: {target_battery}%)", "DECISION")
        return ('recharge', robot_pos, 'Recarregar bateria na estação')
    
    # Caso 3: Bateria crítica (< 20%) -> PRIORIDADE MÁXIMA: IR RECARREGAR
    if battery < 20:
        if not recharge_stations:
            log("ERRO: Bateria crítica mas não há estações de recarga!", "ERROR")
            return None
        nearest_recharge = find_nearest(robot_pos, recharge_stations)
        if nearest_recharge:
            cost_to_recharge = calculate_route_cost(robot_pos, nearest_recharge)
            if battery >= cost_to_recharge + SAFETY_MARGIN:
                log(f"Decisão: RECARREGAR (bateria crítica: {battery:.1f}%, custo: {cost_to_recharge:.1f}%)", "DECISION")
                return ('recharge', nearest_recharge, f'Bateria crítica ({battery:.1f}%), indo recarregar')
            else:
                # EMERGÊNCIA: Bateria insuficiente para chegar à estação
                # Tenta mover-se o máximo possível em direção à estação
                log(f"🚨 EMERGÊNCIA: Bateria insuficiente para chegar à estação! Bateria: {battery:.1f}%, Custo: {cost_to_recharge:.1f}%", "ERROR")
                log(f"🚨 Tentando movimento de emergência: mover-se na direção da estação o máximo possível", "DECISION")
                # Calcula caminho e retorna mesmo sem bateria suficiente
                return ('recharge', nearest_recharge, f'EMERGÊNCIA: Tentando chegar à estação (bateria: {battery:.1f}%)')
    
    # Caso 4: Tem itens no inventário -> ANALISAR SE DEVE ENTREGAR OU COLETAR MAIS
    if len(robot_inventory) > 0:
        log(f"Análise: Robô com {len(robot_inventory)} itens no inventário", "DECISION")
        
        if not warehouses:
            log("ERRO: Tem itens mas não há almoxarifados!", "ERROR")
            return None
        
        nearest_warehouse = find_nearest(robot_pos, warehouses)
        cost_to_warehouse = calculate_route_cost(robot_pos, nearest_warehouse)
        
        # Calcular custo para ir ao almoxarifado e depois à estação de recarga
        nearest_recharge = find_nearest(nearest_warehouse, recharge_stations) if recharge_stations else None
        cost_warehouse_to_recharge = calculate_route_cost(nearest_warehouse, nearest_recharge) if nearest_recharge else 0
        
        total_cost_deliver = cost_to_warehouse + cost_warehouse_to_recharge
        
        log(f"  - Custo para ir ao almoxarifado: {cost_to_warehouse:.1f}%", "DECISION")
        log(f"  - Custo almoxarifado -> estação: {cost_warehouse_to_recharge:.1f}%", "DECISION")
        log(f"  - Custo total (entregar + poder recarregar): {total_cost_deliver:.1f}%", "DECISION")
        
        # Se bateria não é suficiente para entregar E depois recarregar, PRECISA RECARREGAR ANTES
        if battery < total_cost_deliver + SAFETY_MARGIN:
            log(f"  - Bateria insuficiente ({battery:.1f}% < {total_cost_deliver + SAFETY_MARGIN:.1f}%) para entregar e depois recarregar!", "DECISION")
            log(f"  - Decisão: RECARREGAR ANTES de entregar", "DECISION")
            
            if nearest_recharge:
                cost_to_recharge = calculate_route_cost(robot_pos, nearest_recharge)
                if battery >= cost_to_recharge + SAFETY_MARGIN:
                    return ('recharge', nearest_recharge, 'Recarregar antes de entregar (bateria insuficiente)')
                else:
                    # Situação crítica: tem itens mas não tem bateria nem para recarregar
                    # Verifica se pelo menos pode entregar os itens primeiro
                    if battery >= cost_to_warehouse + SAFETY_MARGIN:
                        log(f"⚠️ DECISÃO DE EMERGÊNCIA: Entregar itens primeiro (bateria: {battery:.1f}%)", "DECISION")
                        return ('deliver', nearest_warehouse, f'EMERGÊNCIA: Entregar antes de ficar sem bateria')
                    else:
                        log(f"🚨 EMERGÊNCIA CRÍTICA: Bateria muito baixa! Tentando mover-se em direção à estação", "ERROR")
                        return ('recharge', nearest_recharge, f'EMERGÊNCIA: Tentando chegar à estação (bateria: {battery:.1f}%)')
        
        # Se inventário está cheio, DEVE ENTREGAR
        if len(robot_inventory) >= ROBOT_CAPACITY:
            log(f"  - Inventário cheio ({len(robot_inventory)}/{ROBOT_CAPACITY}), decisão: ENTREGAR", "DECISION")
            return ('deliver', nearest_warehouse, 'Inventário cheio, entregar itens')
        
        # Se inventário não está cheio, AVALIAR SE DEVE COLETAR MAIS OU ENTREGAR
        if items:
            nearest_item = find_nearest(robot_pos, items)
            cost_to_item = calculate_route_cost(robot_pos, nearest_item)
            
            # OTIMIZAÇÃO: Se já está na célula com item, custo é 0!
            if robot_pos == nearest_item:
                log(f"  - ✅ OTIMIZAÇÃO: Robô já está na célula com item! Custo de coleta: 0%", "DECISION")
                log(f"  - Decisão: COLETAR item adicional (mesma célula, sem custo)", "DECISION")
                return ('collect', nearest_item, f'Coletar item na mesma célula (0% bateria)')
            
            # Calcular custo total: coletar item -> ir ao almoxarifado -> ir à estação
            cost_item_to_warehouse = calculate_route_cost(nearest_item, nearest_warehouse)
            total_cost_collect = cost_to_item + cost_item_to_warehouse + cost_warehouse_to_recharge
            
            log(f"  - Custo para coletar mais item: {cost_to_item:.1f}%", "DECISION")
            log(f"  - Custo total (coletar + entregar + recarregar): {total_cost_collect:.1f}%", "DECISION")
            
            # Se tem bateria para coletar mais, COLETA (margem reduzida)
            if battery >= total_cost_collect + SAFETY_MARGIN:
                log(f"  - Decisão: COLETAR mais item (bateria suficiente: {battery:.1f}%)", "DECISION")
                return ('collect', nearest_item, f'Coletar mais item (inventário: {len(robot_inventory)}/{ROBOT_CAPACITY})')
            # OTIMIZAÇÃO: Se o custo é baixo e tem mais de 20%, arrisca coletar
            elif cost_to_item <= 6 and battery >= 20:
                log(f"  - ✅ OTIMIZAÇÃO: Item próximo ({cost_to_item:.1f}%) e bateria razoável ({battery:.1f}%), decisão: COLETAR", "DECISION")
                return ('collect', nearest_item, f'Coletar item próximo')
            else:
                # Não tem bateria para coletar mais, ENTREGA O QUE TEM
                log(f"  - Decisão: ENTREGAR itens atuais (bateria insuficiente para coletar mais)", "DECISION")
                return ('deliver', nearest_warehouse, f'Entregar {len(robot_inventory)} itens')
        else:
            # Não há mais itens para coletar, ENTREGA O QUE TEM
            log(f"  - Não há mais itens, decisão: ENTREGAR", "DECISION")
            return ('deliver', nearest_warehouse, f'Entregar últimos {len(robot_inventory)} itens')
    
    # Caso 5: Inventário vazio -> COLETAR ITENS
    if len(robot_inventory) == 0 and items:
        log("Análise: Inventário vazio, procurando itens para coletar", "DECISION")
        
        nearest_item = find_nearest(robot_pos, items)
        cost_to_item = calculate_route_cost(robot_pos, nearest_item)
        
        if not warehouses:
            log("ERRO: Não há almoxarifados para entregar depois!", "ERROR")
            return None
        
        nearest_warehouse = find_nearest(nearest_item, warehouses)
        cost_item_to_warehouse = calculate_route_cost(nearest_item, nearest_warehouse)
        
        nearest_recharge = find_nearest(nearest_warehouse, recharge_stations) if recharge_stations else None
        cost_warehouse_to_recharge = calculate_route_cost(nearest_warehouse, nearest_recharge) if nearest_recharge else 0
        
        total_cost = cost_to_item + cost_item_to_warehouse + cost_warehouse_to_recharge
        
        log(f"  - Custo para coletar item: {cost_to_item:.1f}%", "DECISION")
        log(f"  - Custo item -> almoxarifado: {cost_item_to_warehouse:.1f}%", "DECISION")
        log(f"  - Custo almoxarifado -> estação: {cost_warehouse_to_recharge:.1f}%", "DECISION")
        log(f"  - Custo total: {total_cost:.1f}%", "DECISION")
        
        # Se tem bateria para coletar, entregar e recarregar, COLETA
        if battery >= total_cost + SAFETY_MARGIN:
            log(f"  - Decisão: COLETAR item (bateria suficiente: {battery:.1f}%)", "DECISION")
            return ('collect', nearest_item, 'Coletar item')
        else:
            # Bateria insuficiente, verifica se precisa recarregar
            # Se já está na estação de recarga, verifica se tem bateria suficiente
            if is_at_recharge_station():
                needed_battery = calculate_needed_battery()
                
                # OTIMIZAÇÃO: Se tem mais de 25%, tenta coletar (ser menos conservador)
                if battery >= 25 and battery >= needed_battery * 0.85:
                    log(f"  - ✅ Na estação com bateria razoável ({battery:.1f}% >= 25%), decisão: COLETAR", "DECISION")
                    return ('collect', nearest_item, 'Coletar item (bateria razoável)')
                elif battery >= needed_battery:
                    log(f"  - Já está na estação com bateria suficiente ({battery:.1f}% >= {needed_battery:.1f}%), decisão: COLETAR", "DECISION")
                    return ('collect', nearest_item, 'Coletar item')
                else:
                    log(f"  - Está na estação mas precisa recarregar mais ({battery:.1f}% < {needed_battery:.1f}%), decisão: RECARREGAR", "DECISION")
                    return ('recharge', robot_pos, 'Recarregar antes de coletar')
            
            # Não está na estação, precisa ir até lá
            log(f"  - Bateria insuficiente ({battery:.1f}% < {total_cost + SAFETY_MARGIN:.1f}%), decisão: RECARREGAR ANTES", "DECISION")
            if nearest_recharge:
                cost_to_recharge = calculate_route_cost(robot_pos, nearest_recharge)
                if battery >= cost_to_recharge + SAFETY_MARGIN:
                    return ('recharge', nearest_recharge, 'Recarregar antes de coletar')
                else:
                    log(f"ERRO: Bateria insuficiente até para recarregar! Bateria: {battery:.1f}%, Custo: {cost_to_recharge:.1f}%", "ERROR")
                    return None
    
    # Caso 6: Todos os itens coletados e entregues -> MISSÃO COMPLETA
    if not items and len(robot_inventory) == 0:
        log("=== MISSÃO COMPLETA! Todos os itens foram coletados e entregues ===", "DECISION")
        return None
    
    log("ATENÇÃO: Nenhuma ação pôde ser decidida com segurança", "DECISION")
    return None


def decide_next_action():
    """
    Decide a próxima ação para modo semi-automático.
    Retorna: ('action_type', target_pos) ou None
    """
    robot_pos = tuple(robot_grid_pos)
    items, warehouses, recharge_stations = find_all_positions()
    current_time = pygame.time.get_ticks()
    
    # Prioridade 0: Se está no almoxarifado com itens, sempre decidir entregar
    # Não precisa calcular rota, já está no local
    if is_at_warehouse() and len(robot_inventory) > 0:
        log(f"Prioridade: Entregar itens (já está no almoxarifado com {len(robot_inventory)} itens)", "DECISION")
        return ('deliver', robot_pos)  # Já está na posição, entrega será automática após 3s
    
    # Prioridade 0.5: Se está na estação de recarga com bateria baixa, sempre decidir recarregar
    # Não precisa calcular rota, já está no local
    if is_at_recharge_station() and battery < 100:
        log(f"Prioridade: Recarregar (já está na estação de recarga, bateria: {battery:.1f}%)", "DECISION")
        return ('recharge', robot_pos)  # Já está na posição, recarga será automática após 3s
    
    # Prioridade 1: Recarregar se bateria muito baixa (< 20%)
    if battery < 20 and recharge_stations:
        # Verifica se já está em uma estação de recarga
        if is_at_recharge_station():
            log("Prioridade: Recarregar (bateria < 20%, já está na estação)", "DECISION")
            return ('recharge', robot_pos)
        nearest_recharge = find_nearest(robot_pos, recharge_stations)
        if nearest_recharge:
            log("Prioridade: Recarregar (bateria < 20%)", "DECISION")
            return ('recharge', nearest_recharge)
    
    # Prioridade 2: Entregar se inventário cheio
    if len(robot_inventory) >= ROBOT_CAPACITY and warehouses:
        # Verifica se já está no almoxarifado
        if is_at_warehouse():
            log("Prioridade: Entregar (inventário cheio, já está no almoxarifado)", "DECISION")
            return ('deliver', robot_pos)
        nearest_warehouse = find_nearest(robot_pos, warehouses)
        if nearest_warehouse:
            log("Prioridade: Entregar (inventário cheio)", "DECISION")
            return ('deliver', nearest_warehouse)
    
    # Prioridade 3: Entregar se tem itens e está muito próximo do almoxarifado
    if len(robot_inventory) > 0 and warehouses:
        # Se já está no almoxarifado, não precisa calcular rota
        if is_at_warehouse():
            log("Prioridade: Entregar (tem itens, já está no almoxarifado)", "DECISION")
            return ('deliver', robot_pos)
        nearest_warehouse = find_nearest(robot_pos, warehouses)
        if nearest_warehouse:
            graph = build_graph_from_matrix(matriz2)
            path = a_star(graph, robot_pos, nearest_warehouse)
            if path and len(path) <= 2:  # Muito próximo (1-2 movimentos)
                log(f"Prioridade: Entregar (muito próximo do almoxarifado, {len(path)-1} passos)", "DECISION")
                return ('deliver', nearest_warehouse)
    
    # Prioridade 4: Coletar itens se houver espaço
    if len(robot_inventory) < ROBOT_CAPACITY and items:
        # Filtra itens que realmente existem e podem ser coletados
        valid_items = []
        for item_pos in items:
            if item_pos in items_on_grid and len(items_on_grid[item_pos]) > 0:
                valid_items.append(item_pos)
        
        if valid_items:
            nearest_item = find_nearest(robot_pos, valid_items)
            if nearest_item:
                # Se já está na posição do item, pode coletar
                if nearest_item == robot_pos:
                    if (nearest_item in items_on_grid and 
                        len(items_on_grid[nearest_item]) > 0 and
                        len(robot_inventory) < ROBOT_CAPACITY):
                        log("Prioridade: Coletar (já está na posição do item)", "DECISION")
                        return ('collect', nearest_item)
                else:
                    # Verifica se tem bateria suficiente para ir até o item
                    graph = build_graph_from_matrix(matriz2)
                    path = a_star(graph, robot_pos, nearest_item)
                    if path:
                        battery_cost = estimate_battery_cost(path)
                        if battery >= battery_cost + 10:  # Deixa margem de segurança
                            log(f"Prioridade: Coletar item em ({nearest_item[0]}, {nearest_item[1]})", "DECISION")
                            return ('collect', nearest_item)
    
    # Prioridade 5: Recarregar se bateria baixa (< 30%) e não há itens para coletar
    if battery < 30 and recharge_stations and len(robot_inventory) == 0:
        # Verifica se já está em uma estação de recarga
        if is_at_recharge_station():
            log("Prioridade: Recarregar (bateria < 30%, já está na estação)", "DECISION")
            return ('recharge', robot_pos)
        nearest_recharge = find_nearest(robot_pos, recharge_stations)
        if nearest_recharge:
            log("Prioridade: Recarregar (bateria < 30%, sem itens)", "DECISION")
            return ('recharge', nearest_recharge)
    
    # Prioridade 6: Entregar se tem itens (última opção)
    if len(robot_inventory) > 0 and warehouses:
        # Se já está no almoxarifado, não precisa calcular rota
        if is_at_warehouse():
            log("Prioridade: Entregar (tem itens, já está no almoxarifado)", "DECISION")
            return ('deliver', robot_pos)
        nearest_warehouse = find_nearest(robot_pos, warehouses)
        if nearest_warehouse:
            log("Prioridade: Entregar (tem itens)", "DECISION")
            return ('deliver', nearest_warehouse)
    
    # Prioridade 7: Recarregar se bateria não está cheia e há estações disponíveis
    if battery < 100 and recharge_stations:
        # Se já está em uma estação de recarga, não precisa calcular rota
        if is_at_recharge_station():
            log(f"Prioridade: Recarregar (bateria: {battery:.1f}%, já está na estação)", "DECISION")
            return ('recharge', robot_pos)
        nearest_recharge = find_nearest(robot_pos, recharge_stations)
        if nearest_recharge:
            log(f"Prioridade: Recarregar (bateria: {battery:.1f}%)", "DECISION")
            return ('recharge', nearest_recharge)
    
    # Se chegou aqui, realmente não há trabalho a fazer
    # Verifica se todos os itens foram coletados
    if not items and len(robot_inventory) == 0:
        log("Nenhuma ação disponível: Todos os itens foram coletados e entregues!", "DECISION")
    else:
        log(f"Nenhuma ação disponível: Itens restantes: {len(items)}, Inventário: {len(robot_inventory)}, Bateria: {battery:.1f}%", "DECISION")
    return None


def plan_full_mission():
    """
    Planeja missão completa para modo automático total.
    Retorna lista de ações: [('action_type', target_pos), ...]
    """
    log("Iniciando planejamento de missão completa...", "PLAN")
    mission_plan = []
    current_pos = tuple(robot_grid_pos)
    current_battery = battery
    remaining_items = list(items_on_grid.keys())
    graph = build_graph_from_matrix(matriz2)
    items, warehouses, recharge_stations = find_all_positions()
    
    log(f"Itens restantes para coletar: {len(remaining_items)}", "PLAN")
    log(f"Bateria atual: {current_battery}%", "PLAN")
    
    trip_number = 1
    while remaining_items:
        # Verifica se precisa recarregar antes de continuar
        if current_battery < 30 and recharge_stations:
            nearest_recharge = find_nearest(current_pos, recharge_stations)
            if nearest_recharge:
                path = a_star(graph, current_pos, nearest_recharge)
                if path:
                    log(f"Viagem {trip_number}: Recarga planejada em ({nearest_recharge[0]}, {nearest_recharge[1]}) - Bateria: {current_battery}%", "PLAN")
                    mission_plan.append(('recharge', nearest_recharge))
                    current_pos = nearest_recharge
                    current_battery = 100
        
        # Coleta itens até encher ou acabar
        items_to_collect = []
        items_collected = 0
        
        while items_collected < ROBOT_CAPACITY and remaining_items:
            nearest_item = find_nearest(current_pos, remaining_items)
            if not nearest_item:
                break
            
            path = a_star(graph, current_pos, nearest_item)
            if not path:
                break
            
            battery_cost = estimate_battery_cost(path)
            if current_battery < battery_cost + 20:  # Precisa recarregar
                break
            
            items_to_collect.append(nearest_item)
            remaining_items.remove(nearest_item)
            items_collected += 1
            current_pos = nearest_item
            current_battery -= battery_cost
        
        # Adiciona ações de coleta
        if items_to_collect:
            log(f"Viagem {trip_number}: Planejando coleta de {len(items_to_collect)} itens", "PLAN")
            for item_pos in items_to_collect:
                mission_plan.append(('collect', item_pos))
                log(f"  - Coletar item em ({item_pos[0]}, {item_pos[1]})", "PLAN")
        
        # Vai entregar no almoxarifado mais próximo
        if items_to_collect and warehouses:
            nearest_warehouse = find_nearest(current_pos, warehouses)
            if nearest_warehouse:
                path = a_star(graph, current_pos, nearest_warehouse)
                if path:
                    battery_cost = estimate_battery_cost(path)
                    current_battery -= battery_cost
                    log(f"Viagem {trip_number}: Entrega planejada em ({nearest_warehouse[0]}, {nearest_warehouse[1]})", "PLAN")
                    mission_plan.append(('deliver', nearest_warehouse))
                    current_pos = nearest_warehouse
                    trip_number += 1
    
    log(f"Planejamento completo! Total de ações: {len(mission_plan)}", "PLAN")
    return mission_plan


def execute_auto_action():
    """Executa a próxima ação automática."""
    global current_path, current_path_index, current_action, waiting_for_action, auto_mode, just_collected, action_completed
    
    if not current_path:
        return
    
    # CRÍTICO: Só executa ações se a animação estiver completa
    if not is_animation_complete():
        return  # Aguarda animação completar antes de executar qualquer ação
    
    # Se ainda está seguindo um caminho
    if current_path_index < len(current_path):
        next_pos = current_path[current_path_index]
        
        # VALIDAÇÃO CRÍTICA: Verifica se o próximo passo não é um obstáculo
        if (0 <= next_pos[0] < len(matriz2[0]) and 0 <= next_pos[1] < len(matriz2)):
            cell_type = matriz2[next_pos[1]][next_pos[0]]
            if cell_type == '0':
                # Próximo passo é um obstáculo! Aborta o caminho
                log(f"🚫 ERRO CRÍTICO: Próximo passo é OBSTÁCULO em ({next_pos[0]}, {next_pos[1]})! Abortando.", "ERROR")
                current_action = None
                current_path = []
                current_path_index = 0
                waiting_for_action = False
                if auto_mode == AUTO_MODE_FULL:
                    action_completed = True
                return
            else:
                log(f"✓ Validação: próximo passo ({next_pos[0]}, {next_pos[1]}) é válido (tipo: {cell_type})", "AUTO")
        
        # Move o robô na direção do próximo passo
        current_x, current_y = robot_grid_pos
        target_x, target_y = next_pos
        
        # Valida que o movimento é válido (apenas 1 célula de distância)
        dx = abs(target_x - current_x)
        dy = abs(target_y - current_y)
        if dx + dy != 1:
            log(f"ERRO: Movimento inválido de ({current_x}, {current_y}) para ({target_x}, {target_y}) - distância incorreta!", "ERROR")
            current_action = None
            current_path = []
            current_path_index = 0
            waiting_for_action = False
            if auto_mode == AUTO_MODE_FULL:
                action_completed = True
            return
        
        # Tenta mover
        old_pos = robot_grid_pos.copy()
        if target_x > current_x:
            move_robot('mr')
        elif target_x < current_x:
            move_robot('ml')
        elif target_y > current_y:
            move_robot('md')
        elif target_y < current_y:
            move_robot('mu')
        
        # Verifica se o movimento foi bem-sucedido
        if robot_grid_pos == old_pos:
            # Movimento falhou (provavelmente obstáculo ou bateria)
            log(f"Movimento falhou de ({old_pos[0]}, {old_pos[1]}) para ({target_x}, {target_y})", "ERROR")
            current_action = None
            current_path = []
            current_path_index = 0
            waiting_for_action = False
            if auto_mode == AUTO_MODE_FULL:
                action_completed = True
            return
        
        # Verifica se chegou na posição
        if robot_grid_pos[0] == target_x and robot_grid_pos[1] == target_y:
            current_path_index += 1
        else:
            # Robô não chegou na posição esperada - algo deu errado
            log(f"ERRO: Robô não chegou na posição esperada. Esperado: ({target_x}, {target_y}), Atual: ({robot_grid_pos[0]}, {robot_grid_pos[1]})", "ERROR")
            current_action = None
            current_path = []
            current_path_index = 0
            waiting_for_action = False
            if auto_mode == AUTO_MODE_FULL:
                action_completed = True
            return
    
    # Se completou o caminho, executa a ação
    if current_path_index >= len(current_path) and current_path:
        if current_action == 'collect':
            # Verifica se realmente chegou na posição alvo do caminho
            target_pos = current_path[-1] if current_path else tuple(robot_grid_pos)
            
            # Coleta se está na posição correta e tem item
            if (tuple(robot_grid_pos) == target_pos and
                tuple(robot_grid_pos) in items_on_grid and 
                len(items_on_grid[tuple(robot_grid_pos)]) > 0 and
                len(robot_inventory) < ROBOT_CAPACITY):
                log(f"✓ Validação de coleta: Robô NA célula ({robot_grid_pos[0]}, {robot_grid_pos[1]}) = Item alvo ({target_pos[0]}, {target_pos[1]})", "AUTO")
                collect_item(1)
                log(f"Ação automática COMPLETA: Coleta em ({robot_grid_pos[0]}, {robot_grid_pos[1]})", "AUTO")
                just_collected = True  # Marca que acabou de coletar
                
                # Modo semi-automático: desativa após coletar
                if auto_mode == AUTO_MODE_SEMI:
                    current_action = None
                    current_path = []
                    current_path_index = 0
                    waiting_for_action = False
                    auto_mode = AUTO_MODE_OFF
                    log("=== AÇÃO SEMI-AUTOMÁTICA COMPLETA: Coleta finalizada ===", "AUTO")
                    log("Modo semi-automático DESATIVADO. Ative novamente ('S') para próxima ação.", "AUTO")
                    return
                # Modo automático total: marca ação completa e registra tempo
                elif auto_mode == AUTO_MODE_FULL:
                    current_action = None
                    current_path = []
                    current_path_index = 0
                    waiting_for_action = False
                    last_action_time = pygame.time.get_ticks()  # Marca tempo para delay de 300ms
                    invalidate_battery_cache()  # Invalida cache para recalcular bateria necessária
                    log("=== AÇÃO AUTOMÁTICA COMPLETA: Coleta finalizada ===", "AUTO")
                    return
            else:
                log(f"Ação automática FALHOU: Não é possível coletar em ({target_pos[0]}, {target_pos[1]}) - Posição atual: ({robot_grid_pos[0]}, {robot_grid_pos[1]}), Itens: {tuple(robot_grid_pos) in items_on_grid}, Inventário: {len(robot_inventory)}/{ROBOT_CAPACITY}", "ERROR")
                # Se falhou, limpa e marca tempo
                if auto_mode == AUTO_MODE_FULL:
                    current_action = None
                    current_path = []
                    current_path_index = 0
                    waiting_for_action = False
                    last_action_time = pygame.time.get_ticks()
                elif auto_mode == AUTO_MODE_SEMI:
                    auto_mode = AUTO_MODE_OFF
                    current_action = None
                    current_path = []
                    current_path_index = 0
                    waiting_for_action = False
                    log("Modo semi-automático DESATIVADO devido a falha na coleta.", "AUTO")
                return
            waiting_for_action = False
        
        elif current_action == 'deliver':
            # Entrega será automática quando chegar no almoxarifado
            # Define waiting_for_action para aguardar o sistema automático de entrega
            if not waiting_for_action:
                waiting_for_action = True
                current_path = []
                current_path_index = 0
                log(f"Robô chegou ao almoxarifado, aguardando entrega automática...", "AUTO")
            # Aguarda entrega completar
            elif len(robot_inventory) == 0:
                log(f"Ação automática COMPLETA: Entrega em ({robot_grid_pos[0]}, {robot_grid_pos[1]})", "AUTO")
                if auto_mode == AUTO_MODE_FULL:
                    action_completed = True
                current_action = None
                current_path = []
                current_path_index = 0
                waiting_for_action = False
        
        elif current_action == 'recharge':
            # Recarga será automática quando chegar na estação
            # Define waiting_for_action para aguardar o sistema automático de recarga
            if not waiting_for_action:
                waiting_for_action = True
                current_path = []
                current_path_index = 0
                log(f"Robô chegou à estação de recarga, aguardando recarga automática...", "AUTO")
            # A limpeza do estado é feita em update_auto_recharge() quando atingir target
            # Não precisa verificar aqui para evitar condição de corrida


def update_auto_mode():
    """Atualiza o modo automático."""
    global auto_mode, current_path, current_path_index, current_action, waiting_for_action, just_collected, action_completed, last_action_time
    
    if auto_mode == AUTO_MODE_OFF:
        return
    
    # CRÍTICO: Se a animação não estiver completa, não processa novas ações
    # Isso garante que o robô visualmente chegue na posição antes de coletar/entregar
    if not is_animation_complete():
        return  # Aguarda animação completar
    
    # Debug: log quando entra em update_auto_mode no modo semi-automático
    if auto_mode == AUTO_MODE_SEMI and not current_path and not waiting_for_action:
        log(f"[DEBUG] update_auto_mode: Modo SEMI, sem caminho ativo, decidindo próxima ação...", "AUTO")
    
    # Se acabou de coletar, aguarda uma iteração antes de processar próxima ação
    if just_collected:
        just_collected = False
        return
    
    # Se está esperando ação completar (entrega ou recarga)
    if waiting_for_action:
        # Modo semi-automático: desativa após completar ação
        if auto_mode == AUTO_MODE_SEMI:
            if current_action == 'deliver' and len(robot_inventory) == 0:
                waiting_for_action = False
                current_action = None
                current_path = []
                current_path_index = 0
                auto_mode = AUTO_MODE_OFF
                log("=== AÇÃO SEMI-AUTOMÁTICA COMPLETA: Entrega finalizada ===", "AUTO")
                log("Modo semi-automático DESATIVADO. Ative novamente ('S') para próxima ação.", "AUTO")
                return
            elif current_action == 'recharge' and battery >= 100:
                waiting_for_action = False
                current_action = None
                current_path = []
                current_path_index = 0
                auto_mode = AUTO_MODE_OFF
                log("=== AÇÃO SEMI-AUTOMÁTICA COMPLETA: Recarga finalizada ===", "AUTO")
                log("Modo semi-automático DESATIVADO. Ative novamente ('S') para próxima ação.", "AUTO")
                return
            else:
                return  # Continua esperando
        # Modo automático total: ações completadas pelas funções update_auto_recharge e update_auto_delivery
        elif auto_mode == AUTO_MODE_FULL:
            return  # Continua esperando, as ações setam waiting_for_action = False quando completam
    
    # Se não há caminho ativo, planeja próxima ação
    if not current_path:
        if auto_mode == AUTO_MODE_FULL:
            # Modo automático total: funciona como sequência de ações semi-automáticas com delay
            current_time = pygame.time.get_ticks()
            
            # Verifica se passou tempo suficiente desde a última ação (delay de 300ms)
            if last_action_time > 0 and (current_time - last_action_time) < AUTO_ACTION_DELAY:
                return  # Aguarda delay entre ações
            
            log("=== DECIDINDO PRÓXIMA AÇÃO (MODO AUTOMÁTICO TOTAL) ===", "AUTO")
            
            # Verifica se missão está completa
            items_remaining = sum(len(items) for items in items_on_grid.values())
            if items_remaining == 0 and len(robot_inventory) == 0:
                log("=== MISSÃO COMPLETA! Todos os itens foram entregues. ===", "AUTO")
                auto_mode = AUTO_MODE_OFF
                return
            
            # Usa lógica inteligente de decisão (igual ao modo semi-automático)
            decision = decide_next_action_intelligent()
            
            if decision:
                action_type, target_pos, description = decision
                log(f"Decisão automática: {description}", "AUTO")
                
                graph = build_graph_from_matrix(matriz2)
                path = a_star(graph, tuple(robot_grid_pos), target_pos)
                
                # Valida o caminho antes de usar
                if path and not validate_path(path):
                    log(f"🚫 ERRO: Caminho inválido calculado para {action_type}! Abortando ação.", "ERROR")
                    last_action_time = current_time  # Marca tempo para tentar novamente após delay
                    return
                
                if path:
                    if len(path) == 1:
                        # Já está na posição alvo
                        if action_type in ['deliver', 'recharge']:
                            # Para entrega e recarga, pode executar imediatamente
                            current_path = []
                            current_path_index = 0
                            current_action = action_type
                            waiting_for_action = True
                            log(f"Iniciando {action_type} imediatamente (já está no local)", "AUTO")
                        else:
                            # Para coleta, também executa diretamente (já está na posição)
                            current_path = []
                            current_path_index = 0
                            current_action = None
                            
                            # Coleta imediatamente se tiver item
                            if (tuple(robot_grid_pos) in items_on_grid and 
                                len(items_on_grid[tuple(robot_grid_pos)]) > 0 and
                                len(robot_inventory) < ROBOT_CAPACITY):
                                log(f"✓ Robô já está na célula do item ({robot_grid_pos[0]}, {robot_grid_pos[1]}), coletando diretamente", "AUTO")
                                collect_item(1)
                                last_action_time = current_time
                                log("=== AÇÃO AUTOMÁTICA COMPLETA: Coleta finalizada ===", "AUTO")
                            else:
                                log(f"⚠️ AVISO: Robô na posição mas sem item para coletar", "AUTO")
                                last_action_time = current_time
                    else:
                        # Remove posição atual e valida o caminho restante
                        remaining_path = path[1:]
                        if not validate_path(remaining_path):
                            log(f"🚫 ERRO: Caminho restante inválido! Abortando ação.", "ERROR")
                            last_action_time = current_time
                            return
                        
                        current_path = remaining_path
                        current_path_index = 0
                        current_action = action_type
                        log(f"Executando ação: {action_type} -> ({target_pos[0]}, {target_pos[1]}) | {len(path)} passos", "AUTO")
                else:
                    log(f"🚫 ERRO: Não foi possível encontrar caminho para {action_type}", "ERROR")
                    last_action_time = current_time
            else:
                log("⚠️ AVISO: Nenhuma ação decidida. Robô aguardando...", "AUTO")
                last_action_time = current_time
        
        elif auto_mode == AUTO_MODE_SEMI:
            # Modo semi-automático inteligente: decide próxima ação com análise de bateria
            action = decide_next_action_intelligent()
            if action:
                action_type, target_pos, description = action
                log(f"=== AÇÃO SEMI-AUTOMÁTICA INICIADA: {description} ===", "AUTO")
                
                # Se já está na posição alvo para entregar ou recarregar, não precisa calcular rota
                if action_type in ['deliver', 'recharge'] and tuple(robot_grid_pos) == target_pos:
                    # Já está no local necessário, apenas aguarda a ação automática
                    current_path = []
                    current_path_index = 0
                    current_action = action_type
                    waiting_for_action = True
                    log(f"Ação (Semi-Auto): {action_type} - já está no local, aguardando ação automática", "AUTO")
                else:
                    # Precisa se mover até o alvo
                    graph = build_graph_from_matrix(matriz2)
                    path = a_star(graph, tuple(robot_grid_pos), target_pos)
                    
                    # Valida o caminho antes de usar
                    if path and not validate_path(path):
                        log(f"ERRO: Caminho inválido calculado para {action_type} -> ({target_pos[0]}, {target_pos[1]})! Abortando ação.", "ERROR")
                        auto_mode = AUTO_MODE_OFF
                        log("Modo semi-automático DESATIVADO devido a erro.", "AUTO")
                        return
                    
                    if path:
                        # Se já está na posição alvo, cria caminho mínimo para garantir que "passe" pela célula
                        if len(path) == 1:
                            # Já está na posição - cria caminho mínimo
                            if action_type == 'collect':
                                # Tenta encontrar uma célula adjacente livre para fazer o movimento
                                x, y = target_pos
                                adjacent_found = False
                                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                                    nx, ny = x + dx, y + dy
                                    if (0 <= nx < len(matriz2[0]) and 0 <= ny < len(matriz2) and
                                        matriz2[ny][nx] != '0'):
                                        # Cria caminho: posição atual -> adjacente -> posição alvo
                                        min_path = [(nx, ny), target_pos]
                                        # Valida o caminho mínimo antes de usar
                                        if validate_path(min_path):
                                            current_path = min_path
                                            current_path_index = 0
                                            current_action = action_type
                                            log(f"Criando caminho mínimo (Semi-Auto) para passar pela célula: ({x}, {y}) -> ({nx}, {ny}) -> ({x}, {y})", "AUTO")
                                            adjacent_found = True
                                            break
                                        else:
                                            log(f"ERRO: Caminho mínimo inválido criado (Semi-Auto)! Tentando próxima direção...", "ERROR")
                                
                                if not adjacent_found:
                                    # Não há célula adjacente livre - não pode coletar sem passar pela célula
                                    log(f"Ação automática PULADA (Semi-Auto): Não há célula adjacente livre em ({target_pos[0]}, {target_pos[1]})", "AUTO")
                                    auto_mode = AUTO_MODE_OFF
                                    log("Modo semi-automático DESATIVADO.", "AUTO")
                                    current_action = None
                        else:
                            # Remove posição atual e valida o caminho restante
                            remaining_path = path[1:]
                            if not validate_path(remaining_path):
                                log(f"ERRO: Caminho restante inválido após remover posição atual (Semi-Auto)! Abortando ação.", "ERROR")
                                auto_mode = AUTO_MODE_OFF
                                log("Modo semi-automático DESATIVADO devido a erro.", "AUTO")
                                return
                            current_path = remaining_path
                            current_path_index = 0
                            current_action = action_type
                            log(f"Decisão (Semi-Auto): {action_type} -> ({target_pos[0]}, {target_pos[1]})", "AUTO")
                            log(f"Caminho calculado: {len(path)} passos", "AUTO")
                            # NÃO define waiting_for_action aqui - só define quando chegar ao destino
                            # waiting_for_action será definido em execute_auto_action() quando completar o caminho
                    else:
                        log(f"ERRO: Não foi possível encontrar caminho para {action_type} -> ({target_pos[0]}, {target_pos[1]})", "ERROR")
                        auto_mode = AUTO_MODE_OFF
                        log("Modo semi-automático DESATIVADO devido a erro.", "AUTO")
            else:
                # decide_next_action_intelligent() retornou None
                log("Nenhuma ação pode ser decidida com segurança no momento.", "AUTO")
                auto_mode = AUTO_MODE_OFF
                log("Modo semi-automático DESATIVADO.", "AUTO")
    
    # Executa ação atual
    if current_path:
        log(f"[DEBUG] Executando ação: current_path={current_path}, current_path_index={current_path_index}, current_action={current_action}", "AUTO")
        execute_auto_action()
    elif auto_mode == AUTO_MODE_SEMI:
        log(f"[DEBUG] Modo semi-automático ativo mas sem caminho! waiting_for_action={waiting_for_action}, current_action={current_action}", "AUTO")


def is_animation_complete():
    """Verifica se a animação do robô está completa (posição visual = posição lógica)."""
    target_x = robot_grid_pos[0] * CELL_SIZE
    target_y = robot_grid_pos[1] * CELL_SIZE
    
    # Considera completa se está muito próxima (dentro de ANIMATION_SPEED)
    x_aligned = abs(robot_real_pos[0] - target_x) < ANIMATION_SPEED
    y_aligned = abs(robot_real_pos[1] - target_y) < ANIMATION_SPEED
    
    return x_aligned and y_aligned


def animate_robot():
    """Faz a animação de transição suave do robô entre os nós."""
    target_x = robot_grid_pos[0] * CELL_SIZE
    target_y = robot_grid_pos[1] * CELL_SIZE

    if robot_real_pos[0] < target_x:
        robot_real_pos[0] += ANIMATION_SPEED
    elif robot_real_pos[0] > target_x:
        robot_real_pos[0] -= ANIMATION_SPEED

    if robot_real_pos[1] < target_y:
        robot_real_pos[1] += ANIMATION_SPEED
    elif robot_real_pos[1] > target_y:
        robot_real_pos[1] -= ANIMATION_SPEED


def draw_side_panel():
    """Desenha o painel lateral direito com todas as informações do jogo."""
    global panel_max_scroll
    
    panel_x = GRID_WIDTH
    panel_y = 0
    panel_bg_color = (30, 30, 40)  # Azul escuro
    panel_border_color = (100, 100, 120)
    
    # Desenha fundo do painel
    pygame.draw.rect(screen, panel_bg_color, (panel_x, panel_y, PANEL_WIDTH, HEIGHT))
    pygame.draw.line(screen, panel_border_color, (panel_x, 0), (panel_x, HEIGHT), 3)
    
    # Criar superfície virtual para scroll (altura estimada)
    virtual_height = HEIGHT + 400  # Altura extra para conteúdo
    virtual_surface = pygame.Surface((PANEL_WIDTH, virtual_height), pygame.SRCALPHA)
    virtual_surface.fill((0, 0, 0, 0))  # Transparente
    
    # Posição inicial para textos (na superfície virtual)
    y_offset = 15
    x_margin = 15
    
    # ========== TÍTULO ==========
    title_text = font_small.render("STATUS", True, (255, 255, 255))
    virtual_surface.blit(title_text, (x_margin, y_offset))
    y_offset += 35
    
    # ========== MODO ==========
    if auto_mode == AUTO_MODE_FULL:
        mode_text = "AUTOMÁTICO TOTAL"
        mode_color = GREEN
    elif auto_mode == AUTO_MODE_SEMI:
        mode_text = "SEMI-AUTOMÁTICO"
        mode_color = (255, 200, 0)
    else:
        mode_text = "MANUAL"
        mode_color = WHITE
    
    mode_label = font_tiny.render("Modo:", True, (200, 200, 200))
    virtual_surface.blit(mode_label, (x_margin, y_offset))
    y_offset += 22
    mode_surface = font_tiny.render(mode_text, True, mode_color)
    virtual_surface.blit(mode_surface, (x_margin + 8, y_offset))
    y_offset += 28
    
    # ========== AÇÃO ATUAL ==========
    if auto_mode != AUTO_MODE_OFF and current_action:
        action_label = font_tiny.render("Ação:", True, (200, 200, 200))
        virtual_surface.blit(action_label, (x_margin, y_offset))
        y_offset += 22
        
        action_text = current_action.upper()
        if current_path:
            action_text += f" ({len(current_path) - current_path_index} passos)"
        action_surface = font_tiny.render(action_text, True, mode_color)
        virtual_surface.blit(action_surface, (x_margin + 8, y_offset))
        y_offset += 25
    
    # Linha separadora
    pygame.draw.line(virtual_surface, panel_border_color, (x_margin, y_offset), (PANEL_WIDTH - 15, y_offset), 1)
    y_offset += 15
    
    # ========== BATERIA ==========
    battery_label = font_tiny.render("Bateria:", True, (200, 200, 200))
    virtual_surface.blit(battery_label, (x_margin, y_offset))
    y_offset += 22
    
    # Barra de bateria
    bar_width = PANEL_WIDTH - 40
    bar_height = 20
    bar_x = x_margin + 5
    bar_y = y_offset
    
    # Cor da bateria baseada no nível
    if battery > 60:
        battery_color = GREEN
    elif battery > 30:
        battery_color = (255, 255, 0)  # Amarelo
    else:
        battery_color = RED
    
    # Borda da barra
    pygame.draw.rect(virtual_surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 2)
    # Preenchimento da barra
    fill_width = int((bar_width - 4) * (battery / 100.0))
    pygame.draw.rect(virtual_surface, battery_color, (bar_x + 2, bar_y + 2, fill_width, bar_height - 4))
    
    # Texto da bateria
    battery_text = f"{int(battery)}%"
    battery_surface = font_tiny.render(battery_text, True, WHITE)
    battery_rect = battery_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
    virtual_surface.blit(battery_surface, battery_rect)
    y_offset += 28
    
    # Status de recarga
    if is_recharging:
        battery_needed = 100 - battery_at_recharge_start
        time_needed = (battery_needed / 100.0) * RECHARGE_SPEED
        elapsed_time = (pygame.time.get_ticks() - recharge_start_time) / 1000.0
        time_remaining = max(0, time_needed - elapsed_time)
        
        status_text = f"⚡ Recarregando... ({time_remaining:.1f}s)"
        status_surface = font_tiny.render(status_text, True, GREEN)
        virtual_surface.blit(status_surface, (x_margin + 8, y_offset))
        y_offset += 22
    elif is_at_recharge_station() and not is_recharging and battery < 100:
        wait_time = (pygame.time.get_ticks() - time_at_station) / 1000.0 if time_at_station > 0 else 0
        wait_remaining = max(0, (STATION_WAIT_TIME / 1000.0) - wait_time)
        
        status_text = f"⏳ Aguardando... ({wait_remaining:.1f}s)"
        status_surface = font_tiny.render(status_text, True, (255, 255, 0))
        virtual_surface.blit(status_surface, (x_margin + 8, y_offset))
        y_offset += 22
    
    # Linha separadora
    pygame.draw.line(virtual_surface, panel_border_color, (x_margin, y_offset), (PANEL_WIDTH - 15, y_offset), 1)
    y_offset += 15
    
    # ========== INVENTÁRIO ==========
    inventory_label = font_tiny.render("Inventário:", True, (200, 200, 200))
    virtual_surface.blit(inventory_label, (x_margin, y_offset))
    y_offset += 22
    
    inventory_text = f"{len(robot_inventory)}/{ROBOT_CAPACITY} itens"
    inventory_color = (255, 200, 0) if len(robot_inventory) > 0 else WHITE
    inventory_surface = font_tiny.render(inventory_text, True, inventory_color)
    virtual_surface.blit(inventory_surface, (x_margin + 8, y_offset))
    y_offset += 25
    
    # Status de entrega
    if is_delivering:
        items_remaining = len(robot_inventory)
        status_text = f"📦 Entregando... ({items_remaining} itens)"
        status_surface = font_tiny.render(status_text, True, GREEN)
        virtual_surface.blit(status_surface, (x_margin + 8, y_offset))
        y_offset += 22
    elif is_at_warehouse() and len(robot_inventory) > 0 and not is_delivering:
        wait_time = (pygame.time.get_ticks() - time_at_warehouse) / 1000.0 if time_at_warehouse > 0 else 0
        wait_remaining = max(0, (WAREHOUSE_WAIT_TIME / 1000.0) - wait_time)
        
        status_text = f"⏳ Aguardando... ({wait_remaining:.1f}s)"
        status_surface = font_tiny.render(status_text, True, (255, 200, 0))
        virtual_surface.blit(status_surface, (x_margin + 8, y_offset))
        y_offset += 22
    
    # Linha separadora
    pygame.draw.line(virtual_surface, panel_border_color, (x_margin, y_offset), (PANEL_WIDTH - 15, y_offset), 1)
    y_offset += 15
    
    # ========== ESTATÍSTICAS ==========
    stats_label = font_tiny.render("Estatísticas:", True, (200, 200, 200))
    virtual_surface.blit(stats_label, (x_margin, y_offset))
    y_offset += 22
    
    # Itens entregues
    delivered_text = f"✓ Entregues: {items_delivered_count}"
    delivered_surface = font_tiny.render(delivered_text, True, (150, 255, 150))
    virtual_surface.blit(delivered_surface, (x_margin + 8, y_offset))
    y_offset += 22
    
    # Itens restantes
    items_remaining = sum(len(items) for items in items_on_grid.values())
    remaining_text = f"○ No ambiente: {items_remaining}"
    remaining_surface = font_tiny.render(remaining_text, True, (255, 255, 150))
    virtual_surface.blit(remaining_surface, (x_margin + 8, y_offset))
    y_offset += 25
    
    # Linha separadora
    pygame.draw.line(virtual_surface, panel_border_color, (x_margin, y_offset), (PANEL_WIDTH - 15, y_offset), 1)
    y_offset += 15
    
    # ========== SOM ==========
    sound_icon = "🔊" if SOUND_ENABLED else "🔇"
    sound_status = "Ligado" if SOUND_ENABLED else "Desligado"
    sound_color = (150, 255, 150) if SOUND_ENABLED else (255, 150, 150)
    sound_text = f"{sound_icon} Som: {sound_status}"
    sound_surface = font_tiny.render(sound_text, True, sound_color)
    virtual_surface.blit(sound_surface, (x_margin + 8, y_offset))
    y_offset += 28
    
    # Linha separadora
    pygame.draw.line(virtual_surface, panel_border_color, (x_margin, y_offset), (PANEL_WIDTH - 15, y_offset), 1)
    y_offset += 15
    
    # ========== CONTROLES ==========
    controls_label = font_tiny.render("Controles:", True, (200, 200, 200))
    virtual_surface.blit(controls_label, (x_margin, y_offset))
    y_offset += 22
    
    controls = [
        ("Setas", "Mover robô"),
        ("1/2", "Coletar item"),
        ("A", "Auto Total"),
        ("S", "Semi-Auto"),
        ("R", "Reiniciar"),
        ("M", "Mute/Som"),
        ("T", "Testar Sons"),
    ]
    
    for key, desc in controls:
        key_surface = font_tiny.render(f"{key}:", True, (200, 200, 255))
        virtual_surface.blit(key_surface, (x_margin + 8, y_offset))
        
        desc_surface = font_tiny.render(desc, True, (180, 180, 180))
        virtual_surface.blit(desc_surface, (x_margin + 65, y_offset))
        y_offset += 20
    
    # Total de conteúdo
    total_content_height = y_offset + 20
    
    # Calcula o máximo de scroll
    panel_max_scroll = max(0, total_content_height - HEIGHT)
    
    # Desenha a parte visível da superfície virtual no painel
    visible_area = pygame.Rect(0, panel_scroll_offset, PANEL_WIDTH, HEIGHT)
    screen.blit(virtual_surface, (panel_x, panel_y), visible_area)
    
    # Desenha indicadores de scroll se necessário
    if panel_max_scroll > 0:
        # Seta para cima (se não está no topo)
        if panel_scroll_offset > 0:
            arrow_up = font_tiny.render("▲", True, (200, 200, 255))
            screen.blit(arrow_up, (panel_x + PANEL_WIDTH - 25, 5))
        
        # Seta para baixo (se não está no final)
        if panel_scroll_offset < panel_max_scroll:
            arrow_down = font_tiny.render("▼", True, (200, 200, 255))
            screen.blit(arrow_down, (panel_x + PANEL_WIDTH - 25, HEIGHT - 25))
        
        # Barra de scroll lateral
        scroll_bar_height = max(30, int(HEIGHT * (HEIGHT / total_content_height)))
        scroll_bar_y = int((HEIGHT - scroll_bar_height) * (panel_scroll_offset / panel_max_scroll))
        pygame.draw.rect(screen, (150, 150, 170), (panel_x + PANEL_WIDTH - 8, scroll_bar_y, 6, scroll_bar_height), border_radius=3)


def draw_battery():
    """Função mantida para compatibilidade, mas não é mais usada."""
    pass


def draw_delivery_status():
    """Função mantida para compatibilidade, mas não é mais usada."""
    pass


def draw_auto_mode_status():
    """Função mantida para compatibilidade, mas não é mais usada."""
    pass


def check_game_state():
    """Verifica o estado do jogo (vitória ou game over)."""
    global game_state
    
    # Verifica se todos os itens foram entregues
    items_remaining = sum(len(items) for items in items_on_grid.values())
    total_items_delivered = items_delivered_count + len(robot_inventory)
    
    if items_remaining == 0 and len(robot_inventory) == 0 and total_items_initial > 0:
        # Todos os itens foram coletados e entregues
        if game_state == "playing":
            game_state = "victory"
            play_sound('victory')
    elif battery <= 0 and (items_remaining > 0 or len(robot_inventory) > 0):
        # Bateria acabou e ainda há itens para entregar
        if game_state == "playing":
            game_state = "game_over"
            play_sound('gameover')


def draw_game_overlay():
    """Desenha mensagens de vitória ou game over."""
    # Centro da área do grid (sem incluir o painel lateral)
    grid_center_x = GRID_WIDTH // 2
    grid_center_y = HEIGHT // 2
    
    if game_state == "victory":
        # Mensagem de vitória
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Título
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("PARABÉNS!", True, GREEN)
        title_rect = title_text.get_rect(center=(grid_center_x, grid_center_y - 60))
        screen.blit(title_text, title_rect)
        
        # Mensagem
        message_font = pygame.font.Font(None, 48)
        message_text = message_font.render("Todos os itens foram entregues!", True, WHITE)
        message_rect = message_text.get_rect(center=(grid_center_x, grid_center_y))
        screen.blit(message_text, message_rect)
        
        # Instrução
        instruction_font = pygame.font.Font(None, 36)
        instruction_text = instruction_font.render("Pressione ESPAÇO para jogar novamente", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(grid_center_x, grid_center_y + 60))
        screen.blit(instruction_text, instruction_rect)
        
    elif game_state == "game_over":
        # Mensagem de game over
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Título
        title_font = pygame.font.Font(None, 72)
        title_text = title_font.render("GAME OVER", True, RED)
        title_rect = title_text.get_rect(center=(grid_center_x, grid_center_y - 60))
        screen.blit(title_text, title_rect)
        
        # Mensagem
        message_font = pygame.font.Font(None, 48)
        message_text = message_font.render("Bateria acabou!", True, WHITE)
        message_rect = message_text.get_rect(center=(grid_center_x, grid_center_y))
        screen.blit(message_text, message_rect)
        
        # Mensagem adicional
        items_remaining = sum(len(items) for items in items_on_grid.values()) + len(robot_inventory)
        additional_text = message_font.render(f"Ainda há {items_remaining} itens para entregar", True, (255, 200, 200))
        additional_rect = additional_text.get_rect(center=(grid_center_x, grid_center_y + 40))
        screen.blit(additional_text, additional_rect)
        
        # Instrução
        instruction_font = pygame.font.Font(None, 36)
        instruction_text = instruction_font.render("Pressione ESPAÇO para tentar novamente", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(grid_center_x, grid_center_y + 100))
        screen.blit(instruction_text, instruction_rect)


def reset_game():
    """Reinicia o jogo."""
    global robot_grid_pos, robot_real_pos, battery
    global is_recharging, time_at_station, recharge_start_time, battery_at_recharge_start, last_position
    global items_on_grid, robot_inventory
    global is_delivering, time_at_warehouse, last_delivery_time, items_delivered_count
    global game_state, total_items_initial
    
    # Resetar posição do robô
    for row_idx, row in enumerate(matriz2):
        for col_idx, cell in enumerate(row):
            if cell == 'S':
                robot_grid_pos = [col_idx, row_idx]
                robot_real_pos = [col_idx * CELL_SIZE, row_idx * CELL_SIZE]
                break
    
    # Resetar bateria
    battery = 100
    
    # Resetar recarga
    is_recharging = False
    time_at_station = 0
    recharge_start_time = 0
    battery_at_recharge_start = 100
    last_position = robot_grid_pos.copy()
    
    # Resetar itens
    robot_inventory = []
    items_delivered_count = 0
    initialize_items_randomly()
    
    # Resetar entrega
    is_delivering = False
    time_at_warehouse = 0
    last_delivery_time = 0
    
    # Resetar estado do jogo
    game_state = "playing"


# Inicializar itens aleatoriamente
initialize_items_randomly()

# Diagnóstico do mixer de áudio
log("=" * 60, "SOUND")
log("DIAGNÓSTICO DO SISTEMA DE ÁUDIO", "SOUND")
try:
    mixer_info = pygame.mixer.get_init()
    if mixer_info:
        log(f"Mixer inicializado: freq={mixer_info[0]}Hz, size={mixer_info[1]}, channels={mixer_info[2]}", "SOUND")
        log(f"Canais disponíveis: {pygame.mixer.get_num_channels()}", "SOUND")
    else:
        log("AVISO: Mixer não foi inicializado!", "ERROR")
except Exception as e:
    log(f"Erro ao verificar mixer: {e}", "ERROR")

# Inicializar sistema de sons
init_sounds()

# Log do estado inicial
log("=" * 60, "INIT")
log("=== SIMULADOR DE ROBÔ - INICIADO ===", "INIT")
log(f"Posição inicial do robô: ({robot_grid_pos[0]}, {robot_grid_pos[1]})", "INIT")
log(f"Bateria inicial: {battery}%", "INIT")
log(f"Capacidade do robô: {ROBOT_CAPACITY} itens", "INIT")
log(f"Total de itens no ambiente: {total_items_initial}", "INIT")
# Conta almoxarifados e estações de recarga
warehouses_count = sum(1 for row in matriz2 for cell in row if cell == 'A')
recharge_count = sum(1 for row in matriz2 for cell in row if cell == 'R')
log(f"Almoxarifados disponíveis: {warehouses_count}", "INIT")
log(f"Estações de recarga disponíveis: {recharge_count}", "INIT")
log("=" * 60, "INIT")

# Loop principal
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BLACK)

    # Verifica o estado do jogo
    if game_state == "playing":
        check_game_state()
        
        # Atualiza a recarga automática
        update_auto_recharge()
        
        # Atualiza a entrega automática
        update_auto_delivery()
        
        # Atualiza modo automático
        update_auto_mode()
        
        draw_grid()
        draw_items_on_grid()  # Desenha itens no grid
        animate_robot()  # Atualiza a posição do robô suavemente
        draw_robot(scale=0.45)
        draw_robot_item_count()  # Mostra quantidade de itens carregados
        draw_side_panel()  # Desenha painel lateral com todas as informações
    else:
        # Desenha o jogo pausado
        draw_grid()
        draw_items_on_grid()
        animate_robot()  # Mantém animação mesmo pausado
        draw_robot(scale=0.45)
        draw_robot_item_count()
        draw_side_panel()  # Desenha painel lateral com todas as informações
    
    # Desenha overlay de vitória ou game over
    draw_game_overlay()

    pygame.display.flip()
    clock.tick(30)  # Atualiza 30 vezes por segundo

    # Captura de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll do painel lateral
            scroll_amount = -event.y * 25  # Inverte e multiplica para suavizar
            panel_scroll_offset = max(0, min(panel_max_scroll, panel_scroll_offset + scroll_amount))

        elif event.type == pygame.KEYDOWN:
            if game_state == "playing":
                # Controles de modo automático
                if event.key == pygame.K_a:
                    # Alterna modo automático total
                    if auto_mode == AUTO_MODE_OFF:
                        auto_mode = AUTO_MODE_FULL
                        # Limpa estados anteriores
                        current_path = []
                        current_path_index = 0
                        current_action = None
                        waiting_for_action = False
                        last_action_time = 0  # Inicia imediatamente sem delay
                        log("=== MODO AUTOMÁTICO TOTAL ATIVADO (Sequência de ações com delay de 300ms) ===", "MODE")
                        play_sound('mode_change')
                    else:
                        auto_mode = AUTO_MODE_OFF
                        current_path = []
                        current_action = None
                        log("Modo automático DESATIVADO (voltou para MANUAL)", "MODE")
                        play_sound('mode_change')
                
                elif event.key == pygame.K_s:
                    # Ativa modo semi-automático (sempre ativa, nunca desativa)
                    # O modo se desativa automaticamente após completar uma ação
                    if auto_mode == AUTO_MODE_OFF:
                        auto_mode = AUTO_MODE_SEMI
                        # Limpa resíduos de execuções anteriores
                        current_path = []
                        current_path_index = 0
                        current_action = None
                        waiting_for_action = False
                        log("=== MODO SEMI-AUTOMÁTICO ATIVADO ===", "MODE")
                        play_sound('mode_change')
                    elif auto_mode == AUTO_MODE_SEMI:
                        # Se já está em modo semi-automático, ignora
                        log("Modo semi-automático já está ativo. Aguarde a conclusão da ação atual.", "MODE")
                    else:
                        # Se está em modo automático total, avisa que não pode ativar semi-automático
                        log("Não é possível ativar modo semi-automático enquanto modo automático total está ativo.", "MODE")
                
                # Controles normais (interrompem modo automático se usado)
                elif event.key == pygame.K_RIGHT:
                    if auto_mode != AUTO_MODE_OFF:
                        log("Modo automático interrompido por movimento manual", "MODE")
                        auto_mode = AUTO_MODE_OFF
                        current_path = []
                        current_action = None
                    move_robot('mr')
                elif event.key == pygame.K_LEFT:
                    if auto_mode != AUTO_MODE_OFF:
                        log("Modo automático interrompido por movimento manual", "MODE")
                        auto_mode = AUTO_MODE_OFF
                        current_path = []
                        current_action = None
                    move_robot('ml')
                elif event.key == pygame.K_UP:
                    if auto_mode != AUTO_MODE_OFF:
                        log("Modo automático interrompido por movimento manual", "MODE")
                        auto_mode = AUTO_MODE_OFF
                        current_path = []
                        current_action = None
                    move_robot('mu')
                elif event.key == pygame.K_DOWN:
                    if auto_mode != AUTO_MODE_OFF:
                        log("Modo automático interrompido por movimento manual", "MODE")
                        auto_mode = AUTO_MODE_OFF
                        current_path = []
                        current_action = None
                    move_robot('md')
                elif event.key == pygame.K_1:
                    if auto_mode != AUTO_MODE_OFF:
                        log("Modo automático interrompido por coleta manual", "MODE")
                        auto_mode = AUTO_MODE_OFF
                        current_path = []
                        current_action = None
                    # Coleta o primeiro item (índice 1)
                    collect_item(1)
                elif event.key == pygame.K_2:
                    if auto_mode != AUTO_MODE_OFF:
                        log("Modo automático interrompido por coleta manual", "MODE")
                        auto_mode = AUTO_MODE_OFF
                        current_path = []
                        current_action = None
                    # Coleta o segundo item (índice 2)
                    collect_item(2)
                
                elif event.key == pygame.K_m:
                    # Toggle de som
                    toggle_sound()
                
                elif event.key == pygame.K_t:
                    # Testa todos os sons (apenas se som estiver habilitado)
                    if SOUND_ENABLED:
                        log("========== TESTANDO TODOS OS SONS ==========", "SOUND")
                        test_sounds = ['move', 'collect', 'deliver', 'recharge_start', 
                                      'recharge_complete', 'mode_change', 'victory', 'gameover']
                        for i, sound_name in enumerate(test_sounds):
                            log(f"Teste {i+1}/{len(test_sounds)}: {sound_name}", "SOUND")
                            play_sound(sound_name, debug=True)
                            pygame.time.wait(400)  # Espera 400ms entre sons
                        log("========== TESTE COMPLETO ==========", "SOUND")
                    else:
                        log("Som está desabilitado. Pressione M para habilitar.", "SOUND")
            elif event.key == pygame.K_SPACE:
                # Reinicia o jogo quando em vitória ou game over
                reset_game()

pygame.quit()