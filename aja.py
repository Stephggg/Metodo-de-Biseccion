# -*- coding: utf-8 -*-
"""
Bisection Solver con entrada de ecuaciones renderizada estilo GeoGebra
y teclado matemático virtual.
"""
import sys
import math
import numpy as np
import sympy as sp
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QTableWidget,
                               QTableWidgetItem, QSplitter, QMessageBox, QFrame)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ---------------------- BISECTION LOGIC ----------------------
def bisection_method(f, a, b, tol=1e-6, max_iter=1000):
    fa = f(a)
    fb = f(b)
    if fa * fb > 0:
        raise ValueError("f(a) y f(b) deben tener signos opuestos.")
    rows = []
    for i in range(1, max_iter + 1):
        c = (a + b) / 2
        fc = f(c)
        error = abs(b - a) / 2
        rows.append((i, a, b, c, fa, fb, fc, error))
        if abs(fc) < tol or error < tol:
            break
        if fa * fc < 0:
            b = c
            fb = fc
        else:
            a = c
            fa = fc
    return rows, c, error

# ---------------------- MAIN APPLICATION ----------------------
class BisectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bisection Solver Renderizado")
        self.setGeometry(100, 100, 1200, 700)

        # Layout principal
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # ---------------------- IZQUIERDA ----------------------
        left_frame = QVBoxLayout()
        # WebEngine para ecuación renderizada
        self.equation_input = QWebEngineView()
        self.equation_input.setHtml(self.html_template())
        left_frame.addWidget(QLabel("Ecuación (Renderizada):"))
        left_frame.addWidget(self.equation_input, 1)

        # Teclado virtual
        keyboard_layout = QHBoxLayout()
        for key in ["sin()", "cos()", "tan()", "log()", "exp()", "^", "√", "(", ")"]:
            btn = QPushButton(key)
            btn.clicked.connect(lambda checked, k=key: self.insert_key(k))
            keyboard_layout.addWidget(btn)
        left_frame.addLayout(keyboard_layout)

        # Intervalos y tolerancia
        interval_layout = QHBoxLayout()
        self.lbl_a = QLabel("a:")
        self.val_a = QLabel("-10")
        self.lbl_b = QLabel("b:")
        self.val_b = QLabel("10")
        self.lbl_tol = QLabel("Tol:")
        self.val_tol = QLabel("1e-6")
        interval_layout.addWidget(self.lbl_a)
        interval_layout.addWidget(self.val_a)
        interval_layout.addWidget(self.lbl_b)
        interval_layout.addWidget(self.val_b)
        interval_layout.addWidget(self.lbl_tol)
        interval_layout.addWidget(self.val_tol)
        left_frame.addLayout(interval_layout)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_scan = QPushButton("Graficar")
        self.btn_scan.clicked.connect(self.plot_function)
        self.btn_calc = QPushButton("Calcular Bisección")
        self.btn_calc.clicked.connect(self.calculate_bisection)
        btn_layout.addWidget(self.btn_scan)
        btn_layout.addWidget(self.btn_calc)
        left_frame.addLayout(btn_layout)

        # ---------------------- DERECHA ----------------------
        right_splitter = QSplitter(Qt.Vertical)

        # Gráfica
        self.fig = Figure(figsize=(5,4))
        self.canvas = FigureCanvas(self.fig)
        right_splitter.addWidget(self.canvas)

        # Tabla de iteraciones
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Iter","a","b","c","f(a)","f(b)","f(c)","Error"])
        right_splitter.addWidget(self.table)

        main_layout.addLayout(left_frame, 3)
        main_layout.addWidget(right_splitter, 4)

    # ---------------------- METHODS ----------------------
    def html_template(self):
        # MathLive editable equation
        return """
        <!DOCTYPE html>
        <html>
        <head>
          <script src="https://unpkg.com/mathlive/dist/mathlive.min.js"></script>
        </head>
        <body>
          <math-field id="mf" virtual-keyboard-mode="manual" style="width:100%; height:60px;"></math-field>
        </body>
        </html>
        """

    def insert_key(self, key):
        # Inserta key en MathLive
        js = f"""
        var mf = document.getElementById('mf');
        mf.executeCommand('{key}');
        """
        self.equation_input.page().runJavaScript(js)

    def get_equation(self, callback):
        # Obtiene ecuación de MathLive en formato latex
        js = "document.getElementById('mf').getValue();"
        self.equation_input.page().runJavaScript(js, callback)

    def parse_function(self, latex_str):
        # Convierte latex a función numérica
        x = sp.symbols('x')
        try:
            expr = sp.sympify(latex_str.replace('^','**'))
            f = sp.lambdify(x, expr, modules=["numpy", {"sin": np.sin,"cos":np.cos,"tan":np.tan,"log":np.log,"exp":np.exp,"sqrt":np.sqrt}])
            return f
        except Exception as e:
            QMessageBox.critical(self,"Error","No se pudo interpretar la ecuación:\n"+str(e))
            return None

    def plot_function(self):
        def callback(latex_str):
            f = self.parse_function(latex_str)
            if f is None:
                return
            a = float(self.val_a.text())
            b = float(self.val_b.text())
            xs = np.linspace(a,b,400)
            ys = []
            for xi in xs:
                try:
                    yi = f(xi)
                except:
                    yi = np.nan
                ys.append(yi)
            self.fig.clear()
            ax = self.fig.add_subplot(111)
            ax.plot(xs, ys, label="f(x)")
            ax.axhline(0, color="black")
            ax.legend()
            self.canvas.draw()
        self.get_equation(callback)

    def calculate_bisection(self):
        def callback(latex_str):
            f = self.parse_function(latex_str)
            if f is None:
                return
            a = float(self.val_a.text())
            b = float(self.val_b.text())
            tol = float(self.val_tol.text())
            try:
                rows, root, error = bisection_method(f, a, b, tol)
            except Exception as e:
                QMessageBox.critical(self,"Error","Bisección falló:\n"+str(e))
                return
            # Llenar tabla
            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    self.table.setItem(i,j,QTableWidgetItem(f"{val:.6g}"))
            QMessageBox.information(self,"Resultado",
                                    f"Raíz aproximada: {root:.12g}\nError final: {error:.12g}\nTolerancia usada: {tol}")

        self.get_equation(callback)

# ---------------------- RUN ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BisectionApp()
    window.show()
    sys.exit(app.exec())
