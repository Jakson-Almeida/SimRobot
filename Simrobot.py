import pygame
import math
import random

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
matriz2 = [
    ['A', '1', '1', 'R', 'A', '1'],
    ['1', '1', '1', '1', '1', '1'],
    ['1', '1', '1', '0', '1', '1'],
    ['1', 'S', '1', '1', '1', '1'],
]

# Definir a posição inicial do robô (encontra o 'S')
for row_idx, row in enumerate(matriz2):
    for col_idx, cell in enumerate(row):
        if cell == 'S':
            robot_grid_pos = [col_idx, row_idx]  # (x, y)

# Inicializar pygame
pygame.init()

# Configurar a tela
WIDTH = len(matriz2[0]) * CELL_SIZE
HEIGHT = len(matriz2) * CELL_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulador de Robô com Bateria e Gradiente")

# Fonte para exibição de texto
font = pygame.font.Font(None, 36)

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
    global items_on_grid
    
    items_on_grid = {}
    
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
                
                # Remove a célula se não houver mais itens
                if len(items_on_grid[cell_key]) == 0:
                    del items_on_grid[cell_key]
                
                return True
    return False


def is_at_warehouse():
    """Verifica se o robô está em um almoxarifado."""
    x, y = robot_grid_pos
    return matriz2[y][x] == 'A'


def update_auto_delivery():
    """Gerencia a entrega automática de itens no almoxarifado."""
    global robot_inventory, is_delivering, time_at_warehouse, last_delivery_time, items_delivered_count, last_position
    
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
                elif current_time - time_at_warehouse >= WAREHOUSE_WAIT_TIME:
                    # Passou 3 segundos, inicia a entrega
                    is_delivering = True
                    last_delivery_time = current_time
            else:
                # Já está entregando, verifica se passou 1 segundo desde a última entrega
                if current_time - last_delivery_time >= DELIVERY_INTERVAL:
                    # Entrega um item
                    if len(robot_inventory) > 0:
                        robot_inventory.pop(0)  # Remove o primeiro item
                        items_delivered_count += 1
                        last_delivery_time = current_time
                    
                    # Se não há mais itens, para de entregar
                    if len(robot_inventory) == 0:
                        is_delivering = False
                        time_at_warehouse = 0
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
        is_recharging = False
        time_at_station = 0
        is_delivering = False
        time_at_warehouse = 0
        last_position = robot_grid_pos.copy()
        battery -= 2  # Reduz a bateria em 2% a cada movimento


def is_at_recharge_station():
    """Verifica se o robô está em uma estação de recarga."""
    x, y = robot_grid_pos
    return matriz2[y][x] == 'R'


def update_auto_recharge():
    """Gerencia a recarga automática do robô."""
    global battery, is_recharging, time_at_station, recharge_start_time, battery_at_recharge_start, last_position
    
    current_time = pygame.time.get_ticks()
    
    # Verifica se está em uma estação de recarga
    if is_at_recharge_station():
        # Verifica se o robô se moveu desde a última verificação
        if robot_grid_pos == last_position:
            # Se não se moveu, incrementa o tempo na estação
            if battery >= 100:
                # Se já está com 100%, mantém a bateria e não faz nada
                battery = 100
                is_recharging = False
                # Não reseta time_at_station para não reiniciar o processo se a bateria baixar
            elif not is_recharging:
                # Ainda não está recarregando, verifica se já passou o tempo de espera
                if time_at_station == 0:
                    time_at_station = current_time
                elif current_time - time_at_station >= STATION_WAIT_TIME:
                    # Passou 3 segundos, inicia a recarga
                    is_recharging = True
                    recharge_start_time = current_time
                    battery_at_recharge_start = battery
            else:
                # Já está recarregando, atualiza a bateria
                if battery < 100:
                    # Calcula o tempo decorrido desde o início da recarga
                    elapsed_time = (current_time - recharge_start_time) / 1000.0  # em segundos
                    
                    # Calcula quanto tempo levaria para recarregar do nível atual até 100%
                    battery_needed = 100 - battery_at_recharge_start
                    time_needed = (battery_needed / 100.0) * RECHARGE_SPEED
                    
                    # Calcula a porcentagem de recarga baseada no tempo decorrido
                    if time_needed > 0:
                        recharge_progress = min(1.0, elapsed_time / time_needed)
                        battery = battery_at_recharge_start + (battery_needed * recharge_progress)
                        battery = min(100, battery)  # Garante que não ultrapasse 100%
                    else:
                        battery = 100
                else:
                    # Bateria chegou a 100%, para de recarregar mas mantém na estação
                    is_recharging = False
                    battery = 100
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


def draw_battery():
    """Exibe o nível de bateria na tela e status de recarga."""
    battery_text = f"Bateria: {int(battery)}%"
    
    # Mostra status de recarga
    if is_recharging:
        # Calcula tempo restante
        battery_needed = 100 - battery_at_recharge_start
        time_needed = (battery_needed / 100.0) * RECHARGE_SPEED
        elapsed_time = (pygame.time.get_ticks() - recharge_start_time) / 1000.0
        time_remaining = max(0, time_needed - elapsed_time)
        
        status_text = f"Recarregando... {time_remaining:.1f}s restantes"
        color = GREEN
    elif is_at_recharge_station() and not is_recharging and battery < 100:
        # Está na estação mas ainda não começou a recarregar (e precisa recarregar)
        wait_time = (pygame.time.get_ticks() - time_at_station) / 1000.0 if time_at_station > 0 else 0
        wait_remaining = max(0, (STATION_WAIT_TIME / 1000.0) - wait_time)
        status_text = f"Aguardando... {wait_remaining:.1f}s para iniciar recarga"
        color = (255, 255, 0)  # Amarelo
    else:
        status_text = ""
        color = WHITE
    
    text = font.render(battery_text, True, color)
    screen.blit(text, (10, HEIGHT - 40))
    
    if status_text:
        status_surface = font.render(status_text, True, color)
        screen.blit(status_surface, (10, HEIGHT - 80))


def draw_delivery_status():
    """Exibe o status de entrega de itens."""
    if is_delivering:
        # Está entregando itens
        items_remaining = len(robot_inventory)
        status_text = f"Entregando... {items_remaining} itens restantes"
        color = GREEN
    elif is_at_warehouse() and len(robot_inventory) > 0 and not is_delivering:
        # Está no almoxarifado com itens mas ainda não começou a entregar
        wait_time = (pygame.time.get_ticks() - time_at_warehouse) / 1000.0 if time_at_warehouse > 0 else 0
        wait_remaining = max(0, (WAREHOUSE_WAIT_TIME / 1000.0) - wait_time)
        status_text = f"Aguardando... {wait_remaining:.1f}s para iniciar entrega"
        color = (255, 200, 0)  # Laranja
    else:
        status_text = ""
        color = WHITE
    
    if status_text:
        status_surface = font.render(status_text, True, color)
        screen.blit(status_surface, (10, HEIGHT - 120))
    
    # Mostra contador de itens entregues
    if items_delivered_count > 0:
        delivered_text = f"Itens entregues: {items_delivered_count}"
        delivered_surface = font.render(delivered_text, True, WHITE)
        screen.blit(delivered_surface, (10, HEIGHT - 160))


# Inicializar itens aleatoriamente
initialize_items_randomly()

# Loop principal
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BLACK)

    # Atualiza a recarga automática
    update_auto_recharge()
    
    # Atualiza a entrega automática
    update_auto_delivery()
    
    draw_grid()
    draw_items_on_grid()  # Desenha itens no grid
    animate_robot()  # Atualiza a posição do robô suavemente
    draw_robot(scale=0.45)
    draw_robot_item_count()  # Mostra quantidade de itens carregados
    draw_battery()
    draw_delivery_status()  # Mostra status de entrega

    pygame.display.flip()
    clock.tick(30)  # Atualiza 30 vezes por segundo

    # Captura de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                move_robot('mr')
            elif event.key == pygame.K_LEFT:
                move_robot('ml')
            elif event.key == pygame.K_UP:
                move_robot('mu')
            elif event.key == pygame.K_DOWN:
                move_robot('md')
            elif event.key == pygame.K_1:
                # Coleta o primeiro item (índice 1)
                collect_item(1)
            elif event.key == pygame.K_2:
                # Coleta o segundo item (índice 2)
                collect_item(2)

pygame.quit()