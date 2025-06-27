import pygame
import matplotlib.pyplot as plt
import threading
import numpy as np

# ─── Parámetros de Simulación ─────────────────────────────
Kp, Ki       = 0.2, 0.05
max_delta    = 0.5
dt           = 0.1
drag_coeff   = 0.01
perturb_imp  = -10.0

min_speed, max_speed      = 0, 200
step_manual, step_cruise  = 1, 5
slider_width              = 600
num_steps_manual          = (max_speed - min_speed) // step_manual
num_steps_cruise          = (max_speed - min_speed) // step_cruise

# ─── Estado Global ────────────────────────────────────────
actual_speed      = 60.0
initial_speed     = actual_speed
desired_speed     = 100.0
integral          = 0.0
previous_throttle = actual_speed * drag_coeff
t                 = 0.0
running           = True
cruise_active     = False
perturb_requested = False

time_data        = []
error_data       = []
speed_data       = []
p_data           = []
i_data           = []
input_speed_data = []

# ─── UI State (inicializado en init_ui) ──────────────────
screen = font = clock = None
manual_slider_rect = cruise_slider_rect = None
manual_knob_rect = cruise_knob_rect = None
button_rect = perturb_button_rect = None
step_size_manual = step_size_cruise = None

# ─── Inicialización de UI ─────────────────────────────────
def init_ui():
    global screen, font, clock
    global manual_slider_rect, cruise_slider_rect
    global manual_knob_rect, cruise_knob_rect
    global button_rect, perturb_button_rect
    global step_size_manual, step_size_cruise

    pygame.init()
    WIDTH, HEIGHT = 900, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Control de Crucero")
    font = pygame.font.SysFont("consolas", 20)
    clock = pygame.time.Clock()

    step_size_manual = slider_width / num_steps_manual
    step_size_cruise = slider_width / num_steps_cruise

    manual_slider_rect = pygame.Rect(150, 50, slider_width, 10)
    cruise_slider_rect = pygame.Rect(150, 110, slider_width, 10)

    mx = manual_slider_rect.left + (initial_speed - min_speed) / (max_speed - min_speed) * slider_width
    cx = cruise_slider_rect.left + (desired_speed - min_speed) / (max_speed - min_speed) * slider_width
    manual_knob_rect = pygame.Rect(mx - 10, manual_slider_rect.y - 6, 20, 20)
    cruise_knob_rect = pygame.Rect(cx - 10, cruise_slider_rect.y - 6, 20, 20)

    bw, pw, bh, gap = 100, 140, 30, 20
    y = 140
    total = bw + gap + pw
    start_x = (WIDTH - total) // 2
    button_rect = pygame.Rect(start_x, y, bw, bh)
    perturb_button_rect = pygame.Rect(start_x + bw + gap, y, pw, bh)

# ─── Simulación (hilo) ────────────────────────────────────
def run_simulation():
    global actual_speed, integral, t, previous_throttle, perturb_requested
    while running:
        if cruise_active:
            if perturb_requested:
                actual_speed = max(0.0, actual_speed + perturb_imp)
                perturb_requested = False

            error = desired_speed - actual_speed
            integral += error * dt
            p_term = Kp * error
            i_term = Ki * integral
            raw = p_term + i_term

            delta = raw - previous_throttle
            if delta > max_delta:
                throttle = previous_throttle + max_delta
            elif delta < -max_delta:
                throttle = previous_throttle - max_delta
            else:
                throttle = raw
            previous_throttle = throttle

            accel = throttle - drag_coeff * actual_speed
            actual_speed += accel * dt

            t += dt
            time_data.append(t)
            error_data.append(error)
            p_data.append(p_term)
            i_data.append(i_term)
            speed_data.append(actual_speed)
            input_speed_data.append(desired_speed)
        else:
            actual_speed = initial_speed
            t += dt
            time_data.append(t)
            error_data.append(0)
            p_data.append(0)
            i_data.append(0)
            speed_data.append(actual_speed)
            input_speed_data.append(initial_speed)

        pygame.time.wait(int(dt * 1000))

# ─── Dibujado de Sliders ───────────────────────────────────
def draw_sliders():
    # Títulos de sliders
    screen.blit(font.render("Velocidad inicial:", True, (0,0,0)),
                (manual_slider_rect.x, manual_slider_rect.y - 25))
    screen.blit(font.render("Velocidad crucero:", True, (0,0,0)),
                (cruise_slider_rect.x, cruise_slider_rect.y - 25))

    # Slider manual
    pygame.draw.rect(screen, (220,220,220), manual_slider_rect)
    pygame.draw.rect(screen, (100,100,255), manual_knob_rect)
    screen.blit(font.render(f"{initial_speed:.1f} km/h", True, (0,0,0)),
                (manual_slider_rect.right + 10, manual_slider_rect.y - 5))

    # Slider crucero
    pygame.draw.rect(screen, (220,220,220), cruise_slider_rect)
    pygame.draw.rect(screen, (0,200,0), cruise_knob_rect)
    screen.blit(font.render(f"{desired_speed:.1f} km/h", True, (0,0,0)),
                (cruise_slider_rect.right + 10, cruise_slider_rect.y - 5))
# ─── Dibujado de Botones ───────────────────────────────────
def draw_buttons():
    # Botón Start/Stop
    color = (0,150,0) if not cruise_active else (200,0,0)
    pygame.draw.rect(screen, color, button_rect)
    surf = font.render("Start" if not cruise_active else "Stop", True, (255,255,255))
    screen.blit(surf, surf.get_rect(center=button_rect.center))

    # Botón Perturbar
    pygame.draw.rect(screen, (150,75,0), perturb_button_rect)
    ps = font.render("Perturbar", True, (255,255,255))
    screen.blit(ps, ps.get_rect(center=perturb_button_rect.center))

# ─── Gráfica ────────────────────────────────────────────── ──────────────────────────────────────────────
def plot_to_surface():
    fig, (ax1, ax2) = plt.subplots(2,1,figsize=(8,6), dpi=100)

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
    w,h = fig.canvas.get_width_height()
    img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(h, w, 3)
    plt.close(fig)
    return pygame.image.frombuffer(img.flatten(), (w,h), 'RGB')

# ─── Reset de Datos ───────────────────────────────────────
def clear_data():
    global integral, previous_throttle, t
    integral = 0.0
    previous_throttle = actual_speed * drag_coeff
    t = 0.0
    time_data.clear(); error_data.clear()
    speed_data.clear(); p_data.clear()
    i_data.clear(); input_speed_data.clear()

# ─── Manejo de Eventos ────────────────────────────────────
def handle_events():
    global running, cruise_active, perturb_requested
    global initial_speed, desired_speed
    global dragging_manual, dragging_cruise

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if manual_knob_rect.collidepoint(e.pos) and not cruise_active:
                dragging_manual = True
            elif cruise_knob_rect.collidepoint(e.pos):
                dragging_cruise = True
            elif button_rect.collidepoint(e.pos):
                cruise_active = not cruise_active
                if cruise_active: clear_data()
            elif perturb_button_rect.collidepoint(e.pos) and cruise_active:
                perturb_requested = True
        elif e.type == pygame.MOUSEBUTTONUP:
            dragging_manual = dragging_cruise = False
        elif e.type == pygame.MOUSEMOTION:
            if dragging_manual and not cruise_active:
                x = min(max(e.pos[0], manual_slider_rect.left), manual_slider_rect.right)
                rel = round((x - manual_slider_rect.left) / step_size_manual)
                initial_speed = min_speed + rel * step_manual
                manual_knob_rect.x = manual_slider_rect.left + rel * step_size_manual - 10
            elif dragging_cruise:
                x = min(max(e.pos[0], cruise_slider_rect.left), cruise_slider_rect.right)
                rel = round((x - cruise_slider_rect.left) / step_size_cruise)
                desired_speed = min_speed + rel * step_cruise
                cruise_knob_rect.x = cruise_slider_rect.left + rel * step_size_cruise - 10

# ─── Bucle Principal ─────────────────────────────────────
def main():
    global dragging_manual, dragging_cruise
    init_ui()
    threading.Thread(target=run_simulation, daemon=True).start()
    dragging_manual = dragging_cruise = False

    while running:
        handle_events()
        screen.fill((255,255,255))
        draw_sliders()
        draw_buttons()
        screen.blit(font.render(f"Actual: {actual_speed:.1f} km/h", True, (0,100,200)), (150,180))
        # Estado del control de crucero debajo de la velocidad actual
        status = "Crucero: " + ("ACTIVO" if cruise_active else "INACTIVO")
        color = (0,150,0) if cruise_active else (200,0,0)
        screen.blit(font.render(status, True, color), (150,205))
        if cruise_active and len(time_data) > 1:
            surf = plot_to_surface()
            surf = pygame.transform.smoothscale(surf, (700,530))
            screen.blit(surf, (100,240))
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
