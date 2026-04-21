import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import requests
import webbrowser
import os
import threading
import pystray
import time
import platform
from PIL import Image, ImageDraw
import urllib3

SERVIDOR_URL = "http://127.0.0.1:5000"

EXT_VALIDAS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.mp4', '.mov', '.avi', '.mkv', '.webm')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PyGalleryApp:
    def __init__(self, root, on_close_callback):
        self.root = root
        self.on_close_callback = on_close_callback

        self.root.title("pygallery Desktop Sync (ver. local de prueba)")
        self.root.geometry("500x550")
        self.root.configure(bg="#1e1e1e")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_callback)

        self.usuario_id = None
        self.session = None
        self.carpeta_sync = None
        self.archivos_enviados = set()
        self.hilo_activo = False

        self.crear_login()

    def crear_login(self):
        self.limpiar_ventana()
        tk.Label(self.root, text="pygallery", bg="#1e1e1e", fg="#3b82f6", font=("Arial", 24, "bold")).pack(pady=(40,0))
        tk.Label(self.root, text="Desktop Sync", bg="#1e1e1e", fg="white", font=("Arial", 10)).pack(pady=(0,20))

        tk.Label(self.root, text="Usuario:", bg="#1e1e1e", fg="#aaa").pack()
        self.entry_user = tk.Entry(self.root, font=("Arial", 11), bg="#333", fg="white", insertbackground="white", bd=0)
        self.entry_user.pack(pady=5, ipady=5, padx=50, fill="x")

        tk.Label(self.root, text="Contraseña:", bg="#1e1e1e", fg="#aaa").pack()
        self.entry_pass = tk.Entry(self.root, show="*", font=("Arial", 11), bg="#333", fg="white", insertbackground="white", bd=0)
        self.entry_pass.pack(pady=5, ipady=5, padx=50, fill="x")

        tk.Button(self.root, text="INICIAR SESIÓN", command=self.login, bg="#2563eb", fg="white", font=("Arial", 10, "bold"), bd=0, cursor="hand2").pack(pady=30, ipady=10, padx=50, fill="x")

        btn_reg = tk.Label(self.root, text="¿No tienes cuenta? Regístrate, ahora mismo.", bg="#1e1e1e", fg="#3498db", cursor="hand2")
        btn_reg.pack()
        btn_reg.bind("<Button-1>", lambda e: webbrowser.open(f"{SERVIDOR_URL}/registro"))

    def login(self):
        user = self.entry_user.get()
        password = self.entry_pass.get()
        try:
            respuesta = requests.post(f"{SERVIDOR_URL}/api/login", json={"username": user, "password": password}, verify=False, timeout=10)

            if respuesta.status_code == 200:
                datos = respuesta.json()
                self.usuario_id = datos['user_id']
                self.session = requests.Session()
                self.session.post(f"{SERVIDOR_URL}/login", data={"username": user, "password": password}, verify=False)
                self.crear_interfaz_sync(datos.get('username', 'Usuario'))
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos")
        except Exception as e:
            messagebox.showerror("Error de Red", f"No se pudo conectar con el servidor: {e}")

    def crear_interfaz_sync(self, nombre):
        self.limpiar_ventana()
        tk.Label(self.root, text=f"Bienvenido, {nombre}", bg="#1e1e1e", fg="white", font=("Arial", 14, "bold")).pack(pady=10)

        self.lbl_estado = tk.Label(self.root, text="Estado: Esperando configuración...", bg="#1e1e1e", fg="#ef4444", font=("Arial", 9))
        self.lbl_estado.pack(pady=5)

        tk.Button(self.root, text="SELECCIONAR CARPETA", command=self.seleccionar_carpeta, bg="#334155", fg="white", font=("Arial", 9, "bold"), bd=0).pack(pady=10, ipady=8, padx=100, fill="x")

        self.log_box = scrolledtext.ScrolledText(self.root, width=55, height=12, bg="#0f172a", fg="#94a3b8", font=("Consolas", 8), bd=0)
        self.log_box.pack(pady=10, padx=20)

        tk.Button(self.root, text="Cerrar Sesión", command=self.detener_y_salir, bg="#b91c1c", fg="white", bd=0).pack(pady=10, padx=150, fill="x")

    def log(self, mensaje):
        self.log_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {mensaje}\n")
        self.log_box.see(tk.END)

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta_sync = carpeta
            self.lbl_estado.config(text=f"Sincronizando: {os.path.basename(carpeta)}", fg="#2ecc71")
            self.log(f"Configurado: {carpeta}")

            if not self.hilo_activo:
                self.hilo_activo = True
                threading.Thread(target=self.proceso_sincronizacion, daemon=True).start()

    def proceso_sincronizacion(self):
        while self.hilo_activo:
            if self.carpeta_sync:
                try:
                    archivos_en_carpeta = [f for f in os.listdir(self.carpeta_sync) if f.lower().endswith(EXT_VALIDAS)]
                    for nombre_archivo in archivos_en_carpeta:
                        if not self.hilo_activo: break
                        
                        ruta_completa = os.path.join(self.carpeta_sync, nombre_archivo)
                        
                        if nombre_archivo not in self.archivos_enviados:
                            exito = self.subir_archivo(ruta_completa, nombre_archivo)
                            if not exito:
                                break 
                except Exception as e:
                    self.log(f"Error de escaneo: {e}")

            time.sleep(10)

    def subir_archivo(self, ruta, nombre):
        try:
            self.log(f"Subiendo: {nombre}...")
            with open(ruta, 'rb') as f:
                archivos = {'archivo': (nombre, f)}
                datos = {'titulo': f"Sync: {nombre}"}
                
                r = self.session.post(f"{SERVIDOR_URL}/subir", files=archivos, data=datos, verify=False, timeout=60)

                texto_respuesta = r.text.lower()
                
                errores_limite = ["no tienes espacio suficiente", "límite de 15gb", "limite de 15gb", "supera los 15gb"]
                
                if any(error in texto_respuesta for error in errores_limite):
                    self.log("ERROR: Nube llena (15GB alcanzados).")
                    messagebox.showwarning("Almacenamiento Lleno", "Has alcanzado el límite de 15GB.")
                    return False

                if r.status_code == 200:
                    self.log(f"Completado.")
                    self.archivos_enviados.add(nombre)
                    return True
                else:
                    self.log(f"Fallo al subir {nombre}")
                    return True

        except Exception as e:
            self.log(f"Error de red: {e}")
            return False

    def detener_y_salir(self):
        self.hilo_activo = False
        self.crear_login()

    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

def crear_icono(root):
    image = Image.new('RGB', (64, 64), color='#1e1e1e')
    d = ImageDraw.Draw(image)
    d.rectangle([(15, 15), (49, 49)], fill='#2563eb')

    def restaurar(icon, item):
        root.after(0, root.deiconify)

    def salir(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(pystray.MenuItem('Abrir pygallery', restaurar), pystray.MenuItem('Cerrar Aplicación', salir))
    return pystray.Icon("pygallery", image, "pygallery Sync", menu)

def main():
    root = tk.Tk()
    
    es_mac = platform.system() == "Darwin"

    if not es_mac:
        icon = crear_icono(root)

    def manejar_cierre():
        if es_mac:
            root.iconify()
        else:
            root.withdraw()
            if not icon.visible:
                threading.Thread(target=icon.run, daemon=True).start()

    app = PyGalleryApp(root, on_close_callback=manejar_cierre)

    if es_mac:
        try:
            root.createcommand('tk::mac::Quit', lambda: os._exit(0))
        except Exception:
            pass

    root.mainloop()

if __name__ == "__main__":
    main()