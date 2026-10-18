#!/usr/bin/env python3
"""
AetherOS - Premium Mobile Operating System Shell
Built for mobile form factors, Termux:X11, and ARM/x86 touch environments.
Features: 60fps spring physics animations, glassmorphic squircle UI, Dynamic Island,
Control Center, gesture navigation, and interactive mobile apps.
"""

import os
import sys
import time
import math
import random
import subprocess
import tkinter as tk
from tkinter import font as tkfont

# ==========================================
# PALETTE & CONFIGURATION
# ==========================================
THEME = {
    "bg": "#090A0F",             # Deep OLED Night
    "bg_secondary": "#12141D",   # Frosted Glass Card
    "card_border": "#1E2233",    # Glass Edge
    "card_highlight": "#2B3149", # Hover/Press Highlight
    "text_primary": "#FFFFFF",
    "text_secondary": "#8E95AA",
    "text_muted": "#53596E",
    "accent_cyan": "#00F0FF",
    "accent_emerald": "#00E676",
    "accent_purple": "#7C4DFF",
    "accent_sunset": "#FF5252",
    "accent_amber": "#FFD600",
    "pill_bg": "#151824",
}

APPS = [
    {"id": "phone",     "name": "Phone",     "color": ("#00E676", "#00B0FF"), "icon": "📞"},
    {"id": "messages",  "name": "Messages",  "color": ("#00C6FF", "#0072FF"), "icon": "💬"},
    {"id": "browser",   "name": "Browser",   "color": ("#7F00FF", "#E100FF"), "icon": "🌐"},
    {"id": "files",     "name": "Files",     "color": ("#FF9900", "#FF5E62"), "icon": "📁"},
    {"id": "music",     "name": "Music",     "color": ("#FF0844", "#FFB199"), "icon": "🎵"},
    {"id": "settings",  "name": "Settings",  "color": ("#434343", "#282828"), "icon": "⚙️"},
    {"id": "terminal",  "name": "Terminal",  "color": ("#0F2027", "#203A43"), "icon": "💻"},
    {"id": "weather",   "name": "Weather",   "color": ("#4CA1AF", "#2C3E50"), "icon": "☀️"},
    {"id": "clock",     "name": "Clock",     "color": ("#EB3349", "#F45C43"), "icon": "⏰"},
    {"id": "gallery",   "name": "Gallery",   "color": ("#8A2387", "#E94057"), "icon": "🎨"},
    {"id": "notes",     "name": "Notes",     "color": ("#11998E", "#38EF7D"), "icon": "📝"},
    {"id": "calc",      "name": "Calculator","color": ("#F37335", "#FDC830"), "icon": "🧮"},
]

PINNED_APPS = ["phone", "messages", "browser", "music"]

def ease_out_cubic(x):
    return 1.0 - math.pow(1.0 - x, 3)

def ease_out_back(x, c1=1.70158):
    c3 = c1 + 1
    return 1 + c3 * math.pow(x - 1, 3) + c1 * math.pow(x - 1, 2)


class AetherOS:
    def __init__(self, root):
        self.root = root
        self.root.title("AetherOS Mobile")
        self.root.configure(bg=THEME["bg"])
        
        # Adaptive Native Phone Dimensions
        self.w = self.root.winfo_screenwidth()
        self.h = self.root.winfo_screenheight()
        
        # Enable true mobile fullscreen & completely hide the mouse cursor
        self.root.attributes('-fullscreen', True)
        self.root.config(cursor="none")
        self.root.geometry(f"{self.w}x{self.h}+0+0")
        
        # Canvas Root (100% screen fill, no cursor)
        self.canvas = tk.Canvas(
            root, width=self.w, height=self.h,
            bg=THEME["bg"], highlightthickness=0,
            cursor="none"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # OS State
        self.current_app = None
        self.app_transition = 0.0  # 0.0 (home) to 1.0 (app open)
        self.active_app_id = None
        self.control_center_open = False
        self.control_center_prog = 0.0
        self.island_state = "idle"  # idle, music, call, charging
        self.island_scale = 1.0
        self.lockscreen_open = False
        
        # Live Stats
        self.time_str = time.strftime("%I:%M")
        self.date_str = time.strftime("%A, %B %d")
        self.battery_level = 88
        self.wifi_strength = 3
        
        # Terminal app state
        self.term_lines = [
            "AetherOS Kernel 6.1-aarch64 (tty1)",
            "Welcome to AetherOS Mobile Experience.",
            "Type 'help' or any Linux command below:",
            ""
        ]
        self.term_input = ""
        
        # Music app state
        self.is_playing = True
        self.music_track = "Starlight Protocol - Aether Sound"
        self.music_pos = 0.45
        self.eq_bars = [0.3, 0.7, 0.5, 0.9, 0.4, 0.8, 0.6]

        # Phone app state
        self.dial_digits = ""
        
        # Calculator state
        self.calc_display = "0"
        
        # Settings state
        self.settings_toggles = {
            "WiFi": True, "Bluetooth": True, "Dark Mode": True,
            "120Hz Refresh": True, "Haptics": True
        }

        # Setup Interaction Bindings
        self.canvas.bind("<Button-1>", self.on_touch_down)
        self.canvas.bind("<B1-Motion>", self.on_touch_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_touch_up)
        self.root.bind("<Key>", self.on_key_press)
        
        self.touch_start_y = 0
        self.touch_start_x = 0
        self.is_dragging = False

        # Start Main Render Loop (~60 fps)
        self.last_frame = time.time()
        self.render_loop()

    # ==========================================
    # SQUIRCLE & PRIMITIVE DRAWING
    # ==========================================
    def draw_squircle(self, x1, y1, x2, y2, r, fill, outline="", width=1):
        """Draws a smooth rounded rectangle / squircle."""
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return self.canvas.create_polygon(
            points, smooth=True, fill=fill,
            outline=outline, width=width
        )

    # ==========================================
    # TOUCH EVENT HANDLERS
    # ==========================================
    def on_touch_down(self, event):
        self.touch_start_x = event.x
        self.touch_start_y = event.y
        self.is_dragging = False
        
        # Top right pull down -> Control Center
        if event.y < 50 and event.x > self.w - 140 and not self.control_center_open:
            self.control_center_open = True
            return

        # Dynamic island tap -> toggle music pill
        if 8 <= event.y <= 42 and abs(event.x - self.w / 2) < 70:
            self.island_state = "music" if self.island_state == "idle" else "idle"
            return

        # Bottom home bar tap -> Return Home
        if event.y > self.h - 40:
            if self.active_app_id or self.control_center_open:
                self.close_app()
                self.control_center_open = False
                return

        # Control Center interaction
        if self.control_center_open:
            self.handle_control_center_click(event.x, event.y)
            return

        # App interaction if open
        if self.active_app_id:
            self.handle_app_click(event.x, event.y)
            return

        # Homescreen grid & dock clicks
        self.handle_homescreen_click(event.x, event.y)

    def on_touch_drag(self, event):
        dy = event.y - self.touch_start_y
        if abs(dy) > 10:
            self.is_dragging = True

        # Swipe down from top -> drag control center
        if self.touch_start_y < 80 and dy > 20 and not self.control_center_open:
            self.control_center_open = True

        # Swipe up from bottom -> close app
        if self.touch_start_y > self.h - 90 and dy < -30:
            if self.active_app_id or self.control_center_open:
                self.close_app()
                self.control_center_open = False

    def on_touch_up(self, event):
        self.is_dragging = False

    def on_key_press(self, event):
        # Pass typing to terminal app if open
        if self.active_app_id == "terminal":
            if event.keysym == "Return":
                self.exec_terminal_cmd()
            elif event.keysym == "BackSpace":
                self.term_input = self.term_input[:-1]
            elif len(event.char) == 1 and ord(event.char) >= 32:
                self.term_input += event.char

    def open_app(self, app_id):
        self.active_app_id = app_id
        self.app_transition = 0.0

    def close_app(self):
        self.active_app_id = None
        self.app_transition = 0.0

    # ==========================================
    # APP & UI LOGIC
    # ==========================================
    def handle_homescreen_click(self, x, y):
        # Check Grid Apps
        cols = 4
        item_w = self.w // cols
        grid_start_y = 220
        icon_size = 60

        for i, app in enumerate(APPS):
            col = i % cols
            row = i // cols
            cx = col * item_w + item_w // 2
            cy = grid_start_y + row * 95
            if abs(x - cx) < icon_size // 2 + 10 and abs(y - cy) < icon_size // 2 + 10:
                self.open_app(app["id"])
                return

        # Check Dock Apps
        dock_y = self.h - 85
        dock_w = self.w * 0.88
        dock_x1 = (self.w - dock_w) // 2
        item_step = dock_w // len(PINNED_APPS)
        for i, app_id in enumerate(PINNED_APPS):
            cx = dock_x1 + i * item_step + item_step // 2
            cy = dock_y + 35
            if abs(x - cx) < 32 and abs(y - cy) < 32:
                self.open_app(app_id)
                return

    def handle_control_center_click(self, x, y):
        if y < 100 or y > self.h - 150:
            self.control_center_open = False
            return
        # Toggle buttons
        tiles = [("WiFi", 80, 180), ("Bluetooth", 180, 180), ("Dark Mode", 280, 180)]
        for name, tx, ty in tiles:
            if abs(x - tx) < 40 and abs(y - ty) < 40:
                self.settings_toggles[name] = not self.settings_toggles.get(name, True)
                return

    def handle_app_click(self, x, y):
        # Phone dialpad
        if self.active_app_id == "phone":
            keys = [
                ("1", 120, 420), ("2", 240, 420), ("3", 360, 420),
                ("4", 120, 500), ("5", 240, 500), ("6", 360, 500),
                ("7", 120, 580), ("8", 240, 580), ("9", 360, 580),
                ("*", 120, 660), ("0", 240, 660), ("#", 360, 660)
            ]
            for char, kx, ky in keys:
                if abs(x - kx) < 35 and abs(y - ky) < 35:
                    self.dial_digits += char
                    return
            # Call action button
            if abs(x - 240) < 40 and abs(y - 750) < 40:
                self.island_state = "call"
            # Delete button
            if abs(x - 360) < 35 and abs(y - 750) < 35:
                self.dial_digits = self.dial_digits[:-1]

        # Music player controls
        elif self.active_app_id == "music":
            # Play/pause button
            if abs(x - self.w // 2) < 40 and abs(y - 580) < 40:
                self.is_playing = not self.is_playing
                self.island_state = "music" if self.is_playing else "idle"

        # Calculator
        elif self.active_app_id == "calc":
            calc_keys = [
                ("C", 80, 420), ("±", 170, 420), ("%", 260, 420), ("÷", 350, 420),
                ("7", 80, 500), ("8", 170, 500), ("9", 260, 500), ("×", 350, 500),
                ("4", 80, 580), ("5", 170, 580), ("6", 260, 580), ("-", 350, 580),
                ("1", 80, 660), ("2", 170, 660), ("3", 260, 660), ("+", 350, 660),
                ("0", 125, 740), (".", 260, 740), ("=", 350, 740)
            ]
            for key, kx, ky in calc_keys:
                if abs(x - kx) < 35 and abs(y - ky) < 35:
                    self.handle_calc_input(key)
                    return

    def handle_calc_input(self, key):
        if key == "C":
            self.calc_display = "0"
        elif key == "=":
            try:
                expr = self.calc_display.replace("×", "*").replace("÷", "/")
                self.calc_display = str(eval(expr))[:10]
            except Exception:
                self.calc_display = "Error"
        else:
            if self.calc_display == "0" or self.calc_display == "Error":
                self.calc_display = key
            else:
                self.calc_display += key

    def exec_terminal_cmd(self):
        cmd = self.term_input.strip()
        self.term_lines.append(f"aether@mobile:~$ {cmd}")
        self.term_input = ""
        
        if not cmd:
            return
        if cmd == "help":
            self.term_lines.extend([
                "AetherOS Shell Commands:",
                "  status    - View system health & RAM",
                "  apps      - List available apps",
                "  clear     - Clear terminal buffer",
                "  uname -a  - Kernel and hardware specs",
                "  any standard bash command"
            ])
        elif cmd == "clear":
            self.term_lines = [""]
        elif cmd == "status":
            self.term_lines.extend([
                "CPU Architecture : ARM64 (AArch64)",
                "System Shell     : AetherOS v1.0 Fluid",
                "Render Mode      : Termux:X11 Direct",
                "Battery Level    : 88% Normal",
                "Refresh Rate     : 60 FPS Spring Engine"
            ])
        else:
            # Run local command safely
            try:
                out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=2).decode("utf-8")
                self.term_lines.extend(out.strip().split("\n")[:8])
            except Exception as e:
                self.term_lines.append(f"sh: error: {str(e)[:40]}")
                
        # Keep buffer manageable
        if len(self.term_lines) > 25:
            self.term_lines = self.term_lines[-25:]

    # ==========================================
    # RENDERING PIPELINE
    # ==========================================
    def render_loop(self):
        now = time.time()
        dt = now - self.last_frame
        self.last_frame = now

        # Animate transitions
        if self.active_app_id and self.app_transition < 1.0:
            self.app_transition = min(1.0, self.app_transition + dt * 4.5)
        elif not self.active_app_id and self.app_transition > 0.0:
            self.app_transition = max(0.0, self.app_transition - dt * 4.5)

        if self.control_center_open and self.control_center_prog < 1.0:
            self.control_center_prog = min(1.0, self.control_center_prog + dt * 5.0)
        elif not self.control_center_open and self.control_center_prog > 0.0:
            self.control_center_prog = max(0.0, self.control_center_prog - dt * 5.0)

        # Update music EQ visualizer
        if self.is_playing:
            self.eq_bars = [min(1.0, max(0.15, b + random.uniform(-0.15, 0.15))) for b in self.eq_bars]

        # Draw frame
        self.canvas.delete("all")
        self.draw_wallpaper()
        self.draw_homescreen()
        
        # Render active app modal sheet
        if self.app_transition > 0.001:
            self.draw_active_app()

        # Render pull-down Control Center
        if self.control_center_prog > 0.001:
            self.draw_control_center()

        # Render Status Bar & Dynamic Island
        self.draw_status_bar()
        self.draw_gesture_bar()

        # Schedule next frame (~60fps)
        self.root.after(16, self.render_loop)

    def draw_wallpaper(self):
        # Subtle ambient radial gradient effect
        self.canvas.create_rectangle(0, 0, self.w, self.h, fill=THEME["bg"], width=0)
        # Ambient light sphere in top right
        self.canvas.create_oval(
            self.w - 180, -60, self.w + 140, 260,
            fill="#121829", outline="", width=0
        )
        # Ambient emerald glow in bottom left
        self.canvas.create_oval(
            -80, self.h - 320, 220, self.h + 80,
            fill="#0B1C1D", outline="", width=0
        )

    def draw_status_bar(self):
        bar_y = 22
        # Left: Time
        self.canvas.create_text(
            45, bar_y, text=self.time_str,
            font=("Helvetica", 13, "bold"), fill=THEME["text_primary"]
        )

        # Right: 5G, WiFi, Battery
        rx = self.w - 38
        # Battery outline
        self.draw_squircle(rx - 28, bar_y - 8, rx, bar_y + 8, 4, "", outline=THEME["text_secondary"], width=1)
        # Battery terminal
        self.canvas.create_rectangle(rx + 1, bar_y - 4, rx + 3, bar_y + 4, fill=THEME["text_secondary"], width=0)
        # Battery fill
        fill_w = int(24 * (self.battery_level / 100))
        self.canvas.create_rectangle(rx - 26, bar_y - 6, rx - 26 + fill_w, bar_y + 6, fill=THEME["accent_emerald"], width=0)

        # Wi-Fi icon
        self.canvas.create_text(rx - 48, bar_y, text="📶", font=("Helvetica", 10), fill=THEME["text_secondary"])
        # 5G label
        self.canvas.create_text(rx - 78, bar_y, text="5G", font=("Helvetica", 10, "bold"), fill=THEME["text_primary"])

        # Center: Dynamic Island Pill
        cx = self.w // 2
        island_w = 120
        island_h = 28
        
        if self.island_state == "music":
            island_w = 190
            island_h = 32
            self.draw_squircle(cx - island_w // 2, 7, cx + island_w // 2, 7 + island_h, 16, "#000000", outline="#252A3D")
            self.canvas.create_text(cx - 65, 23, text="🎵", font=("Helvetica", 10))
            self.canvas.create_text(cx, 23, text="Starlight", font=("Helvetica", 10, "bold"), fill=THEME["accent_cyan"])
            # Tiny animated equalizer
            for idx, bar in enumerate(self.eq_bars[:4]):
                bx = cx + 55 + idx * 6
                bh = int(bar * 14)
                self.canvas.create_line(bx, 23 + bh // 2, bx, 23 - bh // 2, fill=THEME["accent_cyan"], width=2)
        elif self.island_state == "call":
            island_w = 170
            island_h = 32
            self.draw_squircle(cx - island_w // 2, 7, cx + island_w // 2, 7 + island_h, 16, "#000000", outline="#00E676")
            self.canvas.create_text(cx - 55, 23, text="📞", font=("Helvetica", 10))
            self.canvas.create_text(cx + 10, 23, text="00:14 Calling...", font=("Helvetica", 10, "bold"), fill=THEME["accent_emerald"])
        else:
            self.draw_squircle(cx - island_w // 2, 8, cx + island_w // 2, 8 + island_h, 14, "#000000", outline="#1F2333")

    def draw_homescreen(self):
        # 1. Glass Weather / Date Widget
        card_w = self.w - 48
        card_x1 = 24
        card_y1 = 65
        card_h = 115
        
        self.draw_squircle(card_x1, card_y1, card_x1 + card_w, card_y1 + card_h, 24, THEME["bg_secondary"], outline=THEME["card_border"])
        
        self.canvas.create_text(card_x1 + 24, card_y1 + 35, text=self.date_str, font=("Helvetica", 12, "bold"), fill=THEME["text_secondary"], anchor="w")
        self.canvas.create_text(card_x1 + 24, card_y1 + 75, text="72° Mostly Clear", font=("Helvetica", 20, "bold"), fill=THEME["text_primary"], anchor="w")
        self.canvas.create_text(card_x1 + card_w - 55, card_y1 + 55, text="☀️", font=("Helvetica", 36))

        # 2. App Icons Grid (4 columns)
        cols = 4
        item_w = self.w // cols
        grid_start_y = 220
        icon_size = 58
        r = 18

        for i, app in enumerate(APPS):
            col = i % cols
            row = i // cols
            cx = col * item_w + item_w // 2
            cy = grid_start_y + row * 95

            # Squircle Icon
            x1, y1 = cx - icon_size // 2, cy - icon_size // 2
            x2, y2 = cx + icon_size // 2, cy + icon_size // 2
            
            # Subtle gradient emulation with double outline
            self.draw_squircle(x1, y1, x2, y2, r, app["color"][0], outline=app["color"][1], width=1)
            # Glyph
            self.canvas.create_text(cx, cy, text=app["icon"], font=("Helvetica", 22))
            # Label
            self.canvas.create_text(cx, cy + icon_size // 2 + 14, text=app["name"], font=("Helvetica", 10, "bold"), fill=THEME["text_primary"])

        # 3. Frosted Glass Bottom Dock
        dock_y = self.h - 85
        dock_w = self.w * 0.88
        dock_x1 = (self.w - dock_w) // 2
        
        self.draw_squircle(dock_x1, dock_y, dock_x1 + dock_w, dock_y + 68, 30, THEME["bg_secondary"], outline=THEME["card_border"], width=1)

        item_step = dock_w // len(PINNED_APPS)
        for i, app_id in enumerate(PINNED_APPS):
            app = next(a for a in APPS if a["id"] == app_id)
            cx = dock_x1 + i * item_step + item_step // 2
            cy = dock_y + 34
            
            x1, y1 = cx - 25, cy - 25
            x2, y2 = cx + 25, cy + 25
            self.draw_squircle(x1, y1, x2, y2, 16, app["color"][0], outline=app["color"][1], width=1)
            self.canvas.create_text(cx, cy, text=app["icon"], font=("Helvetica", 18))

    def draw_active_app(self):
        # Smooth sliding expansion animation
        prog = ease_out_cubic(self.app_transition)
        app_y = int((1.0 - prog) * self.h)
        
        # Modal Background Card
        self.draw_squircle(0, app_y + 40, self.w, self.h, 28, THEME["bg"], outline=THEME["card_border"], width=1)
        
        # App Header
        app_meta = next((a for a in APPS if a["id"] == self.active_app_id), None)
        title = app_meta["name"] if app_meta else "Application"
        
        # Header bar
        self.canvas.create_text(self.w // 2, app_y + 70, text=title, font=("Helvetica", 16, "bold"), fill=THEME["text_primary"])
        # Close 'X' pill
        self.draw_squircle(self.w - 55, app_y + 55, self.w - 25, app_y + 85, 15, THEME["bg_secondary"], outline=THEME["card_border"])
        self.canvas.create_text(self.w - 40, app_y + 70, text="✕", font=("Helvetica", 12, "bold"), fill=THEME["text_secondary"])

        # Render App Content
        content_y = app_y + 110
        if self.active_app_id == "phone":
            self.render_phone_app(content_y)
        elif self.active_app_id == "terminal":
            self.render_terminal_app(content_y)
        elif self.active_app_id == "music":
            self.render_music_app(content_y)
        elif self.active_app_id == "settings":
            self.render_settings_app(content_y)
        elif self.active_app_id == "calc":
            self.render_calc_app(content_y)
        elif self.active_app_id == "weather":
            self.render_weather_app(content_y)
        else:
            self.render_generic_app(content_y, title)

    # --- APPS CONTENT RENDERING ---
    def render_phone_app(self, top_y):
        # Display Number
        self.canvas.create_text(
            self.w // 2, top_y + 40,
            text=self.dial_digits if self.dial_digits else "Enter number...",
            font=("Helvetica", 24, "bold"),
            fill=THEME["text_primary"] if self.dial_digits else THEME["text_muted"]
        )

        # Dialpad 3x4
        keys = [
            ("1", 120, 220), ("2", 240, 220), ("3", 360, 220),
            ("4", 120, 300), ("5", 240, 300), ("6", 360, 300),
            ("7", 120, 380), ("8", 240, 380), ("9", 360, 380),
            ("*", 120, 460), ("0", 240, 460), ("#", 360, 460)
        ]
        for char, kx, ky in keys:
            y = top_y + ky - 100
            self.draw_squircle(kx - 35, y - 35, kx + 35, y + 35, 35, THEME["bg_secondary"], outline=THEME["card_border"])
            self.canvas.create_text(kx, y, text=char, font=("Helvetica", 20, "bold"), fill=THEME["text_primary"])

        # Call Button
        cy = top_y + 440
        self.draw_squircle(205, cy - 35, 275, cy + 35, 35, THEME["accent_emerald"], outline="#00B0FF")
        self.canvas.create_text(240, cy, text="📞", font=("Helvetica", 22))

    def render_terminal_app(self, top_y):
        # Obsidian terminal card
        tw = self.w - 40
        th = self.h - top_y - 80
        self.draw_squircle(20, top_y, 20 + tw, top_y + th, 16, "#08090C", outline="#1F2438")

        # Lines buffer
        line_y = top_y + 25
        for line in self.term_lines[-18:]:
            color = THEME["accent_cyan"] if line.startswith("aether@") else THEME["text_primary"]
            self.canvas.create_text(35, line_y, text=line, font=("Courier", 11), fill=color, anchor="w")
            line_y += 20

        # Input line with blinking cursor
        cursor = "▋" if int(time.time() * 2) % 2 == 0 else ""
        self.canvas.create_text(35, line_y, text=f"aether@mobile:~$ {self.term_input}{cursor}", font=("Courier", 11, "bold"), fill=THEME["accent_emerald"], anchor="w")

    def render_music_app(self, top_y):
        cx = self.w // 2
        # Album Art Card
        art_size = 200
        self.draw_squircle(cx - art_size // 2, top_y + 20, cx + art_size // 2, top_y + 20 + art_size, 24, "#1E1233", outline=THEME["accent_purple"], width=2)
        self.canvas.create_text(cx, top_y + 120, text="🌌", font=("Helvetica", 56))

        # Track Info
        self.canvas.create_text(cx, top_y + 260, text="Starlight Protocol", font=("Helvetica", 20, "bold"), fill=THEME["text_primary"])
        self.canvas.create_text(cx, top_y + 290, text="Aether Sound Design • Flac 96kHz", font=("Helvetica", 12), fill=THEME["text_secondary"])

        # Progress Bar
        bar_w = self.w - 80
        bx1 = 40
        by = top_y + 340
        self.draw_squircle(bx1, by, bx1 + bar_w, by + 6, 3, THEME["card_border"])
        self.draw_squircle(bx1, by, bx1 + int(bar_w * self.music_pos), by + 6, 3, THEME["accent_purple"])

        # Controls
        play_symbol = "⏸" if self.is_playing else "▶"
        self.draw_squircle(cx - 35, by + 40, cx + 35, by + 110, 35, THEME["accent_purple"])
        self.canvas.create_text(cx, by + 75, text=play_symbol, font=("Helvetica", 22), fill=THEME["text_primary"])
        self.canvas.create_text(cx - 80, by + 75, text="⏮", font=("Helvetica", 22), fill=THEME["text_secondary"])
        self.canvas.create_text(cx + 80, by + 75, text="⏭", font=("Helvetica", 22), fill=THEME["text_secondary"])

    def render_settings_app(self, top_y):
        sy = top_y + 10
        card_w = self.w - 40
        for name, state in self.settings_toggles.items():
            self.draw_squircle(20, sy, 20 + card_w, sy + 60, 16, THEME["bg_secondary"], outline=THEME["card_border"])
            self.canvas.create_text(40, sy + 30, text=name, font=("Helvetica", 14, "bold"), fill=THEME["text_primary"], anchor="w")
            
            # Switch toggle
            sw_x = 20 + card_w - 60
            color = THEME["accent_emerald"] if state else THEME["card_border"]
            self.draw_squircle(sw_x, sy + 18, sw_x + 44, sy + 42, 12, color)
            knob_x = sw_x + 32 if state else sw_x + 12
            self.canvas.create_oval(knob_x - 9, sy + 21, knob_x + 9, sy + 39, fill="#FFFFFF", width=0)
            sy += 72

        # Device Info Card
        self.draw_squircle(20, sy + 10, 20 + card_w, sy + 130, 18, THEME["bg_secondary"], outline=THEME["card_border"])
        self.canvas.create_text(40, sy + 35, text="AetherOS Mobile v1.0 Fluid", font=("Helvetica", 14, "bold"), fill=THEME["accent_cyan"], anchor="w")
        self.canvas.create_text(40, sy + 65, text="Kernel: Linux 6.1 aarch64 • Termux Hybrid", font=("Helvetica", 11), fill=THEME["text_secondary"], anchor="w")
        self.canvas.create_text(40, sy + 90, text="Display: 60Hz Low Latency Compositor", font=("Helvetica", 11), fill=THEME["text_secondary"], anchor="w")

    def render_calc_app(self, top_y):
        # Screen
        self.draw_squircle(24, top_y + 10, self.w - 24, top_y + 90, 16, THEME["bg_secondary"], outline=THEME["card_border"])
        self.canvas.create_text(self.w - 45, top_y + 50, text=self.calc_display, font=("Helvetica", 28, "bold"), fill=THEME["text_primary"], anchor="e")

        # Buttons
        calc_keys = [
            ("C", 80, 140, THEME["text_muted"]), ("±", 170, 140, THEME["text_muted"]), ("%", 260, 140, THEME["text_muted"]), ("÷", 350, 140, THEME["accent_amber"]),
            ("7", 80, 220, THEME["text_primary"]), ("8", 170, 220, THEME["text_primary"]), ("9", 260, 220, THEME["text_primary"]), ("×", 350, 220, THEME["accent_amber"]),
            ("4", 80, 300, THEME["text_primary"]), ("5", 170, 300, THEME["text_primary"]), ("6", 260, 300, THEME["text_primary"]), ("-", 350, 300, THEME["accent_amber"]),
            ("1", 80, 380, THEME["text_primary"]), ("2", 170, 380, THEME["text_primary"]), ("3", 260, 380, THEME["text_primary"]), ("+", 350, 380, THEME["accent_amber"]),
            ("0", 125, 460, THEME["text_primary"]), (".", 260, 460, THEME["text_primary"]), ("=", 350, 460, THEME["accent_emerald"])
        ]
        for key, kx, ky, color in calc_keys:
            y = top_y + ky
            self.draw_squircle(kx - 35, y - 35, kx + 35, y + 35, 35, THEME["bg_secondary"], outline=THEME["card_border"])
            self.canvas.create_text(kx, y, text=key, font=("Helvetica", 18, "bold"), fill=color)

    def render_weather_app(self, top_y):
        cx = self.w // 2
        self.canvas.create_text(cx, top_y + 30, text="San Francisco", font=("Helvetica", 24, "bold"), fill=THEME["text_primary"])
        self.canvas.create_text(cx, top_y + 80, text="72°", font=("Helvetica", 54, "bold"), fill=THEME["text_primary"])
        self.canvas.create_text(cx, top_y + 125, text="Mostly Sunny • H:76° L:55°", font=("Helvetica", 12), fill=THEME["text_secondary"])

        # Hourly Cards
        hw = self.w - 40
        self.draw_squircle(20, top_y + 160, 20 + hw, top_y + 260, 20, THEME["bg_secondary"], outline=THEME["card_border"])
        hours = [("Now", "72°", "☀️"), ("1 PM", "74°", "🌤"), ("2 PM", "76°", "⛅"), ("3 PM", "75°", "☀️")]
        step = hw // len(hours)
        for i, (hr, temp, ic) in enumerate(hours):
            hx = 20 + i * step + step // 2
            self.canvas.create_text(hx, top_y + 185, text=hr, font=("Helvetica", 11), fill=THEME["text_secondary"])
            self.canvas.create_text(hx, top_y + 210, text=ic, font=("Helvetica", 18))
            self.canvas.create_text(hx, top_y + 235, text=temp, font=("Helvetica", 12, "bold"), fill=THEME["text_primary"])

    def render_generic_app(self, top_y, title):
        card_w = self.w - 40
        self.draw_squircle(20, top_y + 20, 20 + card_w, top_y + 220, 20, THEME["bg_secondary"], outline=THEME["card_border"])
        self.canvas.create_text(self.w // 2, top_y + 100, text=f"{title} Module Loaded", font=("Helvetica", 16, "bold"), fill=THEME["text_primary"])
        self.canvas.create_text(self.w // 2, top_y + 135, text="Connected to Aether Core Services", font=("Helvetica", 12), fill=THEME["text_secondary"])

    def draw_control_center(self):
        prog = ease_out_cubic(self.control_center_prog)
        cc_y = int((prog - 1.0) * 400)
        
        # Backdrop tint
        self.canvas.create_rectangle(0, 0, self.w, self.h, fill="#000000", stipple="gray50", width=0)
        
        # Panel Sheet
        self.draw_squircle(16, cc_y + 35, self.w - 16, cc_y + 360, 28, "#141724", outline=THEME["card_border"], width=1)
        
        # Header
        self.canvas.create_text(40, cc_y + 70, text="Control Center", font=("Helvetica", 15, "bold"), fill=THEME["text_primary"], anchor="w")

        # Quick Tiles (2x2)
        tiles = [("WiFi", "📶", 80, cc_y + 130), ("Bluetooth", "ᛒ", 180, cc_y + 130), ("Dark Mode", "🌙", 280, cc_y + 130)]
        for name, icon, tx, ty in tiles:
            state = self.settings_toggles.get(name, True)
            color = THEME["accent_cyan"] if state else THEME["card_border"]
            self.draw_squircle(tx - 35, ty - 35, tx + 35, ty + 35, 20, THEME["bg_secondary"], outline=color, width=2)
            self.canvas.create_text(tx, ty - 6, text=icon, font=("Helvetica", 18), fill=THEME["text_primary"])
            self.canvas.create_text(tx, ty + 18, text=name, font=("Helvetica", 9), fill=THEME["text_secondary"])

        # Sliders (Brightness & Volume)
        self.draw_squircle(50, cc_y + 200, self.w - 50, cc_y + 245, 14, THEME["bg_secondary"], outline=THEME["card_border"])
        self.canvas.create_text(70, cc_y + 222, text="☀️", font=("Helvetica", 14))
        self.draw_squircle(100, cc_y + 218, self.w - 70, cc_y + 226, 4, THEME["card_border"])
        self.draw_squircle(100, cc_y + 218, self.w - 140, cc_y + 226, 4, THEME["accent_cyan"])

        self.draw_squircle(50, cc_y + 265, self.w - 50, cc_y + 310, 14, THEME["bg_secondary"], outline=THEME["card_border"])
        self.canvas.create_text(70, cc_y + 287, text="🔊", font=("Helvetica", 14))
        self.draw_squircle(100, cc_y + 283, self.w - 70, cc_y + 291, 4, THEME["card_border"])
        self.draw_squircle(100, cc_y + 283, self.w - 180, cc_y + 291, 4, THEME["accent_emerald"])

    def draw_gesture_bar(self):
        # Bottom home pill indicator
        pill_w = 140
        pill_h = 5
        cx = self.w // 2
        cy = self.h - 14
        self.draw_squircle(cx - pill_w // 2, cy - pill_h // 2, cx + pill_w // 2, cy + pill_h // 2, 3, THEME["text_muted"])


if __name__ == "__main__":
    root = tk.Tk()
    app = AetherOS(root)
    root.mainloop()
