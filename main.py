import pygame
import matplotlib.pyplot as plt
import threading
import numpy as np

# Velocities
actual_speed = 60
initial_speed = actual_speed
desired_speed = 100
integral = 0
t = 0

# PI parameters
Kp, Ki = 0.2, 0.05
previous_throttle = actual_speed * 0.01
max_delta = 0.5
dt = 0.1
running = True
cruise_active = False

# Perturbation flag
perturb_requested = False

# Slider configuration
min_speed = 0
max_speed = 200
step_manual = 1
step_cruise = 5
slider_width = 600
num_steps_manual = (max_speed - min_speed) // step_manual
num_steps_cruise = (max_speed - min_speed) // step_cruise

# Graph data
time_data       = []
error_data      = []
speed_data      = []
p_data          = []   # Componente P
i_data          = []   # Componente I
input_speed_data= []   # Velocidad deseada/manual

# Matplotlib figure setup
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), dpi=100)
fig.subplots_adjust(hspace=0.4)
fig.canvas.draw()

def plot_to_surface():
    fig.clf()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)

    # Gráfico 1: Error, P e I
    ax1.plot(time_data, error_data, color='red',    label='Error')
    ax1.plot(time_data, p_data,     color='purple', label='P (Proporcional)')
    ax1.plot(time_data, i_data,     color='brown',  label='I (Integral)')
    ax1.axhline(0, linestyle='-', color='gray', alpha=0.3)
    ax1.set_title("Controlador PI: Error vs P vs I", fontsize=11)
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Valor")
    ax1.legend(loc='upper right')
    if time_data:
        ax1.set_xlim(time_data[0], time_data[-1])

    # Gráfico 2: velocidades
    ax2.plot(time_data, speed_data,       color='green',  label='Velocidad Actual')
    ax2.plot(time_data, input_speed_data, color='orange', linestyle='--', label='Velocidad Ingresada')
    ax2.set_title("Sistema: Velocidad Actual vs Ingresada", fontsize=11)
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("Velocidad (km/h)")
    ax2.legend(loc='upper right')
    if time_data:
        ax2.set_xlim(time_data[0], time_data[-1])

    fig.tight_layout()
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(h, w, 3)
    return pygame.image.frombuffer(img.flatten(), (w, h), 'RGB')

def run_simulation():
    global actual_speed, integral, t, previous_throttle, perturb_requested

    while running:
        if cruise_active:
            # Impulso de perturbación
            if perturb_requested:
                actual_speed = max(0, actual_speed - 10)
                perturb_requested = False

            # Cálculo del error e integral
            error = desired_speed - actual_speed
            integral += error * dt

            # Componentes P e I
            p_term = Kp * error
            i_term = Ki * integral
            throttle = p_term + i_term

            # Guardar datos
            error_data.append(error)
            p_data.append(p_term)
            i_data.append(i_term)
            input_speed_data.append(desired_speed)

            # Suavizado de throttle
            delta = throttle - previous_throttle
            if delta > max_delta:
                throttle = previous_throttle + max_delta
            elif delta < -max_delta:
                throttle = previous_throttle - max_delta
            previous_throttle = throttle

            # Dinámica simple: empuje - resistencia
            accel = throttle - 0.01 * actual_speed
            actual_speed += accel * dt

            # Avanzar tiempo y guardar velocidad
            t += dt
            time_data.append(t)
            speed_data.append(actual_speed)

        else:
            # Modo manual
            actual_speed = initial_speed
            speed_data.append(actual_speed)
            error_data.append(0)
            p_data.append(0)
            i_data.append(0)
            input_speed_data.append(initial_speed)

            if not time_data:
                t = 0
                time_data.append(t)
            else:
                t += dt
                time_data.append(t)

        pygame.time.wait(int(dt * 1000))

pygame.init()
WIDTH, HEIGHT = 900, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Control de Crucero")
font = pygame.font.SysFont("consolas", 20)

step_size_manual = slider_width / num_steps_manual
step_size_cruise = slider_width / num_steps_cruise

manual_slider_rect = pygame.Rect(150, 50, slider_width, 10)
cruise_slider_rect = pygame.Rect(150, 110, slider_width, 10)

manual_knob_x = int((initial_speed - min_speed) / step_manual * step_size_manual + manual_slider_rect.left)
cruise_knob_x = int((desired_speed - min_speed) / step_cruise * step_size_cruise + cruise_slider_rect.left)

manual_knob_rect = pygame.Rect(manual_knob_x - 10, manual_slider_rect.y - 6, 20, 20)
cruise_knob_rect = pygame.Rect(cruise_knob_x - 10, cruise_slider_rect.y - 6, 20, 20)

# Centrar botones Start y Perturbar
button_width, perturb_width, button_height, gap = 100, 140, 30, 20
y_pos = 140
total_w = button_width + gap + perturb_width
start_x = (WIDTH - total_w) // 2
button_rect = pygame.Rect(start_x, y_pos, button_width, button_height)
perturb_button_rect = pygame.Rect(start_x + button_width + gap, y_pos, perturb_width, button_height)

threading.Thread(target=run_simulation, daemon=True).start()

dragging_manual = dragging_cruise = False
plot_surface = None
clock = pygame.time.Clock()

while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
            pygame.quit()
            raise SystemExit
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if manual_knob_rect.collidepoint(e.pos) and not cruise_active:
                dragging_manual = True
            elif cruise_knob_rect.collidepoint(e.pos):
                dragging_cruise = True
            elif button_rect.collidepoint(e.pos):
                cruise_active = not cruise_active
                if cruise_active:
                    # Reset datos
                    integral = 0
                    previous_throttle = actual_speed * 0.01
                    t = 0
                    time_data.clear()
                    error_data.clear()
                    speed_data.clear()
                    p_data.clear()
                    i_data.clear()
                    input_speed_data.clear()
            elif perturb_button_rect.collidepoint(e.pos) and cruise_active:
                perturb_requested = True
        elif e.type == pygame.MOUSEBUTTONUP:
            dragging_manual = dragging_cruise = False
        elif e.type == pygame.MOUSEMOTION:
            if dragging_manual and not cruise_active:
                x = min(max(e.pos[0], manual_slider_rect.left), manual_slider_rect.right)
                rel = round((x - manual_slider_rect.left) / step_size_manual)
                manual_knob_x = int(manual_slider_rect.left + rel * step_size_manual)
                initial_speed = min_speed + rel * step_manual
                manual_knob_rect.x = manual_knob_x - 10
            elif dragging_cruise:
                x = min(max(e.pos[0], cruise_slider_rect.left), cruise_slider_rect.right)
                rel = round((x - cruise_slider_rect.left) / step_size_cruise)
                cruise_knob_x = int(cruise_slider_rect.left + rel * step_size_cruise)
                desired_speed = min_speed + rel * step_cruise
                cruise_knob_rect.x = cruise_knob_x - 10

    if not dragging_manual:
        manual_knob_rect.x = int((initial_speed - min_speed) / step_manual * step_size_manual + manual_slider_rect.left) - 10

    screen.fill((255, 255, 255))

    # Labels
    screen.blit(font.render("Velocidad inicial:", True, (0, 0, 0)), (150, 25))
    screen.blit(font.render("Velocidad crucero:", True, (0, 0, 0)), (150, 85))
    screen.blit(font.render(f"Velocidad actual: {actual_speed:.1f} km/h", True, (0, 100, 200)), (150, 185))
    screen.blit(font.render(f"Crucero: {'ACTIVO' if cruise_active else 'INACTIVO'}",
                             True, (0, 150, 0) if cruise_active else (200, 0, 0)), (150, 215))

    # Sliders
    pygame.draw.rect(screen, (220, 220, 220), manual_slider_rect)
    pygame.draw.rect(screen, (100, 100, 255), manual_knob_rect)
    screen.blit(font.render(f"{initial_speed:.0f} km/h", True, (0, 0, 0)),
                (manual_slider_rect.right + 10, manual_slider_rect.y - 5))

    pygame.draw.rect(screen, (220, 220, 220), cruise_slider_rect)
    pygame.draw.rect(screen, (0, 200, 0), cruise_knob_rect)
    screen.blit(font.render(f"{desired_speed:.0f} km/h", True, (0, 0, 0)),
                (cruise_slider_rect.right + 10, cruise_slider_rect.y - 5))

    # Botón Start/Stop
    pygame.draw.rect(screen, (0, 150, 0) if not cruise_active else (200, 0, 0), button_rect)
    btn_surf = font.render("Start" if not cruise_active else "Stop", True, (255, 255, 255))
    btn_rect = btn_surf.get_rect(center=button_rect.center)
    screen.blit(btn_surf, btn_rect)

    # Botón Perturbar
    pygame.draw.rect(screen, (150, 75, 0), perturb_button_rect)
    perturb_surf = font.render("Perturbar", True, (255, 255, 255))
    perturb_rect = perturb_surf.get_rect(center=perturb_button_rect.center)
    screen.blit(perturb_surf, perturb_rect)

    # Dibujo del gráfico
    if cruise_active and len(time_data) > 1:
        plot_surface = plot_to_surface()
        graph_rect = pygame.Rect(100, 240, 700, 530)
        plot_surface = pygame.transform.smoothscale(plot_surface, (graph_rect.width, graph_rect.height))
        screen.blit(plot_surface, graph_rect.topleft)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
