# pyGallery

Una nube privada para fotos y vídeos que puedes hostear tú mismo. Sin Google, sin iCloud, sin que nadie más tenga tus archivos.

---

## ¿Qué es esto?

pyGallery nació de una idea simple: tener un Google Photos propio, corriendo en un servidor de casa, al que puedas acceder desde cualquier sitio. El proyecto tiene dos partes que trabajan juntas:

- **pyGallery Server** → la aplicación web donde se sube, visualiza y gestiona todo
- **pyGallery Desktop Sync** → una app de escritorio que vigila tus carpetas locales y sube los archivos nuevos automáticamente en segundo plano

Está pensado para uso personal o entre un grupo pequeño de personas de confianza, donde cada usuario tiene su propio espacio aislado de los demás.

---

## Stack

- **Backend:** Python + Flask
- **Frontend:** HTML/CSS con Jinja2 (tipografía DM Sans, tema oscuro basado en slate de Tailwind)
- **Base de datos:** SQLite (gestionada desde Flask)
- **Servidor probado en:** Ubuntu Server 24.04
- **Acceso externo:** DDNS con No-IP

---

## Funcionalidades del servidor

### Cuentas y sesiones
- Registro e inicio de sesión con usuario y contraseña
- Cada usuario tiene su propio directorio de archivos completamente separado del resto
- Opción de eliminar la cuenta, que borra también todos los archivos asociados de manera permanente

### Galería
- Vista en cuadrícula que carga las imágenes con `lazy loading` para no matar el ancho de banda
- Al hacer clic en cualquier archivo se abre un modal a pantalla completa, sin salir de la página
- Los vídeos se reproducen directamente en el modal con controles nativos del navegador
- Formatos de imagen soportados: `png`, `jpg`, `jpeg`, `gif`, `webp`
- Formatos de vídeo soportados: `mp4`, `webm`, `mov`, `avi`, `mkv`
- Los archivos de otros formatos se muestran igualmente en la galería y se ofrecen como descarga

### Subida de archivos
- El backend filtra las extensiones permitidas antes de guardar nada, así que no se puede colar un `.exe` disfrazado de imagen
- Se puede añadir un título al archivo al subirlo (opcional; si no se pone, se usa el nombre del archivo)
- El formulario de subida solo acepta los formatos multimedia definidos, también a nivel de HTML

### Almacenamiento y cuotas
- Cada cuenta tiene un límite de **15 GB** (configurable directamente en el código del servidor)
- La pantalla principal muestra una barra de progreso con el espacio consumido
- Si el uso supera el 90%, la barra cambia a rojo como aviso visual
- Cuando se alcanza el límite, el formulario de subida se reemplaza por un mensaje de aviso y no se puede subir nada más

### Compartir archivos
- Cualquier archivo puede compartirse mediante un enlace único generado por el servidor
- El enlace lleva a una página pública que no requiere login, donde se puede ver o reproducir el archivo
- El enlace se puede revocar en cualquier momento desde la galería; en cuanto se desactiva, deja de funcionar al instante
- El botón de "Copiar enlace" usa la Clipboard API del navegador para copiarlo sin fricciones

---

## pyGallery Desktop Sync

Aplicación de escritorio desarrollada por **Gonzalo**, compatible con Windows, Linux y macOS.

Funciona en segundo plano: el usuario inicia sesión una sola vez, selecciona las carpetas que quiere vigilar, y la app comprueba cada 5 minutos si hay archivos nuevos para subirlos al servidor automáticamente.

Un detalle importante en el diseño: **la sincronización es solo de subida**. Borrar un archivo de tu equipo no lo elimina del servidor, y viceversa. Esto es intencional, para evitar pérdidas accidentales de datos. Si quieres borrar algo del servidor, tienes que hacerlo manualmente desde la web.

---

## Instalación del servidor

### Requisitos
- Python 3.10 o superior
- pip
- Un servidor Linux (recomendado Ubuntu Server 24.04)

### Pasos

```bash
# Clona el repositorio
git clone https://github.com/oriilol/pygallery.git
cd pygallery

# Instala las dependencias
pip install -r requirements.txt

# Arranca el servidor
python app.py
```

Por defecto el servidor corre en `http://localhost:5000`. Para exponerlo al exterior necesitarás configurar el reenvío de puertos en tu router y, si quieres un dominio fijo, un servicio de DDNS como No-IP.

> La instancia que tenemos corriendo está en [pygallery.ddns.net:5000](https://pygallery.ddns.net:5000)

### Configuración del límite de almacenamiento

El límite de 15 GB por usuario está definido como constante en `app.py`. Búscala y cámbiala por el valor que necesites:

```python
LIMITE_ALMACENAMIENTO_GB = 15
```

---

## Estructura del proyecto

```
pygallery/
├── app.py                  # Lógica principal del servidor Flask
├── requirements.txt
├── static/
│   ├── style.css           # Todos los estilos (tema oscuro, galería, modales...)
│   └── imagenes/
│       └── {usuario_id}/   # Archivos de cada usuario en su propia carpeta
└── templates/
    ├── index.html          # Galería principal
    ├── login.html          # Inicio de sesión
    ├── registro.html       # Crear cuenta
    ├── subir.html          # Formulario de subida
    └── ver_compartido.html # Vista pública de archivos compartidos
```

---

## Créditos

- **Servidor, interfaz web y base de datos:** Cristian
- **Aplicación de sincronización de escritorio:** Gonzalo
