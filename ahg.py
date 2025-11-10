import sys
import numpy as np
import sympy as sp
import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =======================
# 🔹 Clase Teclado Matemático Mejorado
# =======================
class MathKeyboard(tk.Toplevel):
    def __init__(self, master, target_entry):
        super().__init__(master)
        self.title("Teclado Matemático")
        self.geometry("650x250")
        self.resizable(False, False)
        self.target_entry = target_entry
        self.configure(bg="#2c2c2c")

        buttons = [
            ["7", "8", "9", "+", "-", "×", "÷", "(", ")"],
            ["4", "5", "6", "^", "√", "π", "e", "abs", "exp"],
            ["1", "2", "3", "sin", "cos", "tan", "log", "ln", "←"],
            ["0", ".", ",", "floor", "ceil", "**", "%", "!", "AC"]
        ]

        for i, row in enumerate(buttons):
            for j, char in enumerate(row):
                b = ttk.Button(self, text=char, width=6,
                               command=lambda c=char: self.insert_text(c))
                b.grid(row=i, column=j, padx=3, pady=3, sticky="nsew")

        for k in range(len(buttons[0])):
            self.columnconfigure(k, weight=1)
        for k in range(len(buttons)):
            self.rowconfigure(k, weight=1)

    def insert_text(self, char):
        entry = self.target_entry
        pos = entry.index(tk.INSERT)
        translations = {
            "×": "*", "÷": "/", "√": "sp.sqrt(", "^": "**",
            "π": "sp.pi", "e": "sp.E", "ln": "sp.log(", "log": "sp.log10(",
            "sin": "sp.sin(", "cos": "sp.cos(", "tan": "sp.tan(",
            "exp": "sp.exp(", "abs": "sp.Abs(", "floor": "sp.floor(",
            "ceil": "sp.ceiling(", "!": "sp.factorial("
        }

        if char == "←":
            if pos > 0:
                entry.delete(pos - 1, pos)
            return
        if char == "AC":
            entry.delete(0, tk.END)
            return

        insert_text = translations.get(char, char)
        entry.insert(pos, insert_text)
        if insert_text.endswith("("):
            entry.icursor(pos + len(insert_text))

# =======================
# 🔹 Funciones matemáticas
# =======================
def parse_equation(eq_text: str):
    if not eq_text.strip():
        raise ValueError("La ecuación está vacía")
    eq_norm = eq_text.replace('^', '**')
    if '=' in eq_norm:
        parts = eq_norm.split('=')
        if len(parts) != 2:
            raise ValueError("Ecuación con formato inválido")
        left, right = parts
        expr_text = f"({left})-({right})"
    else:
        expr_text = eq_norm

    x = sp.symbols('x')
    expr = sp.sympify(expr_text, convert_xor=True)
    f_num = sp.lambdify(x, expr, modules=["numpy", {"sin": np.sin, "cos": np.cos,
                                                     "tan": np.tan, "exp": np.exp,
                                                     "log": np.log, "sqrt": np.sqrt,
                                                     "Abs": np.abs}])
    return expr, f_num

def parse_tolerance(tol_text: str) -> float:
    if not tol_text.strip():
        raise ValueError("La tolerancia está vacía")
    txt = tol_text.strip().replace('^', '**').replace(',', '.')
    return float(sp.N(sp.sympify(txt)))

# =======================
# 🔹 Métodos Numéricos
# =======================
def bisection(f, a, b, tol, max_iter=1000):
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("f(a) y f(b) deben tener signos opuestos.")
    rows = []
    for it in range(1, max_iter + 1):
        c = (a + b) / 2
        fc = f(c)
        error = abs(b - a) / 2
        rows.append((it, a, b, c, fa, fb, fc, error))
        if abs(fc) < tol or error < tol:
            break
        if fa * fc < 0:
            b = c
            fb = fc
        else:
            a = c
            fa = fc
    return rows, {'root': c, 'error': error, 'iterations': it, 'f_root': fc}

def false_position(f, a, b, tol, max_iter=1000):
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("f(a) y f(b) deben tener signos opuestos.")
    rows = []
    for it in range(1, max_iter + 1):
        c = (a * fb - b * fa) / (fb - fa)
        fc = f(c)
        error = abs(fc)
        rows.append((it, a, b, c, fa, fb, fc, error))
        if abs(fc) < tol or error < tol:
            break
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    return rows, {'root': c, 'error': error, 'iterations': it, 'f_root': fc}

def newton(f, df, x0, tol, max_iter=1000):
    rows = []
    x = x0
    for it in range(1, max_iter + 1):
        fx = f(x)
        dfx = df(x)
        if dfx == 0:
            raise ValueError("Derivada cero, no se puede continuar")
        x_new = x - fx / dfx
        error = abs(x_new - x)
        rows.append((it, x, fx, dfx, x_new, error))
        if error < tol:
            break
        x = x_new
    return rows, {'root': x, 'error': error, 'iterations': it, 'f_root': f(x)}

# =======================
# 🔹 Aplicación Principal
# =======================
class RootFinderApp:
    def __init__(self, master):
        self.master = master
        master.title("Buscador de Raíces Profesional")
        master.geometry("1250x750")

        # Layout
        self.frm_top = tk.Frame(master)
        self.frm_top.pack(fill=tk.X, padx=10, pady=5)
        self.frm_center = tk.Frame(master)
        self.frm_center.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.frm_left = tk.Frame(self.frm_center)
        self.frm_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.frm_right = tk.Frame(self.frm_center)
        self.frm_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Entradas
        tk.Label(self.frm_top, text="Ecuación f(x) = 0:", foreground="white", background="#2c2c2c").grid(row=0, column=0, sticky='w')
        self.var_eq = tk.StringVar()
        self.entry_eq = tk.Entry(self.frm_top, textvariable=self.var_eq, width=60)
        self.entry_eq.grid(row=0, column=1, columnspan=4, sticky='we', padx=5)

        tk.Label(self.frm_top, text="a:", foreground="white", background="#2c2c2c").grid(row=1, column=0, sticky='w')
        self.var_a = tk.StringVar()
        self.entry_a = tk.Entry(self.frm_top, textvariable=self.var_a, width=12)
        self.entry_a.grid(row=1, column=1, sticky='w')

        tk.Label(self.frm_top, text="b / x0:", foreground="white", background="#2c2c2c").grid(row=1, column=2, sticky='w')
        self.var_b = tk.StringVar()
        self.entry_b = tk.Entry(self.frm_top, textvariable=self.var_b, width=12)
        self.entry_b.grid(row=1, column=3, sticky='w')

        tk.Label(self.frm_top, text="Tolerancia:", foreground="white", background="#2c2c2c").grid(row=1, column=4, sticky='w')
        self.var_tol = tk.StringVar(value='1e-6')
        self.entry_tol = tk.Entry(self.frm_top, textvariable=self.var_tol, width=12)
        self.entry_tol.grid(row=1, column=5, sticky='w')

        # Método
        tk.Label(self.frm_top, text="Método:", foreground="white", background="#2c2c2c").grid(row=0, column=5, sticky='e')
        self.method_choice = ttk.Combobox(self.frm_top, values=["Bisección", "Falsa Posición", "Newton-Raphson"], width=18)
        self.method_choice.current(0)
        self.method_choice.grid(row=0, column=6, sticky='w')

        # Botones
        ttk.Button(self.frm_top, text="🧮 Teclado", command=self.open_math_keyboard, style="info.TButton").grid(row=0, column=7, padx=3)
        ttk.Button(self.frm_top, text="Graficar", command=self.on_plot, style="primary.TButton").grid(row=0, column=8, padx=3)
        ttk.Button(self.frm_top, text="Calcular", command=self.on_calculate, style="success.TButton").grid(row=0, column=9, padx=3)
        ttk.Button(self.frm_top, text="Reiniciar", command=self.on_reset, style="danger.TButton").grid(row=1, column=7, padx=3)
        ttk.Button(self.frm_top, text="Exportar CSV", command=self.on_export_csv, style="secondary.TButton").grid(row=1, column=8, padx=3)
        ttk.Button(self.frm_top, text="Intervalos [-100,100]", command=self.on_scan_intervals, style="warning.TButton").grid(row=1, column=9, padx=3)

        # Tabla de iteraciones
        self.frm_table = tk.LabelFrame(self.frm_left, text="Iteraciones")
        self.frm_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree = ttk.Treeview(self.frm_table, columns=[], show='headings', height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.scrollbar = tk.Scrollbar(self.frm_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Resultados
        self.frm_results = tk.LabelFrame(self.frm_left, text="Resultados")
        self.frm_results.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_root = tk.Label(self.frm_results, text="Raíz aproximada: -"); self.lbl_root.pack(anchor='w')
        self.lbl_error = tk.Label(self.frm_results, text="Error final: -"); self.lbl_error.pack(anchor='w')
        self.lbl_iters = tk.Label(self.frm_results, text="Iteraciones: -"); self.lbl_iters.pack(anchor='w')

        # Gráfica
        self.frm_plot = tk.LabelFrame(self.frm_right, text="Gráfica")
        self.frm_plot.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.fig = Figure(figsize=(6,5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('x'); self.ax.set_ylabel('f(x)')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frm_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Guardar últimas iteraciones
        self.last_rows = []

    # --------------------------
    # Métodos GUI
    # --------------------------
    def open_math_keyboard(self):
        MathKeyboard(self.master, self.entry_eq)

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def update_table(self, rows):
        self.clear_table()
        if not rows: return
        # Ajustar columnas según método
        method = self.method_choice.get()
        if method in ["Bisección","Falsa Posición"]:
            cols = ('Iter', 'a', 'b', 'c', 'f(a)', 'f(b)', 'f(c)', 'Error')
        else:
            cols = ('Iter', 'x', 'f(x)', "f'(x)", 'x_new', 'Error')
        self.tree.config(columns=cols)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor='center', width=100)

        for r in rows:
            vals = tuple(f"{v:.6g}" if isinstance(v, (int,float)) else str(v) for v in r)
            self.tree.insert('', 'end', values=vals)
        self.last_rows = rows

    def update_results(self, final):
        self.lbl_root.config(text=f"Raíz aproximada: {final['root']:.12g}")
        self.lbl_error.config(text=f"Error final: {final['error']:.12g}")
        self.lbl_iters.config(text=f"Iteraciones: {final['iterations']}")

    def plot_function(self, f, a=-10, b=10, root=None, intervals=None):
        self.ax.clear()
        xs = np.linspace(a, b, 400)
        ys = np.array([f(x) if not np.isnan(f(x)) else np.nan for x in xs])
        self.ax.plot(xs, ys, label='f(x)')
        self.ax.axhline(0, color='black', linewidth=0.7)
        if intervals:
            for (start, end) in intervals:
                self.ax.axvspan(start, end, color='orange', alpha=0.3)
        if root is not None:
            self.ax.plot(root, f(root), 'ro', label="Raíz")
        self.ax.legend()
        self.canvas.draw()

    def on_reset(self):
        self.var_eq.set(''); self.var_a.set(''); self.var_b.set(''); self.var_tol.set('1e-6')
        self.clear_table()
        self.lbl_root.config(text="Raíz aproximada: -")
        self.lbl_error.config(text="Error final: -")
        self.lbl_iters.config(text="Iteraciones: -")
        self.ax.clear(); self.ax.set_xlabel('x'); self.ax.set_ylabel('f(x)')
        self.canvas.draw()

    def on_plot(self):
        try:
            expr, f = parse_equation(self.var_eq.get())
            self.plot_function(f, -10, 10)
        except Exception as e:
            messagebox.showerror("Error", str(e))

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
            messagebox.showerror('Error', 'Ingrese una ecuación antes de buscar intervalos.')
            return
        expr, f = parse_equation(eq_text)
        sign_changes = self.find_sign_change_intervals(f, -100, 100, 1.0)
        if not sign_changes:
            messagebox.showinfo('Sin resultados', 'No se encontraron intervalos con cambio de signo.')
            return
        text = "Posibles intervalos donde f(x) cambia de signo:\n\n" + "\n".join(
            [f"[{a:.2f}, {b:.2f}]" for a, b in sign_changes])
        messagebox.showinfo('Intervalos detectados', text)
        self.plot_function(f, -100, 100, intervals=sign_changes)

    def on_calculate(self):
        try:
            expr, f = parse_equation(self.var_eq.get())
            tol = parse_tolerance(self.var_tol.get())
            method = self.method_choice.get()
            if method == "Bisección":
                a, b = float(self.var_a.get()), float(self.var_b.get())
                rows, final = bisection(f, a, b, tol)
            elif method == "Falsa Posición":
                a, b = float(self.var_a.get()), float(self.var_b.get())
                rows, final = false_position(f, a, b, tol)
            else:  # Newton-Raphson
                x0 = float(self.var_a.get())
                df = sp.lambdify(sp.symbols('x'), sp.diff(expr, sp.symbols('x')), modules=["numpy"])
                rows, final = newton(f, df, x0, tol)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self.update_table(rows)
        self.update_results(final)
        self.plot_function(f, -10, 10, root=final['root'])

    def on_export_csv(self):
        if not self.last_rows:
            messagebox.showinfo("Info", "No hay datos para exportar")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files","*.csv")])
        if not file_path:
            return
        df = pd.DataFrame(self.last_rows)
        df.to_csv(file_path, index=False)
        messagebox.showinfo("Éxito", f"Tabla exportada a {file_path}")

# =======================
# 🔹 Programa Principal
# =======================
def main():
    style = Style(theme='cyborg')  # Tema azul oscuro moderno
    root = style.master
    app = RootFinderApp(root)
    root.mainloop()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error:", e)
        sys.exit(1)
