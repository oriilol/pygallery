import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import requests
import webbrowser
import os
import threading
import pystray
import time
from PIL import Image, ImageDraw
import urllib3

SERVIDOR_URL = "https://192.168.1.39:5000"

EXT_VALIDAS = ('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov', '.avi', '.mkv')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PyGalleryApp:
    def __init__(self, root, on_close_callback):
        self.root = root
        self.on_close_callback = on_close_callback

        self.root.title("pygallery Desktop Sync")
        self.root.geometry("500x550")
        self.root.configure(bg="#222")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_callback)

        self.usuario_id = None
        self.session = None
        self.carpeta_sync = None
        self.archivos_enviados = set()
        self.hilo_activo = False

        self.crear_login()

    def crear_login(self):
        self.limpiar_ventana()

        tk.Label(self.root, text="pygallery Desktop Sync", bg="#222", fg="white", font=("Segoe UI", 16, "bold")).pack(pady=30)

        tk.Label(self.root, text="Usuario:", bg="#222", fg="#aaa").pack()
        self.entry_user = tk.Entry(self.root, font=("Arial", 11))
        self.entry_user.pack(pady=5)

        tk.Label(self.root, text="Contrasena:", bg="#222", fg="#aaa").pack()
        self.entry_pass = tk.Entry(self.root, show="*", font=("Arial", 11))
        self.entry_pass.pack(pady=5)

        tk.Button(self.root, text="Iniciar Sesion", command=self.login, bg="#444", fg="white", font=("Arial", 11), bd=0, padx=20, pady=5).pack(pady=30)

        btn_reg = tk.Label(self.root, text="Crear cuenta nueva", bg="#222", fg="#3498db", cursor="hand2")
        btn_reg.pack()
        btn_reg.bind("<Button-1>", lambda e: webbrowser.open(f"{SERVIDOR_URL}/registro"))

    def login(self):
        user = self.entry_user.get()
        password = self.entry_pass.get()

        try:
            respuesta = requests.post(f"{SERVIDOR_URL}/api/login", json={"username": user, "password": password}, verify=False)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                self.usuario_id = datos['user_id']
                self.session = requests.Session()
                self.session.post(f"{SERVIDOR_URL}/login", data={"username": user, "password": password}, verify=False)
                self.crear_interfaz_sync(datos.get('username', 'Usuario'))
            else:
                messagebox.showerror("Error", "Credenciales incorrectas")
        except Exception as e:
            messagebox.showerror("Error Conexion", f"No se pudo conectar: {e}")

    def crear_interfaz_sync(self, nombre):
        self.limpiar_ventana()

        tk.Label(self.root, text=f"Usuario: {nombre}", bg="#222", fg="white", font=("Segoe UI", 12)).pack(pady=10)

        self.lbl_estado = tk.Label(self.root, text="Estado: Inactivo", bg="#222", fg="#aaa", font=("Arial", 10))
        self.lbl_estado.pack(pady=5)

        tk.Button(self.root, text="Seleccionar Carpeta", command=self.seleccionar_carpeta, bg="#444", fg="white", font=("Arial", 11), pady=5).pack(pady=15)

        self.log_box = scrolledtext.ScrolledText(self.root, width=55, height=15, bg="#333", fg="#ccc", font=("Consolas", 8))
        self.log_box.pack(pady=10, padx=10)

        tk.Button(self.root, text="Cerrar Sesion", command=self.detener_y_salir, bg="#882222", fg="white").pack(pady=10)

    def log(self, mensaje):
        self.log_box.insert(tk.END, f"{mensaje}\n")
        self.log_box.see(tk.END)

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta_sync = carpeta
            self.lbl_estado.config(text=f"Sincronizando: {os.path.basename(carpeta)}", fg="#2ecc71")
            self.log(f"Carpeta: {carpeta}")

            if not self.hilo_activo:
                self.hilo_activo = True
                threading.Thread(target=self.proceso_sincronizacion, daemon=True).start()

    def proceso_sincronizacion(self):
        while self.hilo_activo:
            self.log("Escaneando...")

            try:
                for nombre_archivo in os.listdir(self.carpeta_sync):
                    if nombre_archivo.lower().endswith(EXT_VALIDAS):
                        ruta_completa = os.path.join(self.carpeta_sync, nombre_archivo)

                        if nombre_archivo not in self.archivos_enviados:
                            self.subir_archivo(ruta_completa, nombre_archivo)
            except Exception as e:
                self.log(f"Error: {e}")

            time.sleep(300)

    def subir_archivo(self, ruta, nombre):
        try:
            self.log(f"Subiendo: {nombre}")
            archivos = {'archivo': open(ruta, 'rb')}
            datos = {'titulo': nombre}

            r = self.session.post(f"{SERVIDOR_URL}/subir", files=archivos, data=datos, verify=False)

            if r.status_code == 200:
                self.log("Completado.")
                self.archivos_enviados.add(nombre)
            else:
                self.log(f"Fallo al subir {nombre}")

        except Exception as e:
            self.log(f"Error red: {e}")

    def detener_y_salir(self):
        self.hilo_activo = False
        self.crear_login()

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

def crear_icono(root):
    image = Image.new('RGB', (64, 64), color='#333')
    d = ImageDraw.Draw(image)
    d.rectangle([(20, 20), (44, 44)], fill='white')

    def restaurar(icon, item):
        root.after(0, root.deiconify)

    def salir(icon, item):
        icon.stop()
        root.after(0, root.destroy)

    menu = pystray.Menu(pystray.MenuItem('Abrir', restaurar), pystray.MenuItem('Salir', salir))
    return pystray.Icon("pygallery", image, "pygallery Sync", menu)

def main():
    root = tk.Tk()
    icon = crear_icono(root)

    def ocultar_ventana():
        root.withdraw()
        if not icon.visible:
            threading.Thread(target=icon.run, daemon=True).start()

    app = PyGalleryApp(root, on_close_callback=ocultar_ventana)
    root.mainloop()

if __name__ == "__main__":
    main()
