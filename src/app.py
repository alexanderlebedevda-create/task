import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import csv
from datetime import datetime, date, timedelta
import uuid

DATA_DIR = r"C:\TodoApp"
DATA_FILE = os.path.join(DATA_DIR, "tasks.json")

BG      = "#141414"
BG2     = "#1C1C1E"
BG3     = "#222224"
PANEL   = "#1A1A1C"
BORDER  = "#2A2A2C"
TEXT    = "#E8E8E8"
TEXT2   = "#888888"
TEXT3   = "#555555"
ACCENT  = "#E8A020"
RED     = "#E05252"
GREEN   = "#4EC97B"
BLUE    = "#4A9EE8"

P_COLORS = {"high": RED, "mid": ACCENT, "low": GREEN}
P_LABELS = {"high": "ВЫСОКИЙ", "mid": "СРЕДНИЙ", "low": "НИЗКИЙ"}
P_BG     = {"high": "#3A1A1A", "mid": "#3A2E10", "low": "#1A3A25"}

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_tasks():
    ensure_data_dir()
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return [
        {"id": str(uuid.uuid4()), "task": "Снять интро сцену", "date": today, "priority": "high", "comment": "Камера A — широкий план", "done": False},
        {"id": str(uuid.uuid4()), "task": "Цветокоррекция — день 1", "date": today, "priority": "high", "comment": "S-curve + shadows", "done": True},
        {"id": str(uuid.uuid4()), "task": "Смонтировать экшн сцену", "date": tomorrow, "priority": "mid", "comment": "J-cut на переходах", "done": False},
        {"id": str(uuid.uuid4()), "task": "Записать закадровый голос", "date": tomorrow, "priority": "mid", "comment": "Студия в 15:00", "done": False},
        {"id": str(uuid.uuid4()), "task": "Экспорт H.264 4K", "date": today, "priority": "low", "comment": "Для YouTube", "done": True},
    ]

def save_tasks(tasks):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

class TodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DaVinci Task Manager")
        self.geometry("1100x680")
        self.minsize(800, 500)
        self.configure(bg=BG)
        self.tasks = load_tasks()
        self.filter_mode = "all"
        self._clock_job = None
        self._saved_job = None
        self._build_ui()
        self._render_table()
        self._tick_clock()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        save_tasks(self.tasks)
        self.destroy()

    def _build_ui(self):
        self._build_topbar()
        self._build_body()

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG2, height=56)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=BG2)
        left.pack(side="left", padx=20)
        tk.Label(left, text="●", fg=RED, bg=BG2, font=("Courier", 10)).pack(side="left", padx=(0,6))
        tk.Label(left, text="DAVINCI TASK MANAGER", fg=ACCENT, bg=BG2,
                 font=("Courier", 11, "bold")).pack(side="left")

        center = tk.Frame(bar, bg=BG2)
        center.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_date = tk.Label(center, text="", fg=TEXT, bg=BG2, font=("Courier", 13, "bold"))
        self.lbl_date.pack()
        self.lbl_clock = tk.Label(center, text="", fg=TEXT2, bg=BG2, font=("Courier", 10))
        self.lbl_clock.pack()

        right = tk.Frame(bar, bg=BG2)
        right.pack(side="right", padx=16)
        self.lbl_saved = tk.Label(right, text="● Сохранено", fg=GREEN, bg=BG2, font=("Courier", 9))
        self.lbl_saved.pack(side="left", padx=(0,10))
        self.lbl_saved.pack_forget()

        tk.Button(right, text="↓ Экспорт CSV", bg=ACCENT, fg="#111", font=("Arial", 9, "bold"),
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._export_csv).pack(side="left")

    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_main(body)

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=PANEL, width=200)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x")

        self._sidebar_items = {}

        def section(label):
            tk.Label(sb, text=label, fg=TEXT3, bg=PANEL,
                     font=("Courier", 8), anchor="w").pack(fill="x", padx=16, pady=(14,4))

        def item(key, color, text):
            f = tk.Frame(sb, bg=PANEL, cursor="hand2")
            f.pack(fill="x")
            dot = tk.Canvas(f, width=12, height=12, bg=PANEL, highlightthickness=0)
            dot.pack(side="left", padx=(16,8), pady=8)
            dot.create_oval(1,1,11,11, fill=color, outline="")
            lbl = tk.Label(f, text=text, fg=TEXT2, bg=PANEL, font=("Arial", 10, "bold"), anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            cnt = tk.Label(f, text="0", fg=TEXT3, bg=BG3, font=("Courier", 9), padx=5, pady=1)
            cnt.pack(side="right", padx=12)
            self._sidebar_items[key] = {"frame": f, "label": lbl, "count": cnt, "dot_canvas": dot}
            for w in (f, dot, lbl, cnt):
                w.bind("<Button-1>", lambda e, k=key: self._filter(k))
            f.bind("<Enter>", lambda e, fr=f: fr.configure(bg="#222"))
            f.bind("<Leave>", lambda e, fr=f, k=key: fr.configure(bg=ACCENT+"11" if self.filter_mode==k else PANEL))

        section("PROJECT")
        item("all",     ACCENT, "Все задачи")
        item("done",    GREEN,  "Выполнено")
        item("pending", BLUE,   "В работе")
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=16, pady=8)
        section("PRIORITY")
        item("high", RED,    "Высокий")
        item("mid",  ACCENT, "Средний")
        item("low",  GREEN,  "Низкий")

        self._update_sidebar_active()

    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        toolbar = tk.Frame(main, bg=BG2, height=46)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)
        tk.Frame(toolbar, bg=BORDER, height=1).pack(side="bottom", fill="x")

        tk.Button(toolbar, text="+ Новое дело", bg=BG3, fg=ACCENT,
                  font=("Arial", 9, "bold"), relief="flat", padx=12, pady=5,
                  cursor="hand2", command=self._add_task,
                  highlightbackground=ACCENT, bd=1).pack(side="left", padx=12, pady=8)

        tk.Frame(toolbar, bg=BORDER, width=1, height=24).pack(side="left", pady=10)

        self.lbl_total   = self._stat_chip(toolbar, "Всего")
        self.lbl_done_tb = self._stat_chip(toolbar, "Готово")
        self.lbl_left    = self._stat_chip(toolbar, "Осталось")

        cols_frame = tk.Frame(main, bg=BG3, height=32)
        cols_frame.pack(fill="x")
        cols_frame.pack_propagate(False)
        tk.Frame(cols_frame, bg=BORDER, height=1).pack(side="bottom", fill="x")
        for col, w in [("#", 40), ("✓", 36), ("ДЕЛО", 280), ("ДАТА", 100), ("ПРИОРИТЕТ", 90), ("КОММЕНТАРИЙ", 200), ("", 30)]:
            tk.Label(cols_frame, text=col, fg=TEXT3, bg=BG3,
                     font=("Courier", 8), width=w//7, anchor="w").pack(side="left", padx=4)

        scroll_frame = tk.Frame(main, bg=BG)
        scroll_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(scroll_frame, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.rows_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window((0,0), window=self.rows_frame, anchor="nw")

        self.rows_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

    def _stat_chip(self, parent, label):
        f = tk.Frame(parent, bg=BG3, padx=8, pady=3)
        f.pack(side="left", padx=6, pady=8)
        tk.Label(f, text=label+":", fg=TEXT2, bg=BG3, font=("Courier", 9)).pack(side="left")
        lbl = tk.Label(f, text="0", fg=TEXT, bg=BG3, font=("Courier", 9, "bold"))
        lbl.pack(side="left", padx=(3,0))
        return lbl

    def _get_filtered(self):
        if self.filter_mode == "all":     return self.tasks
        if self.filter_mode == "done":    return [t for t in self.tasks if t["done"]]
        if self.filter_mode == "pending": return [t for t in self.tasks if not t["done"]]
        return [t for t in self.tasks if t["priority"] == self.filter_mode]

    def _render_table(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()

        visible = self._get_filtered()

        if not visible:
            tk.Label(self.rows_frame, text="Нет задач в этой категории",
                     fg=TEXT3, bg=BG, font=("Arial", 11), pady=40).pack()
        else:
            for vi, task in enumerate(visible):
                self._render_row(vi, task)

        self._update_stats()
        self._update_sidebar_active()

    def _render_row(self, vi, task):
        real_i = self.tasks.index(task)
        row_bg = "#0F0F0F" if task["done"] else BG
        fg = TEXT3 if task["done"] else TEXT

        f = tk.Frame(self.rows_frame, bg=row_bg)
        f.pack(fill="x")
        tk.Frame(self.rows_frame, bg=BORDER, height=1).pack(fill="x")

        def on_enter(e, fr=f): fr.configure(bg="#1A1A1A")
        def on_leave(e, fr=f, bg=row_bg): fr.configure(bg=bg)
        f.bind("<Enter>", on_enter)
        f.bind("<Leave>", on_leave)

        tk.Label(f, text=str(vi+1).zfill(2), fg=TEXT3, bg=row_bg,
                 font=("Courier", 9), width=3).pack(side="left", padx=(8,4))

        var = tk.BooleanVar(value=task["done"])
        def on_check(v=var, t=task):
            t["done"] = v.get()
            save_tasks(self.tasks)
            self._show_saved()
            self._render_table()
        cb = tk.Checkbutton(f, variable=var, command=on_check, bg=row_bg,
                            activebackground=row_bg, selectcolor=GREEN,
                            fg=GREEN, cursor="hand2")
        cb.pack(side="left", padx=4)

        task_var = tk.StringVar(value=task["task"])
        task_entry = tk.Entry(f, textvariable=task_var, bg=row_bg, fg=fg,
                              insertbackground=TEXT, relief="flat", font=("Arial", 10),
                              width=28, disabledforeground=TEXT3)
        task_entry.pack(side="left", padx=4)
        if task["done"]:
            task_entry.configure(state="disabled")
        def on_task_change(e, v=task_var, t=task):
            t["task"] = v.get(); self._debounce_save()
        task_entry.bind("<KeyRelease>", on_task_change)

        date_var = tk.StringVar(value=task["date"])
        date_entry = tk.Entry(f, textvariable=date_var, bg=row_bg, fg=fg,
                              insertbackground=TEXT, relief="flat", font=("Courier", 10), width=11)
        date_entry.pack(side="left", padx=4)
        def on_date_change(e, v=date_var, t=task):
            t["date"] = v.get(); self._debounce_save()
        date_entry.bind("<KeyRelease>", on_date_change)

        p_color = P_COLORS.get(task["priority"], ACCENT)
        p_bg    = P_BG.get(task["priority"], BG3)
        p_lbl   = P_LABELS.get(task["priority"], "MID")
        p_btn = tk.Label(f, text=p_lbl, fg=p_color, bg=p_bg,
                         font=("Courier", 8, "bold"), padx=8, pady=3, cursor="hand2")
        p_btn.pack(side="left", padx=6)
        def cycle_priority(e, t=task):
            order = ["high","mid","low"]
            t["priority"] = order[(order.index(t["priority"])+1)%3]
            save_tasks(self.tasks); self._show_saved(); self._render_table()
        p_btn.bind("<Button-1>", cycle_priority)

        comment_var = tk.StringVar(value=task["comment"])
        comment_entry = tk.Entry(f, textvariable=comment_var, bg=row_bg, fg=TEXT2,
                                 insertbackground=TEXT, relief="flat", font=("Arial", 9))
        comment_entry.pack(side="left", padx=4, fill="x", expand=True)
        def on_comment_change(e, v=comment_var, t=task):
            t["comment"] = v.get(); self._debounce_save()
        comment_entry.bind("<KeyRelease>", on_comment_change)

        del_btn = tk.Label(f, text="✕", fg=TEXT3, bg=row_bg,
                           font=("Arial", 10), cursor="hand2", padx=8)
        del_btn.pack(side="right")
        def on_del(e, idx=real_i):
            self.tasks.pop(idx); save_tasks(self.tasks)
            self._show_saved(); self._render_table()
        del_btn.bind("<Button-1>", on_del)
        del_btn.bind("<Enter>", lambda e, l=del_btn: l.configure(fg=RED))
        del_btn.bind("<Leave>", lambda e, l=del_btn: l.configure(fg=TEXT3))

    def _add_task(self):
        self.tasks.append({
            "id": str(uuid.uuid4()),
            "task": "",
            "date": date.today().isoformat(),
            "priority": "mid",
            "comment": "",
            "done": False
        })
        save_tasks(self.tasks)
        self._render_table()
        self.canvas.yview_moveto(1.0)

    def _filter(self, mode):
        self.filter_mode = mode
        self._render_table()

    def _update_sidebar_active(self):
        counts = {
            "all":     len(self.tasks),
            "done":    sum(1 for t in self.tasks if t["done"]),
            "pending": sum(1 for t in self.tasks if not t["done"]),
            "high":    sum(1 for t in self.tasks if t["priority"]=="high"),
            "mid":     sum(1 for t in self.tasks if t["priority"]=="mid"),
            "low":     sum(1 for t in self.tasks if t["priority"]=="low"),
        }
        for key, widgets in self._sidebar_items.items():
            is_active = key == self.filter_mode
            widgets["frame"].configure(bg=ACCENT+"22" if is_active else PANEL)
            widgets["label"].configure(fg=ACCENT if is_active else TEXT2,
                                       bg=ACCENT+"22" if is_active else PANEL)
            widgets["count"].configure(text=str(counts.get(key,0)),
                                       bg=BG3)

    def _update_stats(self):
        total = len(self.tasks)
        done  = sum(1 for t in self.tasks if t["done"])
        self.lbl_total.configure(text=str(total))
        self.lbl_done_tb.configure(text=str(done))
        self.lbl_left.configure(text=str(total-done))

    _save_job = None
    def _debounce_save(self):
        if self._save_job: self.after_cancel(self._save_job)
        self._save_job = self.after(800, self._do_save)

    def _do_save(self):
        save_tasks(self.tasks)
        self._show_saved()

    def _show_saved(self):
        self.lbl_saved.pack(side="left", padx=(0,10))
        if self._saved_job: self.after_cancel(self._saved_job)
        self._saved_job = self.after(2000, self.lbl_saved.pack_forget)

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файл","*.csv")],
            initialfile="tasks.csv",
            initialdir=DATA_DIR)
        if not path: return
        p_ru = {"high":"Высокий","mid":"Средний","low":"Низкий"}
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["#","Выполнено","Дело","Дата","Приоритет","Комментарий"])
            for i,t in enumerate(self.tasks):
                w.writerow([i+1, "Да" if t["done"] else "Нет",
                            t["task"], t["date"],
                            p_ru.get(t["priority"],t["priority"]),
                            t["comment"]])
        messagebox.showinfo("Экспорт", f"Сохранено:\n{path}")

    def _tick_clock(self):
        now = datetime.now()
        self.lbl_date.configure(text=now.strftime("%d.%m.%Y"))
        frames = now.microsecond // 41667
        self.lbl_clock.configure(text=now.strftime(f"%H:%M:%S:{frames:02d}"))
        self._clock_job = self.after(42, self._tick_clock)

if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
