import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttkb
import pandas as pd
import sympy as sp

# -----------------------
# Método de Bisección
# -----------------------
def biseccion(expr_str, a, b, tol, max_iter=100):
    """
    Método de bisección (versión con comentarios simples).

    Parámetros:
    - expr_str: cadena con la función (p. ej. "cos(x) = x" o "x^3-2*x-5")
    - a, b: extremos del intervalo donde buscar la raíz
    - tol: tolerancia para el criterio de parada
    - max_iter: número máximo de iteraciones

    Devuelve:
    - tabla: DataFrame con las iteraciones
    - raiz: aproximación final de la raíz
    - error_final: |f(c)| en la última evaluación

    Explicación simple del algoritmo (para explicar en clase):
    1) Convertimos la cadena a una expresión simbólica con sympy.
    2) Evaluamos f(a) y f(b) y comprobamos que tengan signos opuestos.
    3) Repetimos: calculamos el punto medio c=(a+b)/2, evaluamos f(c).
       - Si f(c) es cercano a 0 (o el intervalo es muy pequeño), paramos.
       - Si f(a) y f(c) tienen signos opuestos, la raíz está en [a,c],
         si no, está en [c,b].
    4) Guardamos cada iteración en una tabla para mostrarla.
    """

    x = sp.Symbol('x')

    # Si el usuario escribió una ecuación con '=' la convertimos a f(x)=0
    if '=' in expr_str:
        lado_izq, lado_der = expr_str.split('=')
        expr_str = f"({lado_izq}) - ({lado_der})"

    # Permitir usar '^' para potencias (lo convertimos a '**' para sympy)
    f = sp.sympify(expr_str.replace('^', '**'))

    # Evaluaciones iniciales en los extremos (como floats para comparaciones)
    fa = float(f.subs(x, a))
    fb = float(f.subs(x, b))

    # Necesitamos que f(a) y f(b) tengan signos distintos para aplicar el método
    if fa * fb > 0:
        raise ValueError("f(a) y f(b) deben tener signos opuestos.")

    data = []  # lista para almacenar las filas que luego convertimos a DataFrame

    for i in range(max_iter):
        # Punto medio del intervalo
        c = (a + b) / 2

        # Evaluar f en c y convertir a float para poder usarlo en cálculos/condiciones
        fc = float(f.subs(x, c))

        # Producto para saber si f(a) y f(c) tienen signos opuestos
        producto = fa * fc

        # Guardamos la iteración (índice, intervalo, punto medio y valores de f)
        data.append([i, a, b, c, fa, fb, fc, producto])

        # Criterio de parada simple:
        # - si f(c) está cerca de 0 (|f(c)| < tol)
        # - o si el intervalo se hace menor que la tolerancia
        if abs(fc) < tol or abs(b - a) / 2 < tol:
            break

        # Actualizar el intervalo según el signo
        if producto < 0:
            # La raíz está entre a y c
            b = c
            fb = fc
        else:
            # La raíz está entre c y b
            a = c
            fa = fc

    raiz = (a + b) / 2
    tabla = pd.DataFrame(data, columns=['Iteración', 'a', 'b', 'c', 'f(a)', 'f(b)', 'f(c)', 'f(a)*f(c)'])
    return tabla, raiz, abs(fc)

# -----------------------
# Función de cálculo
# -----------------------
def calcular():
    try:
        expr = entrada_ecuacion.get()
        a = float(entrada_a.get())
        b = float(entrada_b.get())

        # --- Leer tolerancia flexible ---
        tol_str = entrada_tol.get().strip().lower()
        tol_str = tol_str.replace('×', 'x')  # por si usan símbolo de multiplicar

        if 'e' in tol_str:
            tol = float(tol_str)
        elif '10^' in tol_str:
            base, exp = tol_str.split('10^')
            tol = float(base or 1) * 10 ** float(exp)
        elif '10-' in tol_str:
            base, exp = tol_str.split('10-')
            tol = float(base or 1) * 10 ** (-float(exp))
        elif 'x10^' in tol_str:
            base, exp = tol_str.split('x10^')
            tol = float(base or 1) * 10 ** float(exp)
        else:
            tol = float(tol_str)

        # --- Ejecutar método ---
        tabla, raiz, error = biseccion(expr, a, b, tol)

        # Limpiar tabla previa
        for row in tabla_iteraciones.get_children():
            tabla_iteraciones.delete(row)

        # Insertar resultados
        for _, row in tabla.iterrows():
            valores = [
                int(row['Iteración']),
                f"{row['a']:.6f}",
                f"{row['b']:.6f}",
                f"{row['c']:.6f}",
                f"{row['f(a)']:.6f}",
                f"{row['f(b)']:.6f}",
                f"{row['f(c)']:.6f}",
                f"{row['f(a)*f(c)']:.6f}"
            ]
            tabla_iteraciones.insert("", "end", values=valores)

        etiqueta_resultado.config(
            text=f"Raíz aproximada: x = {raiz:.6f}   |   Error final = {error:.6f}   |   Tolerancia = {tol:.6f}"
        )

    except Exception as e:
        messagebox.showerror("Error", str(e))

# -----------------------
# Insertar texto del teclado
# -----------------------
def insertar_texto(simbolo):
    entrada_ecuacion.insert(tk.END, simbolo)

# -----------------------
# Crear interfaz gráfica
# -----------------------
ventana = ttkb.Window(themename="cosmo")
ventana.title("Método de Bisección")
ventana.geometry("980x740")

# --- Título ---
ttkb.Label(ventana, text="Método de Bisección", font=("Segoe UI", 18, "bold")).pack(pady=10)

# --- Frame de entrada ---
frame_inputs = ttkb.Frame(ventana)
frame_inputs.pack(pady=5)

ttkb.Label(frame_inputs, text="Ecuación f(x):").grid(row=0, column=0, padx=5)
entrada_ecuacion = ttkb.Entry(frame_inputs, width=45, font=("Consolas", 11))
entrada_ecuacion.grid(row=0, column=1, columnspan=4, padx=5)
entrada_ecuacion.insert(0, "cos(x) = x")

ttkb.Label(frame_inputs, text="a:").grid(row=1, column=0, padx=5)
entrada_a = ttkb.Entry(frame_inputs, width=10)
entrada_a.grid(row=1, column=1, padx=5)
entrada_a.insert(0, "0")

ttkb.Label(frame_inputs, text="b:").grid(row=1, column=2, padx=5)
entrada_b = ttkb.Entry(frame_inputs, width=10)
entrada_b.grid(row=1, column=3, padx=5)
entrada_b.insert(0, "1")

ttkb.Label(frame_inputs, text="Tolerancia:").grid(row=2, column=0, padx=5)
entrada_tol = ttkb.Entry(frame_inputs, width=10)
entrada_tol.grid(row=2, column=1, padx=5)
entrada_tol.insert(0, "1e-4")

ttkb.Button(frame_inputs, text="Calcular", command=calcular, bootstyle="success").grid(row=3, column=0, columnspan=5, pady=10)

# --- Teclado matemático ---
frame_teclado = ttkb.Labelframe(ventana, text="Teclado Matemático")
frame_teclado.pack(pady=10)

botones = [
    ['x', 'π', 'e', '^', '√()', '(', ')', '='],
    ['sin(', 'cos(', 'tan(', 'log(', 'ln(', 'exp(', '| |', '÷'],
    ['+', '-', '*', '/', '.', '0', '1', '2'],
    ['3', '4', '5', '6', '7', '8', '9', 'DEL']
]

for i, fila in enumerate(botones):
    for j, texto in enumerate(fila):
        def cmd(t=texto):
            if t == 'DEL':
                entrada_ecuacion.delete(len(entrada_ecuacion.get())-1, tk.END)
            elif t == '√()':
                insertar_texto('sqrt(')
            elif t == '| |':
                insertar_texto('abs(')
            elif t == '÷':
                insertar_texto('/')
            elif t == 'π':
                insertar_texto('pi')
            else:
                insertar_texto(t)
        ttkb.Button(frame_teclado, text=texto, width=6, command=cmd, bootstyle="secondary").grid(row=i, column=j, padx=2, pady=2)

# --- Tabla de resultados ---
cols = ['Iteración', 'a', 'b', 'c', 'f(a)', 'f(b)', 'f(c)', 'f(a)*f(c)']
tabla_iteraciones = ttkb.Treeview(ventana, columns=cols, show='headings', height=10)
for col in cols:
    tabla_iteraciones.heading(col, text=col)
    tabla_iteraciones.column(col, width=110, anchor="center")
tabla_iteraciones.pack(pady=10, fill="x", padx=20)

# --- Resultado final ---
etiqueta_resultado = ttkb.Label(ventana, text="", font=("Segoe UI", 12, "bold"))
etiqueta_resultado.pack(pady=10)

ventana.mainloop()
