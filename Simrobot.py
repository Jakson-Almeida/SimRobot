import pygame
import math

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

    # Se o robô se moveu, interrompe a recarga e reseta o tempo na estação
    if robot_grid_pos != old_pos:
        is_recharging = False
        time_at_station = 0
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
            if not is_recharging:
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
                    # Bateria cheia, para de recarregar
                    is_recharging = False
                    time_at_station = 0
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
    elif is_at_recharge_station() and not is_recharging:
        # Está na estação mas ainda não começou a recarregar
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


# Loop principal
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BLACK)

    # Atualiza a recarga automática
    update_auto_recharge()
    
    draw_grid()
    animate_robot()  # Atualiza a posição do robô suavemente
    draw_robot(scale=0.45)
    draw_battery()

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

pygame.quit()