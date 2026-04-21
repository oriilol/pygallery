# pyGallery (⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️ RAMA DE TESTING)

![Static Badge](https://img.shields.io/badge/Ubuntu-24.04-red?style=for-the-badge&logo=ubuntu)
![Static Badge](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Static Badge](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Static Badge](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python&logoColor=white)
![Static Badge](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![Static Badge](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

# ⚠️ (Estás en la rama 'testing'. Es decir, este no es el proyecto en sí. Esta versión corre en localhost para trastear con el programa y puede tener mas cosas que la versión de 'main'. Si quieres usar el proyecto real, ve a la rama 'main'.)

Plataforma de almacenamiento en la nube privada dedicada a la gestión y sincronización de fotos y vídeos. 

PyGallery es una alternativa para mantener el control total sobre la privacidad de los datos y el almacenamiento multimedia, aplicando conocimientos de despliegue de servidores, bases de datos y desarrollo web.

El proyecto se divide en dos componentes principales:

## 1. pyGallery Server (Aplicación Web)
Es el núcleo del proyecto, encargado de gestionar los usuarios, almacenar los archivos de forma segura y servir la interfaz gráfica.

* **Desarrollo:** Backend construido en Python usando el framework Flask. Interfaz web desarrollada con HTML y CSS (diseño asistido por IA para lograr un acabado moderno y responsivo).
* **Multimedia:** Soporte nativo para la previsualización de imágenes y reproducción de vídeos directamente desde el navegador.
* **Seguridad perimetral y de archivos:** Filtro de extensiones en el backend que bloquea la subida de archivos potencialmente peligrosos o no multimedia (ej. `.exe`, `.pdf`).
* **Probado en Ubuntu Server 24.04** (si se va a hostear, esta es la distro recomendable)
* **Acceso Remoto:** El servidor es accesible externamente a través de un dominio dinámico (DDNS) gestionado con No-IP, permitiendo el acceso desde cualquier red. [Aquí se puede entrar a la web hosteada](https://pygallery.ddns.net:5000)
* **Límite de almacenamiento personalizado:** Cada usuario tiene una cuota de límite de almacenamiento de 15GB. Esto es personalizable.

## 2. pyGallery Desktop Sync
Aplicación de escritorio diseñada para ejecutarse en segundo plano y mantener copias de seguridad automáticas de los archivos del usuario.

* **Desarrollo:** Probado y optimizado para entornos Linux.
* **Plataformas:** Windows, Linux, MacOS
* **Sincronización en segundo plano:** El usuario inicia sesión, selecciona las carpetas locales y la aplicación comprueba automáticamente cada 5 minutos si hay archivos nuevos para subirlos al servidor.
* **Conexión directa:** Se conecta a la base de datos del servidor para registrar y subir los nuevos archivos.
* **Seguridad de borrado:** La sincronización es de subida. Para evitar pérdidas accidentales de datos desde el cliente local, la eliminación de archivos solo está permitida de forma manual a través de la aplicación web.

## Créditos
* **Servidor, Interfaz Web y Bases de datos:** Cristian
* **Aplicación de Sincronización (Desktop Sync):** Gonzalo
