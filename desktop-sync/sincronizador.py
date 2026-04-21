import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import requests
import webbrowser
import os
import threading
import time
import platform
import urllib3
import json

SERVIDOR_URL = "http://127.0.0.1:5001"
EXT_VALIDAS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.mov', '.avi', '.mkv', '.webm')
ARCHIVO_SESION = "session.txt"
ARCHIVO_CONFIG = "folders.json"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PyGalleryApp:
    def __init__(self, root, on_close_callback):
        self.root = root
        self.on_close_callback = on_close_callback
        self.root.title("pyGallery Desktop Sync")
        self.root.geometry("600x800")
        self.root.configure(bg="#020617")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_callback)

        self.usuario_id = None
        self.usuario_nombre = None
        self.carpetas = self.cargar_config_carpetas()
        self.archivos_enviados = set()
        self.hilo_activo = False
        self.token = None

        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg="#020617")
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        self.root.bind("<Configure>", self.redibujar_fondo)
        self.verificar_sesion_persistente()

    def obtener_os_bonito(self):
        sys_name = platform.system()
        machine = platform.machine()
        if sys_name == "Darwin":
            display = "macOS"
            if "arm" in machine.lower() or "aarch64" in machine.lower():
                display += " (ARM)"
            return display
        return sys_name

    def cargar_config_carpetas(self):
        if os.path.exists(ARCHIVO_CONFIG):
            try:
                with open(ARCHIVO_CONFIG, "r") as f:
                    return json.load(f)
            except: return []
        return []

    def guardar_config_carpetas(self):
        with open(ARCHIVO_CONFIG, "w") as f:
            json.dump(self.carpetas, f)

    def verificar_sesion_persistente(self):
        if os.path.exists(ARCHIVO_SESION):
            try:
                with open(ARCHIVO_SESION, "r") as f:
                    lineas = f.read().splitlines()
                    if len(lineas) >= 3:
                        self.token, self.usuario_id, self.usuario_nombre = lineas[0], lineas[1], lineas[2]
                
                r = requests.post(f"{SERVIDOR_URL}/api/check_token", json={"token": self.token}, verify=False, timeout=5)
                if r.status_code == 200:
                    self.crear_interfaz_sync(self.usuario_nombre)
                    return
            except: pass
        self.crear_login()

    def redibujar_fondo(self, event=None):
        self.canvas.delete("all")
        w, h = self.root.winfo_width(), self.root.winfo_height()
        r1, g1, b1 = 2, 6, 23
        r2, g2, b2 = 15, 23, 42
        for i in range(0, h, 4):
            nr = int(r1 + (r2 - r1) * i / h)
            ng = int(g1 + (g2 - g1) * i / h)
            nb = int(b1 + (b2 - b1) * i / h)
            color = f"#{nr:02x}{ng:02x}{nb:02x}"
            self.canvas.create_rectangle(0, i, w, i+4, fill=color, outline=color)
        for i in range(0, w, 40): self.canvas.create_line(i, 0, i, h, fill="#1e293b")
        for i in range(0, h, 40): self.canvas.create_line(0, i, w, i, fill="#1e293b")

    def limpiar_interfaz(self):
        for w in self.root.winfo_children():
            if w != self.canvas: w.destroy()

    def crear_login(self):
        self.limpiar_interfaz()
        card = tk.Frame(self.root, bg="#0f172a", bd=1, relief="solid", highlightthickness=1, highlightbackground="#334155")
        card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=520)

        tk.Label(card, text="pyGallery", bg="#0f172a", fg="#3b82f6", font=("DM Sans", 32, "bold")).pack(pady=(30, 5))
        tk.Label(card, text="ENVIRONMENT TESTING", bg="#0f172a", fg="#10b981", font=("DM Sans", 10, "bold")).pack(pady=(0, 20))

        f_form = tk.Frame(card, bg="#0f172a")
        f_form.pack(fill="x", padx=40)

        tk.Label(f_form, text="Usuario", bg="#0f172a", fg="#94a3b8", font=("DM Sans", 11)).pack(anchor="w")
        self.entry_user = tk.Entry(f_form, font=("DM Sans", 13), bg="#1e293b", fg="#f8fafc", insertbackground="white", bd=0, highlightthickness=1, highlightbackground="#334155")
        self.entry_user.pack(ipady=8, fill="x", pady=(5, 15))

        tk.Label(f_form, text="Contraseña", bg="#0f172a", fg="#94a3b8", font=("DM Sans", 11)).pack(anchor="w")
        self.entry_pass = tk.Entry(f_form, show="*", font=("DM Sans", 13), bg="#1e293b", fg="#f8fafc", insertbackground="white", bd=0, highlightthickness=1, highlightbackground="#334155")
        self.entry_pass.pack(ipady=8, fill="x", pady=(5, 25))

        b_login = tk.Label(f_form, text="Iniciar Sesión", bg="#2563eb", fg="white", font=("DM Sans", 12, "bold"), cursor="hand2")
        b_login.pack(ipady=10, fill="x")
        b_login.bind("<Button-1>", lambda e: self.login())

        b_reg = tk.Label(card, text="¿No tienes una cuenta? Registrate gratis", bg="#0f172a", fg="#60a5fa", font=("DM Sans", 10, "underline"), cursor="hand2")
        b_reg.pack(side="bottom", pady=20)
        b_reg.bind("<Button-1>", lambda e: webbrowser.open(f"{SERVIDOR_URL}/registro"))

    def login(self):
        u, p = self.entry_user.get(), self.entry_pass.get()
        try:
            r = requests.post(f"{SERVIDOR_URL}/api/login", json={"username": u, "password": p, "os_name": self.obtener_os_bonito()}, verify=False, timeout=10)
            if r.status_code == 200:
                d = r.json()
                self.token, self.usuario_id, self.usuario_nombre = d['token'], d['user_id'], d['username']
                with open(ARCHIVO_SESION, "w") as f: f.write(f"{self.token}\n{self.usuario_id}\n{self.usuario_nombre}")
                self.crear_interfaz_sync(self.usuario_nombre)
            else: messagebox.showerror("Error", "Credenciales incorrectas")
        except: messagebox.showerror("Error", "Servidor offline")

    def crear_interfaz_sync(self, nombre):
        self.limpiar_interfaz()
        card_sync = tk.Frame(self.root, bg="#0f172a", bd=1, relief="solid", highlightthickness=1, highlightbackground="#1e293b")
        card_sync.place(relx=0.5, rely=0.48, anchor="center", width=520, height=680)

        tk.Label(card_sync, text="pyGallery Sync", bg="#0f172a", fg="#3b82f6", font=("DM Sans", 22, "bold")).pack(pady=(15, 2))
        tk.Label(card_sync, text=f"Hola, {nombre} • {self.obtener_os_bonito()}", bg="#0f172a", fg="#64748b", font=("DM Sans", 9)).pack()

        tk.Label(card_sync, text="CARPETAS COMPARTIDAS", bg="#0f172a", fg="#60a5fa", font=("DM Sans", 8, "bold")).pack(pady=(15, 5))
        f_carpetas = tk.Frame(card_sync, bg="#020617", bd=1, relief="solid", highlightthickness=1, highlightbackground="#1e293b")
        f_carpetas.pack(padx=30, fill="x")

        self.list_carpetas = tk.Listbox(f_carpetas, bg="#020617", fg="#94a3b8", font=("DM Sans", 9), bd=0, highlightthickness=0, height=4)
        self.list_carpetas.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.actualizar_lista_gui()

        f_btns = tk.Frame(card_sync, bg="#0f172a")
        f_btns.pack(pady=10)

        b_add = tk.Label(f_btns, text="+ Añadir", bg="#1e293b", fg="#10b981", font=("DM Sans", 9, "bold"), cursor="hand2", width=10)
        b_add.pack(side="left", padx=5, ipady=5)
        b_add.bind("<Button-1>", lambda e: self.seleccionar_carpeta())

        b_rem = tk.Label(f_btns, text="- Quitar", bg="#1e293b", fg="#ef4444", font=("DM Sans", 9, "bold"), cursor="hand2", width=10)
        b_rem.pack(side="left", padx=5, ipady=5)
        b_rem.bind("<Button-1>", lambda e: self.quitar_carpeta())

        tk.Label(card_sync, text="ESTADO DEL SISTEMA", bg="#0f172a", fg="#94a3b8", font=("DM Sans", 8, "bold")).pack(pady=(10, 0), anchor="w", padx=35)
        f_log = tk.Frame(card_sync, bg="#020617", bd=1, relief="solid", highlightthickness=1, highlightbackground="#1e293b")
        f_log.pack(pady=5, padx=30, fill="both", expand=True)

        self.log_box = scrolledtext.ScrolledText(f_log, bg="#020617", fg="#10b981", font=("Courier", 10), bd=0, highlightthickness=0, state='disabled')
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)

        f_out = tk.Frame(card_sync, bg="#ef4444", bd=1)
        f_out.pack(side="bottom", pady=20, padx=120, fill="x")

        b_out = tk.Label(f_out, text="Cerrar Sesión", bg="#0f172a", fg="#ef4444", font=("DM Sans", 11, "bold"), cursor="hand2")
        b_out.pack(ipady=8, fill="x")
        b_out.bind("<Button-1>", lambda e: self.detener_y_salir())

        if not self.hilo_activo:
            self.hilo_activo = True
            threading.Thread(target=self.proceso_sincronizacion, daemon=True).start()

    def actualizar_lista_gui(self):
        self.list_carpetas.delete(0, tk.END)
        for c in self.carpetas:
            self.list_carpetas.insert(tk.END, f"📁 {os.path.basename(c)}")

    def log(self, m):
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, f"[{time.strftime('%H:%M')}] {m}\n")
        self.log_box.config(state='disabled')
        self.log_box.see(tk.END)

    def seleccionar_carpeta(self):
        c = filedialog.askdirectory()
        if c and c not in self.carpetas:
            self.carpetas.append(c)
            self.guardar_config_carpetas()
            self.actualizar_lista_gui()
            self.log(f"Nueva carpeta: {os.path.basename(c)}")

    def quitar_carpeta(self):
        sel = self.list_carpetas.curselection()
        if sel:
            idx = sel[0]
            removed = self.carpetas.pop(idx)
            self.guardar_config_carpetas()
            self.actualizar_lista_gui()
            self.log(f"Eliminada: {os.path.basename(removed)}")

    def proceso_sincronizacion(self):
        while self.hilo_activo:
            try:
                r = requests.post(f"{SERVIDOR_URL}/api/check_token", json={"token": self.token}, verify=False, timeout=5)
                if r.status_code != 200:
                    self.root.after(0, lambda: self.detener_y_salir(forzar=True))
                    break
                
                for carpeta in self.carpetas:
                    if not os.path.exists(carpeta): continue
                    archs = [f for f in os.listdir(carpeta) if f.lower().endswith(EXT_VALIDAS)]
                    for n in archs:
                        if n not in self.archivos_enviados:
                            if self.subir_archivo(os.path.join(carpeta, n), n):
                                self.archivos_enviados.add(n)
            except Exception as e:
                self.log(f"Error: {str(e)}")
            time.sleep(10)

    def subir_archivo(self, ruta, n):
        try:
            self.log(f"Subiendo: {n}")
            with open(ruta, 'rb') as f:
                r = requests.post(
                    f"{SERVIDOR_URL}/subir", 
                    files={'archivo': (n, f)}, 
                    data={'titulo': f"Sync: {n}", 'token': self.token}, 
                    verify=False, 
                    timeout=60
                )
                if r.status_code == 200:
                    self.log(f"OK: {n}")
                    return True
                else:
                    self.log(f"Fallo {r.status_code}: {n}")
            return False
        except Exception as e:
            self.log(f"Error red: {str(e)}")
            return False

    def detener_y_salir(self, forzar=False):
        self.hilo_activo = False
        if not forzar and self.token:
            try: requests.post(f"{SERVIDOR_URL}/api/logout", json={"token": self.token}, verify=False, timeout=3)
            except: pass
        self.token = None
        if os.path.exists(ARCHIVO_SESION): os.remove(ARCHIVO_SESION)
        self.crear_login()

if __name__ == "__main__":
    root = tk.Tk()
    app = PyGalleryApp(root, on_close_callback=lambda: root.iconify() if platform.system() == "Darwin" else root.withdraw())
    root.mainloop()