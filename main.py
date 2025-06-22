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

# PID parameters
Kp, Ki, Kd = 0.2, 0.05, 0
previous_error = 0
previous_throttle = actual_speed * 0.01
max_delta = 0.5
dt = 0.1
running = True
cruise_active = False

# Slider configuration
min_speed = 0
max_speed = 200
step_manual = 1
step_cruise = 5
slider_width = 600
num_steps_manual = (max_speed - min_speed) // step_manual
num_steps_cruise = (max_speed - min_speed) // step_cruise

# Graph data
time_data = []
error_data = []
speed_data = []

# Matplotlib figure setup (más grande)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), dpi=100)
fig.subplots_adjust(hspace=0.4)
fig.canvas.draw()

def plot_to_surface():
    ax1.clear()
    ax1.plot(time_data, error_data, color='red')
    ax1.axhline(2, linestyle='--', color='gray')
    ax1.axhline(-2, linestyle='--', color='gray')
    ax1.set_title("Error (Deseada - Actual)")
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Error (km/h)")
    if error_data:
        max_abs_error = max(abs(e) for e in error_data)
        margin = 1
        ax1.set_ylim(-max_abs_error - margin, max_abs_error + margin)
        ax1.set_xlim(time_data[0], time_data[-1])
    else:
        ax1.set_ylim(-10, 10)
        ax1.set_xlim(0, 10)

    ax2.clear()
    ax2.plot(time_data, speed_data, color='blue')
    ax2.set_title("Velocidad Actual")
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("Velocidad (km/h)")
    if speed_data:
        min_speed_data = min(speed_data)
        max_speed_data = max(speed_data)
        margin_speed = (max_speed_data - min_speed_data) * 0.1 if max_speed_data != min_speed_data else 5
        y_min = min_speed_data - margin_speed
        y_max = max_speed_data + margin_speed
        ax2.set_ylim(y_min, y_max)
        ax2.set_xlim(time_data[0], time_data[-1])
    else:
        ax2.set_ylim(0, 100)
        ax2.set_xlim(0, 10)

    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    img_data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(h, w, 3)
    return pygame.image.frombuffer(img_data.flatten(), (w, h), 'RGB')

def run_simulation():
    global actual_speed, integral, t, previous_error, previous_throttle
    while running:
        if cruise_active:
            error = desired_speed - actual_speed
            integral += error * dt
            derivative = (error - previous_error) / dt
            throttle = Kp * error + Ki * integral + Kd * derivative
            delta = throttle - previous_throttle
            if delta > max_delta:
                throttle = previous_throttle + max_delta
            elif delta < -max_delta:
                throttle = previous_throttle - max_delta
            previous_throttle = throttle
            accel = throttle - 0.01 * actual_speed
            actual_speed += accel * dt
            previous_error = error
            t += dt
            time_data.append(t)
            error_data.append(error)
            speed_data.append(actual_speed)
        else:
            actual_speed = initial_speed
            speed_data.append(actual_speed)
            if len(time_data) == 0:
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

manual_slider_rect = pygame.Rect(150, 35, slider_width, 10)
cruise_slider_rect = pygame.Rect(150, 75, slider_width, 10)

manual_knob_x = int(manual_slider_rect.left + (initial_speed - min_speed) / step_manual * step_size_manual)
cruise_knob_x = int(cruise_slider_rect.left + (desired_speed - min_speed) / step_cruise * step_size_cruise)

manual_knob_rect = pygame.Rect(manual_knob_x - 10, manual_slider_rect.y - 6, 20, 20)
cruise_knob_rect = pygame.Rect(cruise_knob_x - 10, cruise_slider_rect.y - 6, 20, 20)

button_rect = pygame.Rect((WIDTH - 100) // 2, 110, 100, 30)

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
                    integral = 0
                    previous_error = 0
                    previous_throttle = 0
                    t = 0
                    time_data.clear()
                    error_data.clear()
                    speed_data.clear()
        elif e.type == pygame.MOUSEBUTTONUP:
            dragging_manual = dragging_cruise = False
        elif e.type == pygame.MOUSEMOTION:
            if dragging_manual and not cruise_active:
                manual_knob_x = min(max(e.pos[0], manual_slider_rect.left), manual_slider_rect.right)
                relative_pos = round((manual_knob_x - manual_slider_rect.left) / step_size_manual)
                manual_knob_x = int(manual_slider_rect.left + relative_pos * step_size_manual)
                initial_speed = min_speed + relative_pos * step_manual
                manual_knob_rect.x = manual_knob_x - 10
            elif dragging_cruise:
                cruise_knob_x = min(max(e.pos[0], cruise_slider_rect.left), cruise_slider_rect.right)
                relative_pos = round((cruise_knob_x - cruise_slider_rect.left) / step_size_cruise)
                cruise_knob_x = int(cruise_slider_rect.left + relative_pos * step_size_cruise)
                desired_speed = min_speed + relative_pos * step_cruise
                cruise_knob_rect.x = cruise_knob_x - 10

    if not dragging_manual:
        manual_knob_x = int(manual_slider_rect.left + (initial_speed - min_speed) / step_manual * step_size_manual)
        manual_knob_rect.x = manual_knob_x - 10

    screen.fill((255, 255, 255))

    label1 = font.render("Velocidad inicial:", True, (0, 0, 0))
    label2 = font.render("Cruise objetivo:", True, (0, 0, 0))
    label_actual = font.render(f"Velocidad actual: {actual_speed:.1f} km/h", True, (0, 100, 200))
    label_cruise = font.render(f"Crucero: {'ACTIVO' if cruise_active else 'INACTIVO'}",
                               True, (0, 150, 0) if cruise_active else (200, 0, 0))

    screen.blit(label1, (150, 15))
    screen.blit(label2, (150, 55))
    screen.blit(label_actual, (150, 160))
    screen.blit(label_cruise, (150, 190))

    pygame.draw.rect(screen, (220, 220, 220), manual_slider_rect)
    pygame.draw.rect(screen, (100, 100, 255), manual_knob_rect)
    manual_val = font.render(f"{initial_speed:.0f} km/h", True, (0, 0, 0))
    screen.blit(manual_val, (manual_slider_rect.right + 10, manual_slider_rect.y - 5))

    pygame.draw.rect(screen, (220, 220, 220), cruise_slider_rect)
    pygame.draw.rect(screen, (0, 200, 0), cruise_knob_rect)
    cruise_val = font.render(f"{desired_speed:.0f} km/h", True, (0, 0, 0))
    screen.blit(cruise_val, (cruise_slider_rect.right + 10, cruise_slider_rect.y - 5))

    pygame.draw.rect(screen, (0, 150, 0) if not cruise_active else (200, 0, 0), button_rect)
    btn_label = "Start" if not cruise_active else "Stop"
    btn_text = font.render(btn_label, True, (255, 255, 255))
    screen.blit(btn_text, btn_text.get_rect(center=button_rect.center))

    if cruise_active and len(time_data) > 1:
        plot_surface = plot_to_surface()
        if plot_surface:
            graph_rect = pygame.Rect(100, 240, 700, 530)
            plot_surface = pygame.transform.smoothscale(plot_surface, (graph_rect.width, graph_rect.height))
            screen.blit(plot_surface, graph_rect.topleft)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()