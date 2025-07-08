import time
import pygame
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as tkagg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk
import threading

# Parámetros
Kp, Ki = 0.25, 0.05
max_delta, dt = 0.5, 0.01
drag_coeff = 0.01

min_speed, max_speed = 0, 200
step_manual, step_cruise = 1, 5
slider_width = 300
num_steps_manual = (max_speed - min_speed) // step_manual
num_steps_cruise = (max_speed - min_speed) // step_cruise

# Estado global
actual_speed = 95.0
initial_speed = actual_speed
desired_speed = 100.0
integral = 0.0
previous_throttle = actual_speed * drag_coeff
t = 0.0
running = True
cruise_active = False
paused = False
perturb_flags = {2: False, 5: False, 20: False}

history = {
    "time": [], "error": [], "speed": [], "p": [], "i": [],
    "input_speed": [], "error_band_pos": [], "error_band_neg": [], "feedback": [], "perturbations": []
}

# UI Pygame
plot_window = None
plot_thread = None
plot_running = False
screen = font = clock = None
manual_slider_rect = cruise_slider_rect = None
manual_knob_rect = cruise_knob_rect = None
button_rect = pause_button_rect = None
perturb_buttons_rects = {}
step_size_manual = step_size_cruise = None
dragging_manual = dragging_cruise = False

use_p = True
use_i = True
p_button_rect = None
i_button_rect = None

def init_ui():
    global screen, font, clock
    global manual_slider_rect, cruise_slider_rect
    global manual_knob_rect, cruise_knob_rect, button_rect, pause_button_rect
    global step_size_manual, step_size_cruise, perturb_buttons_rects
    global p_button_rect, i_button_rect

    pygame.init()
    WIDTH, HEIGHT = 520, 350
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Control de Crucero")
    font = pygame.font.SysFont("consolas", 16)
    clock = pygame.time.Clock()

    step_size_manual = slider_width / num_steps_manual
    step_size_cruise = slider_width / num_steps_cruise

    slider_start_x = 30
    manual_slider_rect = pygame.Rect(slider_start_x, 35, slider_width, 10)
    cruise_slider_rect = pygame.Rect(slider_start_x, 75, slider_width, 10)

    mx = manual_slider_rect.left + (initial_speed - min_speed) / (max_speed - min_speed) * slider_width
    cx = cruise_slider_rect.left + (desired_speed - min_speed) / (max_speed - min_speed) * slider_width
    manual_knob_rect = pygame.Rect(mx - 8, manual_slider_rect.y - 5, 16, 16)
    cruise_knob_rect = pygame.Rect(cx - 8, cruise_slider_rect.y - 5, 16, 16)

    p_button_rect = pygame.Rect(30, 115, 80, 30)
    i_button_rect = pygame.Rect(120, 115, 80, 30)
    button_rect = pygame.Rect(220, 115, 80, 30)
    pause_button_rect = pygame.Rect(310, 115, 80, 30)

    pb_width, pb_gap = 70, 10
    total_pb_width = 3 * pb_width + 2 * pb_gap
    start_pb_x = (WIDTH - total_pb_width) // 2
    pb_y = 165
    for idx, kmh in enumerate((2, 5, 10)):
        x = start_pb_x + idx * (pb_width + pb_gap)
        perturb_buttons_rects[kmh] = pygame.Rect(x, pb_y, pb_width, 30)

def run_simulation():
    global actual_speed, integral, t, previous_throttle
    while running:
        if paused:
            time.sleep(dt)
            continue

        if cruise_active:
            perturb_amount = 0
            for k in perturb_flags:
                if perturb_flags[k]:
                    actual_speed = max(0.0, actual_speed - k)
                    perturb_amount += k
                    perturb_flags[k] = False

            error = desired_speed - actual_speed
            integral += error * dt if use_i else 0
            p_term = Kp * error if use_p else 0
            i_term = Ki * integral if use_i else 0
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

        else:
            actual_speed = initial_speed
            p_term = i_term = 0
            perturb_amount = 0

        t += dt
        history["time"].append(t)
        history["error"].append(desired_speed - actual_speed if cruise_active else 0)
        history["p"].append(p_term)
        history["i"].append(i_term)
        history["speed"].append(actual_speed)
        history["input_speed"].append(desired_speed if cruise_active else initial_speed)
        history["feedback"].append(actual_speed)
        history["error_band_pos"].append(2.0)
        history["error_band_neg"].append(-2.0)
        history["perturbations"].append(perturb_amount)

        time.sleep(dt)

def draw_sliders():
    screen.blit(font.render("Inicial:", True, (0, 0, 0)),
                (manual_slider_rect.x, manual_slider_rect.y - 18))
    screen.blit(font.render("Crucero:", True, (0, 0, 0)),
                (cruise_slider_rect.x, cruise_slider_rect.y - 18))

    pygame.draw.rect(screen, (220,220,220), manual_slider_rect)
    pygame.draw.rect(screen, (100,100,255), manual_knob_rect)
    screen.blit(font.render(f"{initial_speed:.0f} km/h", True, (0,0,0)),
                (manual_slider_rect.right + 10, manual_slider_rect.y - 3))

    pygame.draw.rect(screen, (220,220,220), cruise_slider_rect)
    pygame.draw.rect(screen, (0,200,0), cruise_knob_rect)
    screen.blit(font.render(f"{desired_speed:.0f} km/h", True, (0,0,0)),
                (cruise_slider_rect.right + 10, cruise_slider_rect.y - 3))

def draw_buttons():
    color = (0, 200, 0) if use_p else (150, 150, 150)
    pygame.draw.rect(screen, color, p_button_rect)
    label = font.render("Control P", True, (255, 255, 255))
    screen.blit(label, label.get_rect(center=p_button_rect.center))

    color = (0, 200, 0) if use_i else (150, 150, 150)
    pygame.draw.rect(screen, color, i_button_rect)
    label = font.render("Control I", True, (255, 255, 255))
    screen.blit(label, label.get_rect(center=i_button_rect.center))

    color = (0,150,0) if not cruise_active else (200,0,0)
    pygame.draw.rect(screen, color, button_rect)
    text = font.render("Start" if not cruise_active else "Stop", True, (255,255,255))
    screen.blit(text, text.get_rect(center=button_rect.center))

    color = (255,165,0) if not paused else (0,100,255)
    pygame.draw.rect(screen, color, pause_button_rect)
    text = font.render("Pausa" if not paused else "Reanudar", True, (255,255,255))
    screen.blit(text, text.get_rect(center=pause_button_rect.center))

    for kmh, rect in perturb_buttons_rects.items():
        if cruise_active:
            color = {2: (180,60,60), 5: (150,75,0), 10: (120,0,0)}[kmh]
            text_color = (255,255,255)
        else:
            color = (180,180,180)
            text_color = (100,100,100)
        pygame.draw.rect(screen, color, rect)
        txt = font.render(f"-{kmh}", True, text_color)
        screen.blit(txt, txt.get_rect(center=rect.center))

def draw_status():
    screen.blit(font.render(f"Actual: {actual_speed:.1f} km/h", True, (0,100,200)), (30, 215))
    status = "Crucero: " + ("ACTIVO" if cruise_active else "INACTIVO")
    color = (0,150,0) if cruise_active else (200,0,0)
    screen.blit(font.render(status, True, color), (30, 240))

def create_plot_window():
    global plot_window, plot_running

    plot_running = False
    if plot_window:
        try:
            plot_window.after(0, plot_window.destroy)
        except:
            pass
        plot_window = None

    plot_window = tk.Tk()
    plot_window.title("Gráficos - Control PI")
    plot_window.geometry("1400x1000")
    plot_window.protocol("WM_DELETE_WINDOW", close_plot_window)

    fig = Figure(figsize=(14, 10), dpi=100)
    axs = [
        fig.add_subplot(4, 2, 1),  # Realimentación
        fig.add_subplot(4, 2, 2),  # Entrada
        fig.add_subplot(4, 2, 3),  # Control PI
        fig.add_subplot(4, 2, 4),  # Error
        fig.add_subplot(4, 2, 5),  # Controlador P
        fig.add_subplot(4, 2, 6),  # Perturbaciones
        fig.add_subplot(4, 2, 7),  # Controlador I
        fig.add_subplot(4, 2, 8)   # Espacio vacío (opcional)
    ]

    canvas = tkagg.FigureCanvasTkAgg(fig, plot_window)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    btn = ttk.Button(plot_window, text="Cerrar Gráficos", command=close_plot_window)
    btn.pack(pady=10)
    plot_running = True

    def update_plots():
        if not plot_running or not history["time"]:
            plot_window.after(100, update_plots)
            return

        try:
            min_len = min(len(history[k]) for k in history)
            if min_len < 2:
                plot_window.after(100, update_plots)
                return

            trimmed = {k: history[k][:min_len] for k in history}

            for ax in axs:
                ax.clear()

            axs[0].plot(trimmed["time"], trimmed["feedback"], 'g-', label='Realimentación')
            axs[0].set_title("Realimentación")
            axs[0].legend()
            axs[0].grid(True)

            axs[1].plot(trimmed["time"], trimmed["input_speed"], 'b-', label='Entrada deseada')
            axs[1].set_title("Entrada deseada")
            axs[1].legend()
            axs[1].grid(True)

            pi_sum = [p + i for p, i in zip(trimmed["p"], trimmed["i"])]
            axs[2].plot(trimmed["time"], pi_sum, 'black', label='Controlador PI')
            axs[2].set_title("Controlador PI")
            axs[2].legend()
            axs[2].grid(True)

            axs[3].plot(trimmed["time"], trimmed["error"], 'r-', label='Error')
            axs[3].plot(trimmed["time"], trimmed["error_band_pos"], 'gray', linestyle='--', label='Banda ±2')
            axs[3].plot(trimmed["time"], trimmed["error_band_neg"], 'gray', linestyle='--')
            axs[3].set_title("Error")
            axs[3].legend()
            axs[3].grid(True)

            axs[4].plot(trimmed["time"], trimmed["p"], 'purple', label='Controlador P')
            axs[4].set_title("Controlador P")
            axs[4].legend()
            axs[4].grid(True)

            axs[5].step(trimmed["time"], trimmed["perturbations"], where='post', color='orange', label='Perturbaciones')
            axs[5].set_title("Perturbaciones Aplicadas")
            axs[5].legend()
            axs[5].grid(True)

            axs[6].plot(trimmed["time"], trimmed["i"], 'brown', label='Controlador I')
            axs[6].set_title("Controlador I")
            axs[6].legend()
            axs[6].grid(True)

            axs[7].axis('off')  # Espacio libre

            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            print(f"Error al actualizar gráficos: {e}")

        plot_window.after(100, update_plots)

    update_plots()
    plot_window.mainloop()

def close_plot_window():
    global plot_running, plot_window
    plot_running = False
    if plot_window:
        try:
            plot_window.after(0, plot_window.destroy)
        except:
            pass
        plot_window = None

def start_plot_window():
    global plot_thread
    if not plot_window:
        plot_thread = threading.Thread(target=create_plot_window, daemon=True)
        plot_thread.start()

def clear_data():
    global integral, previous_throttle, t
    integral = 0.0
    previous_throttle = actual_speed * drag_coeff
    t = 0.0
    for k in history:
        history[k].clear()

def handle_events():
    global running, cruise_active, paused
    global dragging_manual, dragging_cruise, initial_speed, desired_speed
    global use_p, use_i

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if manual_knob_rect.collidepoint(e.pos) and not cruise_active:
                dragging_manual = True
            elif cruise_knob_rect.collidepoint(e.pos):
                dragging_cruise = True
            elif p_button_rect.collidepoint(e.pos):
                use_p = not use_p
            elif i_button_rect.collidepoint(e.pos):
                use_i = not use_i
            elif button_rect.collidepoint(e.pos):
                cruise_active = not cruise_active
                if cruise_active:
                    clear_data()
                    start_plot_window()
                else:
                    close_plot_window()
            elif pause_button_rect.collidepoint(e.pos):
                paused = not paused
            elif cruise_active:
                for kmh, rect in perturb_buttons_rects.items():
                    if rect.collidepoint(e.pos):
                        perturb_flags[kmh] = True
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

def main():
    init_ui()
    threading.Thread(target=run_simulation, daemon=True).start()

    while running:
        handle_events()
        screen.fill((255,255,255))
        draw_sliders()
        draw_buttons()
        draw_status()
        pygame.display.flip()
        clock.tick(60)

    close_plot_window()
    pygame.quit()

if __name__ == "__main__":
    main()