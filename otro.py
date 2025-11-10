import math
import re
import sys
import tkinter as tk
from tkinter import messagebox

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import sympy as sp
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from tkinter import ttk


# =======================
# 🔹 Clase Teclado Matemático
# =======================
class MathKeyboard(tk.Toplevel):
    def __init__(self, master, target_entry):
        super().__init__(master)
        self.title("Teclado Matemático")
        self.geometry("600x250")
        self.resizable(False, False)
        self.target_entry = target_entry
        self.configure(bg="#f5f5f5")

        # Filas de botones organizados
        buttons = [
            ["7", "8", "9", "+", "-", "×", "÷"],
            ["4", "5", "6", "(", ")", "^", "√"],
            ["1", "2", "3", "π", "e", "sin", "cos"],
            ["0", ".", "tan", "log", "ln", "exp", "←"]
        ]

        for i, row in enumerate(buttons):
            for j, char in enumerate(row):
                b = ttk.Button(self, text=char, width=6,
                               command=lambda c=char: self.insert_text(c))
                b.grid(row=i, column=j, padx=4, pady=4, sticky="nsew")

        self.columnconfigure(tuple(range(len(buttons[0]))), weight=1)
        self.rowconfigure(tuple(range(len(buttons))), weight=1)

    def insert_text(self, char):
        entry = self.target_entry
        pos = entry.index(tk.INSERT)

        # Traducción visual → sintaxis Sympy
        translations = {
            "×": "*", "÷": "/", "√": "sqrt(", "^": "**",
            "π": "pi", "e": "E", "ln": "log(", "log": "log10(",
            "sin": "sin(", "cos": "cos(", "tan": "tan(",
            "exp": "exp("
        }

        if char == "←":  # Borrar
            if pos > 0:
                entry.delete(pos - 1, pos)
            return

        insert_text = translations.get(char, char)
        entry.insert(pos, insert_text)

        # Si el texto abre paréntesis automáticamente, mover el cursor dentro
        if insert_text.endswith("("):
            entry.icursor(pos + len(insert_text))


# =======================
# 🔹 Funciones base
# =======================
def parse_equation(eq_text: str):
    if not eq_text or not eq_text.strip():
        raise ValueError("La ecuación está vacía")

    eq_norm = eq_text.replace('^', '**')
    if '=' in eq_norm:
        parts = eq_norm.split('=')
        if len(parts) != 2:
            raise ValueError("Ecuación con formato inválido (múltiples '=').")
        left, right = parts
        expr_text = f"({left})-({right})"
    else:
        expr_text = eq_norm

    x = sp.symbols('x')
    expr = sp.sympify(expr_text, convert_xor=True)
    f_num = sp.lambdify(
        x, expr,
        modules=["numpy", {"sin": np.sin, "cos": np.cos, "tan": np.tan,
                           "exp": np.exp, "log": np.log, "sqrt": np.sqrt}]
    )
    return expr, f_num


def parse_tolerance(tol_text: str) -> float:
    if tol_text is None or tol_text.strip() == '':
        raise ValueError('La tolerancia está vacía')
    txt = tol_text.strip().replace('^', '**').replace(',', '.')
    return float(sp.N(sp.sympify(txt)))


def bisection(f, a, b, tol, max_iter=1000):
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError('f(a) y f(b) deben tener signos opuestos.')
    rows = []
    for it in range(1, max_iter + 1):
        c = (a + b) / 2.0
        fc = f(c)
        error = abs(b - a) / 2.0
        rows.append((it, a, b, c, f(a), f(b), fc, error))
        if abs(fc) < tol or error < tol:
            break
        if f(a) * fc < 0:
            b = c
        else:
            a = c
    return rows, {'root': c, 'error': error, 'iterations': it, 'f_root': fc}


# =======================
# 🔹 Clase Principal
# =======================
class BisectionApp:
    def __init__(self, master):
        self.master = master
        master.title('Método de Bisección')
        master.geometry('1100x700')

        # --------- Layout principal ---------
        self.frm_top = tk.Frame(master)
        self.frm_top.pack(fill=tk.X, padx=12, pady=8)
        self.frm_center = tk.Frame(master)
        self.frm_center.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        self.frm_left = tk.Frame(self.frm_center)
        self.frm_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.frm_right = tk.Frame(self.frm_center)
        self.frm_right.pack(side=tk.RIGHT, fill=tk.BOTH)

        # --------- Entradas ---------
        tk.Label(self.frm_top, text='Ecuación f(x) = 0:').grid(row=0, column=0, sticky='w')
        self.var_eq = tk.StringVar()
        self.entry_eq = tk.Entry(self.frm_top, textvariable=self.var_eq, width=60)
        self.entry_eq.grid(row=0, column=1, columnspan=4, sticky='we', padx=6)

        tk.Label(self.frm_top, text='a:').grid(row=1, column=0, sticky='w', pady=6)
        self.var_a = tk.StringVar()
        self.entry_a = tk.Entry(self.frm_top, textvariable=self.var_a, width=12)
        self.entry_a.grid(row=1, column=1, sticky='w')

        tk.Label(self.frm_top, text='b:').grid(row=1, column=2, sticky='w')
        self.var_b = tk.StringVar()
        self.entry_b = tk.Entry(self.frm_top, textvariable=self.var_b, width=12)
        self.entry_b.grid(row=1, column=3, sticky='w')

        tk.Label(self.frm_top, text='Tolerancia:').grid(row=1, column=4, sticky='w')
        self.var_tol = tk.StringVar(value='1e-6')
        self.entry_tol = tk.Entry(self.frm_top, textvariable=self.var_tol, width=12)
        self.entry_tol.grid(row=1, column=5, sticky='w')

        # --------- Botones principales ---------
        tk.Button(self.frm_top, text='Graficar', command=self.on_plot,
                  bg='#2196F3', fg='white').grid(row=0, column=6, rowspan=2, padx=4, pady=2, sticky='ns')
        tk.Button(self.frm_top, text='Calcular', command=self.on_calculate,
                  bg='#4CAF50', fg='white').grid(row=0, column=7, rowspan=2, padx=4, pady=2, sticky='ns')
        tk.Button(self.frm_top, text='Reiniciar', command=self.on_reset,
                  bg='#F44336', fg='white').grid(row=0, column=8, rowspan=2, padx=2, pady=2, sticky='ns')
        tk.Button(self.frm_top, text='Buscar intervalos', command=self.on_scan_intervals,
                  bg='#FFC107', fg='black').grid(row=0, column=9, rowspan=2, padx=4, pady=2, sticky='ns')

        # 🔹 Botón para abrir el teclado matemático
        tk.Button(self.frm_top, text='🧮 Teclado', bg='#9C27B0', fg='white',
                  command=self.open_math_keyboard).grid(row=0, column=10, rowspan=2, padx=4, pady=2, sticky='ns')

        # --------- Tabla de iteraciones ---------
        self.frm_table = tk.LabelFrame(self.frm_left, text='Iteraciones')
        self.frm_table.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        cols = ('Iter', 'a', 'b', 'c', 'f(a)', 'f(b)', 'f(c)', 'Error')
        self.tree = ttk.Treeview(self.frm_table, columns=cols, show='headings', height=15)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor='center', width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = tk.Scrollbar(self.frm_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --------- Resultados ---------
        self.frm_results = tk.LabelFrame(self.frm_left, text='Resultados')
        self.frm_results.pack(fill=tk.X, padx=6, pady=6)
        self.lbl_root = tk.Label(self.frm_results, text='Raíz aproximada: -'); self.lbl_root.pack(anchor='w')
        self.lbl_error = tk.Label(self.frm_results, text='Error final: -'); self.lbl_error.pack(anchor='w')
        self.lbl_tol_used = tk.Label(self.frm_results, text='Tolerancia usada: -'); self.lbl_tol_used.pack(anchor='w')
        self.lbl_iters = tk.Label(self.frm_results, text='Iteraciones: -'); self.lbl_iters.pack(anchor='w')

        # --------- Gráfica ---------
        self.frm_plot = tk.LabelFrame(self.frm_right, text='Gráfica')
        self.frm_plot.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('x'); self.ax.set_ylabel('f(x)')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plot)
        self.canvas.draw(); self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # --------------------------
    # 🔹 Métodos de interfaz
    # --------------------------
    def open_math_keyboard(self):
        MathKeyboard(self.master, self.entry_eq)

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def on_reset(self):
        self.var_eq.set(''); self.var_a.set(''); self.var_b.set('')
        self.var_tol.set('1e-6')
        self.clear_table()
        self.lbl_root.config(text='Raíz aproximada: -')
        self.lbl_error.config(text='Error final: -')
        self.lbl_tol_used.config(text='Tolerancia usada: -')
        self.lbl_iters.config(text='Iteraciones: -')
        self.ax.clear(); self.ax.set_xlabel('x'); self.ax.set_ylabel('f(x)')
        self.canvas.draw()

    def update_table(self, rows):
        self.clear_table()
        for r in rows:
            it, a, b, c, fa, fb, fc, err = r
            self.tree.insert('', 'end', values=(it, f"{a:.6g}", f"{b:.6g}",
                                                f"{c:.6g}", f"{fa:.6g}", f"{fb:.6g}",
                                                f"{fc:.6g}", f"{err:.6g}"))

    def update_results(self, final, tol):
        self.lbl_root.config(text=f"Raíz aproximada: {final['root']:.12g}")
        self.lbl_error.config(text=f"Error final: {final['error']:.12g}")
        self.lbl_tol_used.config(text=f"Tolerancia usada: {tol:.12g}")
        self.lbl_iters.config(text=f"Iteraciones: {final['iterations']}")

    def plot_function(self, f, a, b):
        self.ax.clear(); self.ax.set_xlabel('x'); self.ax.set_ylabel('f(x)')
        xs = np.linspace(a, b, 400)
        ys = [f(x) if not np.isnan(f(x)) else np.nan for x in xs]
        self.ax.plot(xs, ys, label='f(x)')
        self.ax.axhline(0, color='black', linewidth=0.7)
        self.ax.legend(); self.canvas.draw()

    def find_sign_change_intervals(self, f, xmin=-100, xmax=100, step=1.0):
        points = np.arange(xmin, xmax + step, step)
        sign_changes = []
        prev_x, prev_y = points[0], f(points[0])
        for x in points[1:]:
            y = f(x)
            if not (np.isnan(prev_y) or np.isnan(y)):
                if prev_y * y < 0:
                    sign_changes.append((prev_x, x))
            prev_x, prev_y = x, y
        return sign_changes

    def on_scan_intervals(self):
        eq_text = self.var_eq.get().strip()
        if not eq_text:
            messagebox.showerror('Error', 'Por favor, ingrese una ecuación antes de buscar intervalos.')
            return
        expr, f = parse_equation(eq_text)
        sign_changes = self.find_sign_change_intervals(f, -100, 100, 1.0)
        if not sign_changes:
            messagebox.showinfo('Sin resultados', 'No se encontraron intervalos con cambio de signo.')
            return
        text = "Posibles intervalos donde f(x) cambia de signo:\n\n" + "\n".join(
            [f"[{a:.2f}, {b:.2f}]" for a, b in sign_changes])
        messagebox.showinfo('Intervalos detectados', text)
        self.plot_function(f, -100, 100)
        for (a, b) in sign_changes:
            self.ax.axvspan(a, b, color='orange', alpha=0.3)
        self.canvas.draw()

    def on_calculate(self):
        try:
            expr, f = parse_equation(self.var_eq.get())
            a, b = float(self.var_a.get()), float(self.var_b.get())
            tol = parse_tolerance(self.var_tol.get())
        except Exception as e:
            messagebox.showerror('Error', str(e))
            return
        rows, final = bisection(f, a, b, tol)
        self.update_table(rows); self.update_results(final, tol)
        self.plot_function(f, a, b)

    def on_plot(self):
        try:
            expr, f = parse_equation(self.var_eq.get())
            self.plot_function(f, -10, 10)
        except Exception as e:
            messagebox.showerror('Error', str(e))


# =======================
# 🔹 Programa principal
# =======================
def main():
    style = Style(theme='flatly')
    root = style.master
    app = BisectionApp(root)
    # Mensaje en consola para confirmar que la aplicación inició.
    print("Iniciando interfaz gráfica (Tk). Si no ve la ventana, revise que no esté minimizada o detrás de otras ventanas.")
    root.mainloop()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Mostrar traceback claro en la consola para diagnóstico
        import traceback
        traceback.print_exc()
        print("Error al iniciar la aplicación:", e)
        sys.exit(1)
