"""
╔══════════════════════════════════════════════════════════════════╗
║        FACE DETECTION SYSTEM  —  v6.0                          ║
║        Zero Errors  |  Beautiful UI  |  Thonny IDE Ready       ║
╚══════════════════════════════════════════════════════════════════╝

  INSTALL:  pip install opencv-python pillow numpy
  RUN:      Open in Thonny IDE → Press F5
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import os
import random


# ══════════════════════════════════════════════════
#   SAFE PIL RESIZE  (all Pillow versions)
# ══════════════════════════════════════════════════
def safe_resize(img, w, h):
    size = (max(1, w), max(1, h))
    try:
        return img.resize(size, Image.Resampling.LANCZOS)
    except AttributeError:
        pass
    try:
        return img.resize(size, Image.LANCZOS)
    except AttributeError:
        pass
    try:
        return img.resize(size, Image.ANTIALIAS)
    except AttributeError:
        pass
    return img.resize(size)


# ══════════════════════════════════════════════════
#   COLOURS & FONTS
# ══════════════════════════════════════════════════
BG_ROOT  = "#03070F"
BG_BAR   = "#060C1A"
BG_SIDE  = "#07101F"
BG_CARD  = "#0A1628"
BG_INSET = "#0D1D35"
BG_ROW   = "#0F2040"
BORDER   = "#112030"
BORDER_H = "#1E3A5F"

C_BLUE   = "#1E90FF"
C_CYAN   = "#00E5CC"
C_GREEN  = "#00D97E"
C_AMBER  = "#FFB020"
C_RED    = "#FF3B5C"
C_PURP   = "#9B6DFF"

T_WHITE  = "#EEF4FF"
T_LIGHT  = "#7DA8CC"
T_DIM    = "#3A5570"
T_DARK   = "#182A3A"

FN = "Consolas"


def dim_color(hex_c, factor):
    """Darken a hex colour — always returns valid 6-digit hex."""
    r = int(hex_c[1:3], 16)
    g = int(hex_c[3:5], 16)
    b = int(hex_c[5:7], 16)
    return "#{:02X}{:02X}{:02X}".format(
        min(255, max(0, int(r * factor))),
        min(255, max(0, int(g * factor))),
        min(255, max(0, int(b * factor))))


# ══════════════════════════════════════════════════
#   PARTICLE BACKGROUND
# ══════════════════════════════════════════════════
class Particle:
    COLS = [C_BLUE, C_CYAN, C_PURP]

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self._spawn()

    def _spawn(self):
        self.x  = random.uniform(0, self.w)
        self.y  = random.uniform(0, self.h)
        self.vx = random.uniform(-0.25, 0.25)
        self.vy = random.uniform(-0.40, -0.08)
        self.r  = random.uniform(1.0, 2.2)
        self.c  = random.choice(self.COLS)

    def step(self):
        self.x += self.vx
        self.y += self.vy
        if self.y < -4 or self.x < -4 or self.x > self.w + 4:
            self.y  = self.h + 4
            self.x  = random.uniform(0, self.w)
            self.vx = random.uniform(-0.25, 0.25)
            self.vy = random.uniform(-0.40, -0.08)


class ParticleBg(tk.Canvas):
    """Canvas with animated floating particles.
    NOTE: bg colour is passed as a constructor arg, NOT via **kw,
    to avoid duplicate-keyword clashes in subclasses."""

    def __init__(self, parent, bg_color=BG_ROOT, n=50):
        super().__init__(parent, bg=bg_color, highlightthickness=0)
        self._alive   = True
        self._n       = n
        self._pts     = []
        self._after_id = None
        self._after_id = self.after(300, self._boot)

    def _boot(self):
        self._after_id = None
        if not self._alive:
            return
        try:
            w = max(self.winfo_width(),  500)
            h = max(self.winfo_height(), 400)
        except Exception:
            return
        self._pts = [Particle(w, h) for _ in range(self._n)]
        self._loop()

    def _loop(self):
        self._after_id = None
        if not self._alive:
            return
        try:
            self.delete("p")
            for pt in self._pts:
                pt.step()
                r  = max(1, int(pt.r))
                gc = dim_color(pt.c, 0.12)
                self.create_oval(pt.x - r*2, pt.y - r*2,
                                 pt.x + r*2, pt.y + r*2,
                                 fill="", outline=gc, tags="p")
                self.create_oval(pt.x - r,   pt.y - r,
                                 pt.x + r,   pt.y + r,
                                 fill=pt.c,  outline="", tags="p")
        except Exception:
            self._alive = False
            return
        if self._alive:
            self._after_id = self.after(40, self._loop)

    def kill(self):
        self._alive = False
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None


# ══════════════════════════════════════════════════
#   GLOW BUTTON  (extends tk.Canvas — NO bg in **kw)
# ══════════════════════════════════════════════════
class GlowBtn(tk.Canvas):
    """Animated neon button.
    bg_color sets the canvas background explicitly.
    Do NOT pass bg= when constructing this widget."""

    def __init__(self, parent, text, cmd,
                 color=C_BLUE, bg_color=BG_SIDE,
                 btn_w=220, btn_h=42, icon=""):
        # Explicit args only — no **kw to avoid duplicate bg
        super().__init__(parent,
                         width=btn_w, height=btn_h,
                         bg=bg_color,
                         highlightthickness=0,
                         cursor="hand2")
        self._text  = text
        self._cmd   = cmd
        self._color = color
        self._icon  = icon
        self._bw    = btn_w
        self._bh    = btn_h
        self._hover = False
        self._paint()
        self.bind("<Enter>",    lambda e: self._enter())
        self.bind("<Leave>",    lambda e: self._leave())
        self.bind("<Button-1>", lambda e: self._click())

    def _enter(self):
        self._hover = True
        self._paint()

    def _leave(self):
        self._hover = False
        self._paint()

    def _click(self):
        self._paint(flash=True)
        self.after(100, self._paint)
        if self._cmd:
            self._cmd()

    def _paint(self, flash=False):
        self.delete("all")
        w, h = self._bw, self._bh
        p    = 2
        col  = self._color
        fill = BG_ROW if (self._hover or flash) else BG_CARD

        if self._hover or flash:
            for g in range(4, 0, -1):
                gc = dim_color(col, 0.05 * g)
                self.create_rectangle(p-g, p-g, w-p+g, h-p+g,
                                      outline=gc, fill="")

        bw = 2 if (self._hover or flash) else 1
        bc = col if (self._hover or flash) else BORDER_H
        self.create_rectangle(p, p, w-p, h-p,
                              outline=bc, fill=fill, width=bw)
        self.create_rectangle(p, p, p+4, h-p, fill=col, outline="")

        if self._icon:
            self.create_text(p+17, h//2,
                             text=self._icon,
                             font=("Segoe UI Emoji", 12),
                             fill=col)

        tx = p + (31 if self._icon else 14)
        tc = T_WHITE if self._hover else col
        self.create_text(tx, h//2, text=self._text,
                         font=(FN, 9, "bold"),
                         fill=tc, anchor="w")

        if self._hover:
            self.create_text(w-12, h//2, text=">",
                             font=(FN, 12, "bold"), fill=col)


# ══════════════════════════════════════════════════
#   TOGGLE SWITCH  (extends tk.Frame — bg explicit)
# ══════════════════════════════════════════════════
class Toggle(tk.Frame):
    """Sliding toggle switch.
    bg_color sets the Frame background explicitly.
    Do NOT pass bg= when constructing this widget."""

    def __init__(self, parent, label, var,
                 cmd=None, bg_color=BG_SIDE):
        # Explicit bg — no **kw
        super().__init__(parent, bg=bg_color)
        self._var = var
        self._cmd = cmd
        self._bg  = bg_color

        self._cv = tk.Canvas(self, width=36, height=18,
                             bg=bg_color,
                             highlightthickness=0,
                             cursor="hand2")
        self._cv.pack(side="left", padx=(8, 6), pady=6)

        self._lbl = tk.Label(self, text=label,
                             font=(FN, 8),
                             bg=bg_color, fg=T_LIGHT,
                             cursor="hand2")
        self._lbl.pack(side="left", pady=6)

        self._draw()
        for w in (self._cv, self._lbl, self):
            w.bind("<Button-1>", self._click)

    def _draw(self):
        self._cv.delete("all")
        on  = self._var.get()
        bg_ = C_BLUE if on else T_DARK
        self._cv.create_rectangle(0, 3, 36, 15, fill=bg_, outline="")
        cx  = 26 if on else 10
        col = C_CYAN if on else T_DIM
        self._cv.create_oval(cx-7, 1, cx+7, 17, fill=col, outline="")

    def _click(self, *_):
        self._var.set(not self._var.get())
        self._draw()
        if self._cmd:
            self._cmd()


# ══════════════════════════════════════════════════
#   FACE DETECTOR ENGINE
# ══════════════════════════════════════════════════
class FaceDetector:
    PALETTES = {
        "blue":   ((30,  144, 255), (0,   80, 180)),
        "cyan":   ((0,   229, 204), (0,  160, 140)),
        "green":  ((0,   217, 126), (0,  140,  70)),
        "amber":  ((255, 176,  32), (180, 110,   0)),
        "red":    ((255,  59,  92), (180,  20,  50)),
        "purple": ((155, 109, 255), (90,   50, 180)),
    }

    def __init__(self):
        haars = cv2.data.haarcascades  # type: ignore[attr-defined]
        self._face  = cv2.CascadeClassifier(
            haars + "haarcascade_frontalface_default.xml")
        self._eye   = cv2.CascadeClassifier(
            haars + "haarcascade_eye.xml")
        self._smile = cv2.CascadeClassifier(
            haars + "haarcascade_smile.xml")

        self.scale     = 1.15
        self.neighbors = 6
        self.min_sz    = (60, 60)
        self.eyes_on   = True
        self.smile_on  = True
        self.blur_on   = False
        self.style     = "bracket"
        self.palette   = "blue"
        self._tick     = 0

    def detect(self, frame):
        self._tick += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.equalizeHist(gray, gray)

        raw = self._face.detectMultiScale(
            gray,
            scaleFactor=self.scale,
            minNeighbors=self.neighbors,
            minSize=self.min_sz,
            flags=cv2.CASCADE_SCALE_IMAGE)

        c1, c2    = self.PALETTES[self.palette]
        info_list = []

        faces = raw if (hasattr(raw, "__len__") and len(raw)) else []

        for idx, (x, y, w, h) in enumerate(faces):
            roi_g = gray[y:y+h, x:x+w]
            roi_c = frame[y:y+h, x:x+w]
            info  = {"id": idx+1, "smile": False, "eyes": 0}

            if self.blur_on:
                frame[y:y+h, x:x+w] = cv2.GaussianBlur(roi_c, (55, 55), 0)

            if self.eyes_on:
                eyes = self._eye.detectMultiScale(
                    roi_g, scaleFactor=1.1,
                    minNeighbors=8, minSize=(20, 20))
                n_eyes = len(eyes) if hasattr(eyes, "__len__") else 0
                info["eyes"] = n_eyes
                for (ex, ey, ew, eh) in (eyes if n_eyes else []):
                    cx_ = ex + ew//2
                    cy_ = ey + eh//2
                    cv2.circle(roi_c, (cx_, cy_), ew//2, c2[::-1], 1)
                    cv2.circle(roi_c, (cx_, cy_), 3,     c1[::-1], -1)

            if self.smile_on:
                sm = self._smile.detectMultiScale(
                    roi_g, scaleFactor=1.6, minNeighbors=20)
                info["smile"] = hasattr(sm, "__len__") and len(sm) > 0

            self._draw_box(frame, x, y, w, h, c1, c2, info)
            info_list.append(info)

        return frame, len(info_list), info_list

    def _draw_box(self, frm, x, y, w, h, c1, c2, info):
        b1 = c1[::-1]
        b2 = c2[::-1]
        s  = self.style

        if s == "bracket":
            cv2.rectangle(frm, (x-2, y-2), (x+w+2, y+h+2), b2, 1)
            L = min(w, h) // 5
            for (px, py, dx, dy) in [(x,y,1,1),(x+w,y,-1,1),
                                      (x,y+h,1,-1),(x+w,y+h,-1,-1)]:
                cv2.line(frm, (px, py), (px+dx*L, py), b1, 3)
                cv2.line(frm, (px, py), (px, py+dy*L), b1, 3)

        elif s == "rect":
            cv2.rectangle(frm, (x, y), (x+w, y+h), b2, 4)
            cv2.rectangle(frm, (x, y), (x+w, y+h), b1, 2)

        elif s == "cyber":
            pts = np.array([[x+10, y], [x+w-10, y],
                             [x+w, y+10], [x+w, y+h-10],
                             [x+w-10, y+h], [x+10, y+h],
                             [x, y+h-10], [x, y+10]], np.int32)
            cv2.polylines(frm, [pts], True, b1, 2)

        elif s == "minimal":
            L = 16
            for (px, py, dx, dy) in [(x,y,1,1),(x+w,y,-1,1),
                                      (x,y+h,1,-1),(x+w,y+h,-1,-1)]:
                cv2.line(frm, (px, py), (px+dx*L, py), b1, 2)
                cv2.line(frm, (px, py), (px, py+dy*L), b1, 2)

        # ID badge
        cv2.rectangle(frm, (x, y-26), (x+52, y), b1, -1)
        cv2.putText(frm, f"#{info['id']:02d}", (x+5, y-7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48,
                    (0, 0, 0), 1, cv2.LINE_AA)

        if info["smile"]:
            cv2.putText(frm, ":)", (x+w-28, y-7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                        b1, 1, cv2.LINE_AA)


# ══════════════════════════════════════════════════
#   MAIN APPLICATION
# ══════════════════════════════════════════════════
class FaceDetectionApp:
    def __init__(self, root):
        self.root    = root
        self.root.title("FACE DETECTION SYSTEM")
        self.root.configure(bg=BG_ROOT)
        self.root.minsize(1200, 720)

        self.det     = FaceDetector()
        self.cap     = None
        self.running = False
        self.paused  = False
        self._thread = None
        self._pbg    = None
        self._photo  = None      # hard ref keeps PhotoImage alive

        # Shutdown / after() tracking
        self._alive      = True          # set False in on_close()
        self._clock_id   = None          # after() id for clock
        self._render_ids = set()         # after() ids for render calls

        self._fc         = 0
        self._fps        = 0
        self._fps_buf    = []
        self._total      = 0
        self._peak       = 0
        self._sess_start = None

        # Tkinter vars
        self.v_fps    = tk.StringVar(value="—")
        self.v_count  = tk.StringVar(value="0")
        self.v_total  = tk.StringVar(value="0")
        self.v_peak   = tk.StringVar(value="0")
        self.v_frames = tk.StringVar(value="0")
        self.v_res    = tk.StringVar(value="—")
        self.v_sess   = tk.StringVar(value="00:00")
        self.v_status = tk.StringVar(value="OFFLINE")

        self.v_scale  = tk.DoubleVar(value=1.15)
        self.v_neigh  = tk.IntVar(value=6)
        self.v_minsz  = tk.IntVar(value=60)
        self.v_eyes   = tk.BooleanVar(value=True)
        self.v_smile  = tk.BooleanVar(value=True)
        self.v_blur   = tk.BooleanVar(value=False)
        self.v_style  = tk.StringVar(value="bracket")
        self.v_cam    = tk.IntVar(value=0)

        self._build_ui()
        self._clock_id = self.root.after(1000, self._clock_loop)

    # ─────────────────────────────────────────────
    #  BUILD UI
    # ─────────────────────────────────────────────

    def _build_ui(self):
        self._build_topbar()
        body = tk.Frame(self.root, bg=BG_ROOT)
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        left   = self._build_left(body)
        center = self._build_center(body)
        right  = self._build_right(body)

        left.pack(side="left",  fill="y",                padx=(0, 5))
        center.pack(side="left", fill="both", expand=True, padx=5)
        right.pack(side="left",  fill="y",                padx=(5, 0))

    # ── TOP BAR ──────────────────────────────────

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=BG_BAR, height=62)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Frame(bar, bg=C_BLUE, width=6).pack(side="left", fill="y")

        tf = tk.Frame(bar, bg=BG_BAR)
        tf.pack(side="left", padx=16, pady=8)

        tk.Label(tf, text="FACE",
                 font=(FN, 22, "bold"), fg=C_BLUE,  bg=BG_BAR).pack(side="left")
        tk.Label(tf, text=" DETECTION",
                 font=(FN, 22, "bold"), fg=T_WHITE, bg=BG_BAR).pack(side="left")
        tk.Label(tf, text=" SYSTEM",
                 font=(FN, 22, "bold"), fg=C_CYAN,  bg=BG_BAR).pack(side="left")
        tk.Label(tf, text="   v6.0  |  OpenCV + Tkinter",
                 font=(FN, 8), fg=T_DIM, bg=BG_BAR).pack(
                     side="left", pady=(14, 0))

        rf = tk.Frame(bar, bg=BG_BAR)
        rf.pack(side="right", padx=18, pady=10)

        fps_box = tk.Frame(rf, bg=BG_CARD, padx=12, pady=4)
        fps_box.pack(side="right", padx=6)
        self._fps_lbl = tk.Label(fps_box,
                                 textvariable=self.v_fps,
                                 font=(FN, 18, "bold"),
                                 fg=C_CYAN, bg=BG_CARD)
        self._fps_lbl.pack(side="left")
        tk.Label(fps_box, text=" FPS",
                 font=(FN, 8), fg=T_DIM, bg=BG_CARD).pack(
                     side="left", pady=(4, 0))

        self._badge = tk.Label(rf,
                               textvariable=self.v_status,
                               font=(FN, 10, "bold"),
                               fg=T_DIM, bg=T_DARK,
                               padx=14, pady=4)
        self._badge.pack(side="right", padx=6)

        tk.Frame(self.root, bg=BORDER_H, height=1).pack(fill="x")

    # ── LEFT PANEL ───────────────────────────────

    def _build_left(self, parent):
        frame = tk.Frame(parent, bg=BG_SIDE, width=244)
        frame.pack_propagate(False)

        self._sec(frame, "CAMERA SOURCE")

        cam_f = tk.Frame(frame, bg=BG_CARD)
        cam_f.pack(fill="x", padx=10, pady=(2, 6))
        tk.Label(cam_f, text="  Camera Index",
                 font=(FN, 8), fg=T_DIM, bg=BG_CARD).pack(
                     side="left", pady=8)
        tk.Spinbox(cam_f, from_=0, to=9,
                   textvariable=self.v_cam, width=3,
                   font=(FN, 9), bg=BG_INSET, fg=C_CYAN,
                   buttonbackground=BG_CARD, relief="flat",
                   insertbackground=C_CYAN).pack(
                       side="right", padx=8, pady=5)

        # Buttons — use bg_color= NOT bg=
        btns = [
            ("▶", "START CAMERA",    self._start_cam,    C_BLUE),
            ("■", "STOP CAMERA",     self._stop_cam,     C_RED),
            ("⏸", "PAUSE / RESUME",  self._toggle_pause, C_AMBER),
            ("📂", "OPEN VIDEO FILE", self._open_file,    C_PURP),
            ("📸", "CAPTURE FRAME",  self._capture,      C_GREEN),
        ]
        for icon, lbl, cmd, col in btns:
            GlowBtn(frame, lbl, cmd,
                    color=col, bg_color=BG_SIDE,
                    icon=icon, btn_w=222, btn_h=42
                    ).pack(padx=10, pady=2)

        self._div(frame)
        self._sec(frame, "DETECTION SETTINGS")

        self._slider(frame, "Scale Factor",       self.v_scale, 1.05, 1.5,  0.01)
        self._slider(frame, "Min Neighbors",      self.v_neigh, 2,    20,   1)
        self._slider(frame, "Min Face Size (px)", self.v_minsz, 40,   200,  10)

        tk.Label(frame,
                 text="  ↑ Raise Min Neighbors + Min Size\n"
                      "    to stop false detections",
                 font=(FN, 7), fg=T_DIM, bg=BG_SIDE,
                 justify="left").pack(anchor="w", padx=10, pady=(0, 4))

        self._div(frame)
        self._sec(frame, "FEATURES")

        # Toggles — use bg_color= NOT bg=
        for lbl, var in [("Detect Eyes",   self.v_eyes),
                         ("Detect Smiles", self.v_smile),
                         ("Privacy Blur",  self.v_blur)]:
            Toggle(frame, lbl, var,
                   cmd=self._apply,
                   bg_color=BG_SIDE).pack(fill="x", padx=10, pady=1)

        self._div(frame)
        self._sec(frame, "BOX STYLE")

        sf = tk.Frame(frame, bg=BG_SIDE)
        sf.pack(fill="x", padx=10, pady=4)
        for i, s in enumerate(["bracket", "rect", "cyber", "minimal"]):
            tk.Radiobutton(
                sf, text=s.upper(),
                variable=self.v_style, value=s,
                command=self._apply,
                font=(FN, 7, "bold"),
                fg=C_BLUE, bg=BG_SIDE,
                selectcolor=BG_CARD,
                activebackground=BG_SIDE,
                activeforeground=C_CYAN,
                indicatoron=True
            ).grid(row=i//2, column=i%2, sticky="w", padx=6, pady=2)

        self._div(frame)
        self._sec(frame, "BOX COLOUR")

        pf = tk.Frame(frame, bg=BG_SIDE)
        pf.pack(fill="x", padx=10, pady=4)
        self._pal_btns = {}
        for ci, (name, col) in enumerate([
            ("blue",   C_BLUE),  ("cyan",   C_CYAN),
            ("green",  C_GREEN), ("amber",  C_AMBER),
            ("red",    C_RED),   ("purple", C_PURP),
        ]):
            b = tk.Button(pf, bg=col, width=3, height=1,
                          relief="flat", cursor="hand2",
                          command=lambda n=name: self._set_pal(n))
            b.grid(row=0, column=ci, padx=2, pady=3)
            self._pal_btns[name] = b
        self._set_pal("blue")

        return frame

    # ── CENTER PANEL ─────────────────────────────

    def _build_center(self, parent):
        frame = tk.Frame(parent, bg=BG_ROOT)

        vid_border = tk.Frame(frame, bg=BORDER_H)
        vid_border.pack(fill="both", expand=True, pady=(0, 5))
        vid_inner = tk.Frame(vid_border, bg=BG_ROOT)
        vid_inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Particle background — use bg_color= NOT bg=
        self._pbg = ParticleBg(vid_inner, bg_color=BG_ROOT, n=50)
        self._pbg.place(relwidth=1.0, relheight=1.0)

        # Video canvas on top
        self.vcanvas = tk.Canvas(vid_inner, bg=BG_ROOT,
                                 highlightthickness=0)
        self.vcanvas.place(relwidth=1.0, relheight=1.0)
        self.vcanvas.bind("<Configure>", lambda e: self._idle_screen())
        self.vcanvas.after(500, self._idle_screen)

        # Stats bar
        sbar = tk.Frame(frame, bg=BG_BAR, height=54)
        sbar.pack(fill="x")
        sbar.pack_propagate(False)

        for lbl, var, col in [
            ("LIVE FPS",      self.v_fps,    C_CYAN),
            ("FACES NOW",     self.v_count,  C_GREEN),
            ("TOTAL COUNTED", self.v_total,  C_BLUE),
            ("PEAK",          self.v_peak,   C_AMBER),
            ("FRAMES",        self.v_frames, C_PURP),
            ("RESOLUTION",    self.v_res,    T_LIGHT),
        ]:
            chip = tk.Frame(sbar, bg=BG_CARD)
            chip.pack(side="left", fill="y", padx=2, pady=5)
            tk.Frame(chip, bg=col, width=3).pack(side="left", fill="y")
            inn = tk.Frame(chip, bg=BG_CARD)
            inn.pack(side="left", padx=8, pady=4)
            tk.Label(inn, text=lbl, font=(FN, 7, "bold"),
                     fg=T_DIM, bg=BG_CARD).pack(anchor="w")
            tk.Label(inn, textvariable=var,
                     font=(FN, 14, "bold"), fg=col,
                     bg=BG_CARD).pack(anchor="w")

        return frame

    # ── RIGHT PANEL ──────────────────────────────

    def _build_right(self, parent):
        frame = tk.Frame(parent, bg=BG_SIDE, width=218)
        frame.pack_propagate(False)

        # Big face counter
        self._sec(frame, "FACES DETECTED")

        count_outer = tk.Frame(frame, bg=BG_CARD)
        count_outer.pack(fill="x", padx=10, pady=(4, 6))
        tk.Frame(count_outer, bg=C_GREEN, width=5).pack(side="left", fill="y")

        count_inner = tk.Frame(count_outer, bg=BG_CARD, padx=14, pady=10)
        count_inner.pack(side="left", fill="both", expand=True)

        self._lbl_count = tk.Label(count_inner,
                                   textvariable=self.v_count,
                                   font=(FN, 64, "bold"),
                                   fg=C_GREEN, bg=BG_CARD)
        self._lbl_count.pack()
        tk.Label(count_inner, text="people in frame",
                 font=(FN, 8), fg=T_DIM, bg=BG_CARD).pack()

        tk.Frame(count_outer, bg=C_GREEN, width=5).pack(side="right", fill="y")

        # Session stats
        self._div(frame)
        self._sec(frame, "SESSION STATS")

        for lbl, var, col in [
            ("PEAK FACES",   self.v_peak,   C_AMBER),
            ("TOTAL FACES",  self.v_total,  C_BLUE),
            ("SESSION TIME", self.v_sess,   C_CYAN),
            ("RESOLUTION",   self.v_res,    T_LIGHT),
            ("FRAME COUNT",  self.v_frames, C_PURP),
        ]:
            row = tk.Frame(frame, bg=BG_ROW)
            row.pack(fill="x", padx=10, pady=1)
            tk.Label(row, text=lbl, font=(FN, 7, "bold"),
                     fg=T_DIM, bg=BG_ROW, padx=8).pack(side="left", pady=7)
            tk.Label(row, textvariable=var, font=(FN, 9, "bold"),
                     fg=col, bg=BG_ROW, padx=8).pack(side="right", pady=7)

        # Event log
        self._div(frame)
        self._sec(frame, "EVENT LOG")

        log_wrap = tk.Frame(frame, bg=BG_ROOT)
        log_wrap.pack(fill="both", expand=True, padx=10, pady=(2, 4))

        sb = tk.Scrollbar(log_wrap, bg=BG_CARD,
                          troughcolor=BG_ROOT, width=7)
        sb.pack(side="right", fill="y")

        self._logbox = tk.Text(log_wrap, font=(FN, 7),
                               bg=BG_ROOT, fg=T_DIM,
                               relief="flat", wrap="word",
                               yscrollcommand=sb.set,
                               insertbackground=C_CYAN,
                               selectbackground=BG_CARD)
        self._logbox.pack(fill="both", expand=True)
        sb.config(command=self._logbox.yview)

        for tag, col in [("ts",   T_DARK), ("face", C_CYAN),
                         ("good", C_GREEN), ("warn", C_AMBER),
                         ("err",  C_RED),   ("info", T_DIM)]:
            self._logbox.tag_config(tag, foreground=col)
        self._logbox.config(state="disabled")

        # Clear log button — use bg_color=
        GlowBtn(frame, "CLEAR LOG", self._clear_log,
                color=T_DIM, bg_color=BG_SIDE,
                btn_w=196, btn_h=38, icon="🗑"
                ).pack(padx=10, pady=4)

        return frame

    # ─────────────────────────────────────────────
    #  HELPER WIDGETS
    # ─────────────────────────────────────────────

    def _sec(self, parent, text):
        f = tk.Frame(parent, bg=BG_SIDE)
        f.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(f, text=text, font=(FN, 7, "bold"),
                 fg=C_BLUE, bg=BG_SIDE).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(
            side="left", fill="x", expand=True, padx=6)

    def _div(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(
            fill="x", padx=10, pady=2)

    def _slider(self, parent, label, var, lo, hi, res):
        wrap = tk.Frame(parent, bg=BG_SIDE)
        wrap.pack(fill="x", padx=10, pady=3)
        top = tk.Frame(wrap, bg=BG_SIDE)
        top.pack(fill="x")
        tk.Label(top, text=label, font=(FN, 7),
                 fg=T_LIGHT, bg=BG_SIDE).pack(side="left")
        tk.Label(top, textvariable=var, font=(FN, 7, "bold"),
                 fg=C_CYAN, bg=BG_SIDE, width=5).pack(side="right")
        tk.Scale(wrap, variable=var, from_=lo, to=hi, resolution=res,
                 orient="horizontal", command=self._apply,
                 showvalue=False, bg=BG_SIDE, fg=C_CYAN,
                 troughcolor=BG_INSET, activebackground=C_BLUE,
                 highlightthickness=0, relief="flat",
                 sliderlength=14, length=218, bd=0).pack()

    # ─────────────────────────────────────────────
    #  IDLE SCREEN
    # ─────────────────────────────────────────────

    def _idle_screen(self):
        try:
            self.vcanvas.delete("idle")
            w  = self.vcanvas.winfo_width()  or 720
            h  = self.vcanvas.winfo_height() or 480
            cx, cy = w//2, h//2

            bw, bh = 220, 190
            bx, by = cx-bw//2, cy-bh//2
            self.vcanvas.create_rectangle(
                bx, by, bx+bw, by+bh,
                outline=BORDER_H, fill="", dash=(6, 4), tags="idle")

            L = 18
            for (px, py, dx, dy) in [(bx,by,1,1),(bx+bw,by,-1,1),
                                      (bx,by+bh,1,-1),(bx+bw,by+bh,-1,-1)]:
                self.vcanvas.create_line(
                    px, py, px+dx*L, py, fill=C_BLUE, width=2, tags="idle")
                self.vcanvas.create_line(
                    px, py, px, py+dy*L, fill=C_BLUE, width=2, tags="idle")

            # Face silhouette
            self.vcanvas.create_oval(cx-28, cy-52, cx+28, cy+28,
                                      outline=BORDER_H, fill="", tags="idle")
            self.vcanvas.create_line(cx-28, cy+28, cx-48, cy+80,
                                      fill=BORDER_H, tags="idle")
            self.vcanvas.create_line(cx+28, cy+28, cx+48, cy+80,
                                      fill=BORDER_H, tags="idle")

            self.vcanvas.create_text(cx, cy+108,
                                      text="PRESS  ▶ START CAMERA  TO BEGIN",
                                      font=(FN, 10, "bold"),
                                      fill=BORDER_H, tags="idle")
            self.vcanvas.create_text(cx, cy+130,
                                      text="FACE DETECTION SYSTEM  |  OpenCV + Tkinter",
                                      font=(FN, 7, "bold"),
                                      fill=T_DARK, tags="idle")
        except Exception:
            pass

    # ─────────────────────────────────────────────
    #  SETTINGS
    # ─────────────────────────────────────────────

    def _apply(self, *_):
        self.det.scale     = round(self.v_scale.get(), 2)
        self.det.neighbors = self.v_neigh.get()
        sz = self.v_minsz.get()
        self.det.min_sz    = (sz, sz)
        self.det.eyes_on   = self.v_eyes.get()
        self.det.smile_on  = self.v_smile.get()
        self.det.blur_on   = self.v_blur.get()
        self.det.style     = self.v_style.get()

    def _set_pal(self, name):
        self.det.palette = name
        for n, b in self._pal_btns.items():
            try:
                b.config(relief="sunken" if n == name else "flat",
                         bd=3 if n == name else 0)
            except Exception:
                pass

    # ─────────────────────────────────────────────
    #  CAMERA
    # ─────────────────────────────────────────────

    def _start_cam(self):
        if self.running:
            self.log("Already running.", "warn")
            return
        idx = self.v_cam.get()
        self.cap = cv2.VideoCapture(idx)
        if not self.cap.isOpened():
            messagebox.showerror(
                "Camera Error",
                f"Cannot open camera index {idx}.\n"
                "Try index 0, 1, or 2.\n"
                "Make sure your webcam is connected.")
            self.log(f"Camera {idx} failed.", "err")
            return
        self._begin_stream()
        self.log(f"Camera {idx} started.", "good")

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Open Video File",
            filetypes=[("Video files",
                        "*.mp4 *.avi *.mov *.mkv *.wmv"),
                       ("All files", "*.*")])
        if not path:
            return
        if self.running:
            self._stop_cam()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Cannot open:\n{path}")
            return
        self._begin_stream()
        self.log(f"Video: {os.path.basename(path)}", "good")

    def _begin_stream(self):
        self.running     = True
        self.paused      = False
        self._fc         = 0
        self._total      = 0
        self._peak       = 0
        self._sess_start = time.time()
        self._fps_buf    = []
        self._apply()
        self._set_status("LIVE", C_GREEN, dim_color(C_GREEN, 0.12))
        self._thread = threading.Thread(
            target=self._stream_loop, daemon=True)
        self._thread.start()

    def _stop_cam(self):
        self.running = False
        self.paused  = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self._set_status("OFFLINE", T_DIM, T_DARK)
        try:
            self.vcanvas.delete("all")
            self._idle_screen()
        except Exception:
            pass
        self.v_count.set("0")
        self.log("Camera stopped.", "warn")

    def _toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        if self.paused:
            self._set_status("PAUSED", C_AMBER,
                             dim_color(C_AMBER, 0.10))
            self.log("Paused.", "warn")
        else:
            self._set_status("LIVE", C_GREEN,
                             dim_color(C_GREEN, 0.12))
            self.log("Resumed.", "good")

    def _set_status(self, text, fg, bg):
        self.v_status.set(text)
        try:
            self._badge.config(fg=fg, bg=bg)
        except Exception:
            pass

    # ─────────────────────────────────────────────
    #  STREAM LOOP
    # ─────────────────────────────────────────────

    def _stream_loop(self):
        while self.running:
            if self.paused:
                time.sleep(0.05)
                continue
            if self.cap is None:
                break
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            self._fc += 1
            now = time.time()
            self._fps_buf.append(now)
            self._fps_buf = [t for t in self._fps_buf if now - t < 1.0]
            self._fps = len(self._fps_buf)

            frame, n, _ = self.det.detect(frame)
            if n > 0:
                self._total += n
                self._peak   = max(self._peak, n)

            try:
                if self._alive:
                    aid = self.root.after(0, self._render, frame, n)
                    self._render_ids.add(aid)
            except Exception:
                break

    # ─────────────────────────────────────────────
    #  RENDER  — PhotoImage stored as self._photo
    # ─────────────────────────────────────────────

    def _render(self, frame, n):
        # Remove this call's id from tracking (it has now fired)
        self._render_ids.discard(id(frame))
        if not self._alive or not self.running:
            return
        try:
            h, w = frame.shape[:2]
            rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img  = Image.fromarray(rgb)

            cw = self.vcanvas.winfo_width()  or 640
            ch = self.vcanvas.winfo_height() or 480
            scale = min(cw / w, ch / h)
            nw    = max(1, int(w * scale))
            nh    = max(1, int(h * scale))

            img = safe_resize(img, nw, nh)

            # Keep hard reference BEFORE assigning to canvas
            self._photo = ImageTk.PhotoImage(image=img)

            self.vcanvas.delete("all")
            x0 = (cw - nw) // 2
            y0 = (ch - nh) // 2

            self.vcanvas.create_image(cw//2, ch//2,
                                       image=self._photo,
                                       anchor="center")

            # Border glow
            edge = C_GREEN if n > 0 else C_BLUE
            glow = dim_color(edge, 0.18)
            self.vcanvas.create_rectangle(
                x0-3, y0-3, x0+nw+3, y0+nh+3,
                outline=glow, width=4)
            self.vcanvas.create_rectangle(
                x0, y0, x0+nw, y0+nh,
                outline=edge, width=1)

            # Corner brackets overlay
            L = 22
            for (bx, by, dx, dy) in [
                (x0,    y0,     1,  1),
                (x0+nw, y0,    -1,  1),
                (x0,    y0+nh,  1, -1),
                (x0+nw, y0+nh, -1, -1),
            ]:
                self.vcanvas.create_line(
                    bx, by, bx+dx*L, by, fill=edge, width=2)
                self.vcanvas.create_line(
                    bx, by, bx, by+dy*L, fill=edge, width=2)

            # Face count badge on video
            if n > 0:
                label = f"  {n} FACE{'S' if n > 1 else ''}  "
                bx0 = x0 + nw - 104
                by0 = y0 + 4
                self.vcanvas.create_rectangle(
                    bx0, by0, bx0+100, by0+24,
                    fill=C_GREEN, outline="")
                self.vcanvas.create_text(
                    bx0+50, by0+12, text=label,
                    font=(FN, 8, "bold"), fill=BG_ROOT)

            # Update stats
            fps_val = int(self._fps)
            self.v_fps.set(str(fps_val))
            self.v_count.set(str(n))
            self.v_total.set(str(self._total))
            self.v_peak.set(str(self._peak))
            self.v_frames.set(str(self._fc))
            self.v_res.set(f"{w}x{h}")

            fps_col = (C_GREEN if fps_val > 24 else
                       C_AMBER if fps_val > 12 else C_RED)
            self._fps_lbl.config(fg=fps_col)
            self._lbl_count.config(fg=C_GREEN if n > 0 else T_DIM)

            if self._sess_start:
                e = int(time.time() - self._sess_start)
                self.v_sess.set(f"{e//60:02d}:{e%60:02d}")

            if n > 0 and self._fc % 30 == 0:
                self.log(f"{n} face(s) in frame {self._fc}", "face")

        except Exception:
            pass

    # ─────────────────────────────────────────────
    #  CAPTURE
    # ─────────────────────────────────────────────

    def _capture(self):
        if not self.running or self.cap is None:
            messagebox.showinfo("Capture", "No live feed active.")
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        out, _, _ = self.det.detect(frame)
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")],
            title="Save Captured Frame")
        if path:
            cv2.imwrite(path, out)
            self.log(f"Saved -> {os.path.basename(path)}", "good")
            messagebox.showinfo("Saved", f"Frame saved:\n{path}")

    # ─────────────────────────────────────────────
    #  LOG
    # ─────────────────────────────────────────────

    def log(self, msg, tag="info"):
        try:
            ts = time.strftime("%H:%M:%S")
            self._logbox.config(state="normal")
            self._logbox.insert("end", f"[{ts}] ", "ts")
            self._logbox.insert("end", f"{msg}\n", tag)
            self._logbox.see("end")
            self._logbox.config(state="disabled")
        except Exception:
            pass

    def _clear_log(self):
        try:
            self._logbox.config(state="normal")
            self._logbox.delete("1.0", "end")
            self._logbox.config(state="disabled")
        except Exception:
            pass

    # ─────────────────────────────────────────────
    #  CLOCK
    # ─────────────────────────────────────────────

    def _clock_loop(self):
        if not self._alive:
            return
        try:
            if self._sess_start:
                e = int(time.time() - self._sess_start)
                self.v_sess.set(f"{e//60:02d}:{e%60:02d}")
        except Exception:
            pass
        if self._alive:
            self._clock_id = self.root.after(1000, self._clock_loop)

    # ─────────────────────────────────────────────
    #  CLOSE
    # ─────────────────────────────────────────────

    def on_close(self):
        # 1. Stop the alive flag so ALL after() loops self-exit
        self._alive  = False
        self.running = False

        # 2. Cancel clock after() explicitly
        if self._clock_id is not None:
            try:
                self.root.after_cancel(self._clock_id)
            except Exception:
                pass

        # 3. Cancel any pending render callbacks
        for aid in list(self._render_ids):
            try:
                self.root.after_cancel(aid)
            except Exception:
                pass
        self._render_ids.clear()

        # 4. Kill particle background
        if self._pbg:
            self._pbg.kill()

        # 5. Release camera
        if self.cap:
            self.cap.release()

        # 6. Give thread a moment to exit then destroy
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

        try:
            self.root.destroy()
        except Exception:
            pass


# ══════════════════════════════════════════════════
#   SPLASH SCREEN
# ══════════════════════════════════════════════════
class Splash:
    def __init__(self, root):
        self.root = root
        self.win  = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg=BG_ROOT)
        self.win.attributes("-topmost", True)

        SW = root.winfo_screenwidth()
        SH = root.winfo_screenheight()
        W, H = 520, 290
        self.win.geometry(f"{W}x{H}+{(SW-W)//2}+{(SH-H)//2}")

        self.cv   = tk.Canvas(self.win, width=W, height=H,
                              bg=BG_ROOT, highlightthickness=0)
        self.cv.pack(fill="both", expand=True)

        self.W    = W
        self.H    = H
        self.prog = 0.0
        self._pts = [Particle(W, H) for _ in range(30)]
        self._draw()

    def _draw(self):
        W, H = self.W, self.H
        self.cv.delete("all")
        cx = W // 2

        for p in self._pts:
            p.step()
            r = max(1, int(p.r))
            self.cv.create_oval(p.x-r, p.y-r, p.x+r, p.y+r,
                                fill=p.c, outline="")

        for i in range(5, 0, -1):
            bc = dim_color(C_BLUE, 0.04 * i)
            self.cv.create_rectangle(i, i, W-i, H-i, outline=bc)

        self.cv.create_rectangle(0, 0, 6, H, fill=C_BLUE, outline="")

        self.cv.create_text(cx+3, H//2 - 60,
                             text="FACE DETECTION SYSTEM",
                             font=(FN, 22, "bold"), fill=T_WHITE)
        self.cv.create_text(cx+3, H//2 - 30,
                             text="OpenCV  +  Tkinter  |  v6.0",
                             font=(FN, 10), fill=T_DIM)

        bx = 60
        bw = W - 120
        by = H//2 + 20
        self.cv.create_rectangle(bx, by, bx+bw, by+5,
                                  fill=BG_CARD, outline="")
        fw = int(bw * self.prog / 100)
        if fw > 2:
            self.cv.create_rectangle(bx, by, bx+fw, by+5,
                                      fill=C_BLUE, outline="")
            self.cv.create_rectangle(bx+fw-3, by-2,
                                      bx+fw+3, by+7,
                                      fill=C_CYAN, outline="")

        steps = ["Loading OpenCV...", "Loading Cascades...",
                 "Building UI...", "Almost ready...", "READY!"]
        idx = min(len(steps)-1, int(self.prog / 25))
        self.cv.create_text(cx, by+20, text=steps[idx],
                             font=(FN, 8), fill=C_CYAN)

        self.prog += 1.8
        if self.prog <= 100:
            self.win.after(25, self._draw)
        else:
            self.win.after(300, self.win.destroy)


# ══════════════════════════════════════════════════
#   ENTRY POINT
# ══════════════════════════════════════════════════
def main():
    root = tk.Tk()
    root.withdraw()

    splash = Splash(root)
    root.wait_window(splash.win)
    root.deiconify()

    app = FaceDetectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)

    SW = root.winfo_screenwidth()
    SH = root.winfo_screenheight()
    W, H = 1300, 800
    root.geometry(f"{W}x{H}+{(SW-W)//2}+{(SH-H)//2}")

    app.log("FACE DETECTION SYSTEM v6.0 ready.", "good")
    app.log("Press  ▶ START CAMERA  to begin.", "info")
    app.log("Tip: Raise Min Neighbors to reduce false detections.", "info")

    root.mainloop()


if __name__ == "__main__":
    main()