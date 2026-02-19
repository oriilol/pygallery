from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secreto_clave_clase_smr'

CONFIG_BD = {
    'host': 'localhost',
    'user': 'pyuser',      
    'password': '1234',    
    'database': 'pygallery_db'
}

CARPETA_IMAGENES = os.path.join('static', 'imagenes')
app.config['UPLOAD_FOLDER'] = CARPETA_IMAGENES
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

EXTENSIONES_FOTO = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
EXTENSIONES_VIDEO = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
EXTENSIONES_VALIDAS = EXTENSIONES_FOTO.union(EXTENSIONES_VIDEO)

LIMITE_ESPACIO_BYTES = 15 * 1024 * 1024 * 1024 


def conectar_bd():
    return mysql.connector.connect(**CONFIG_BD)

def archivo_permitido(nombre_archivo):
    return '.' in nombre_archivo and \
           nombre_archivo.rsplit('.', 1)[1].lower() in EXTENSIONES_VALIDAS

def obtener_carpeta_usuario(usuario_id):
    ruta_usuario = os.path.join(app.config['UPLOAD_FOLDER'], str(usuario_id))
    if not os.path.exists(ruta_usuario):
        os.makedirs(ruta_usuario)
    return ruta_usuario

def calcular_espacio_usuario(usuario_id):
    espacio_total = 0
    ruta_usuario = obtener_carpeta_usuario(usuario_id)
    for archivo in os.listdir(ruta_usuario):
        ruta_archivo = os.path.join(ruta_usuario, archivo)
        if os.path.isfile(ruta_archivo):
            espacio_total += os.path.getsize(ruta_archivo)
    return espacio_total

def formatear_espacio(bytes_size):
    mb = bytes_size / (1024 * 1024)
    if mb < 1024:
        return f"{mb:.2f} MB"
    gb = mb / 1024
    return f"{gb:.2f} GB"


@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        datos = request.json
        usuario = datos.get('username')
        clave = datos.get('password')
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (usuario, clave))
        user = cursor.fetchone()
        cursor.close()
        conexion.close()
        if user:
            return jsonify({'status': 'ok', 'user_id': user['id'], 'username': user['username']})
        return jsonify({'status': 'error', 'message': 'Credenciales incorrectas'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def inicio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    id_actual = session['usuario_id']
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM fotos WHERE usuario_id = %s ORDER BY fecha DESC", (id_actual,))
        lista_fotos = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        bytes_usados = calcular_espacio_usuario(id_actual)
        porcentaje = (bytes_usados / LIMITE_ESPACIO_BYTES) * 100
        texto_espacio = formatear_espacio(bytes_usados)
        
        return render_template('index.html', fotos=lista_fotos, 
                               espacio_usado=texto_espacio, 
                               porcentaje=porcentaje)
    except Exception as e:
        return f"Error: {e}"

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nuevo_usuario = request.form['username']
        nueva_clave = request.form['password']
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (nuevo_usuario, nueva_clave))
            conexion.commit()
            cursor.close()
            conexion.close()
            flash("Cuenta creada con exito. Inicia sesion.")
            return redirect(url_for('login'))
        except mysql.connector.Error:
            flash("Error: El nombre de usuario ya existe.")
            return render_template('registro.html')
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        clave = request.form['password']
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (usuario, clave))
        user_encontrado = cursor.fetchone()
        cursor.close()
        conexion.close()
        if user_encontrado:
            session['usuario_id'] = user_encontrado['id']
            session['usuario_nombre'] = user_encontrado['username']
            return redirect(url_for('inicio'))
        else:
            flash("Usuario o contraseña incorrectos.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

@app.route('/subir', methods=['GET', 'POST'])
def subir_foto():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    id_actual = session['usuario_id']
    bytes_usados = calcular_espacio_usuario(id_actual)
    esta_lleno = bytes_usados >= LIMITE_ESPACIO_BYTES

    if request.method == 'POST':
        if esta_lleno:
            flash("No tienes espacio suficiente (Limite 15GB).")
            return redirect(url_for('subir_foto'))

        archivo = request.files['archivo']
        if archivo and archivo_permitido(archivo.filename):
            archivo.seek(0, os.SEEK_END)
            tamano_nuevo = archivo.tell()
            archivo.seek(0)

            if (bytes_usados + tamano_nuevo) > LIMITE_ESPACIO_BYTES:
                flash("Este archivo supera el limite de 15GB.")
                return redirect(url_for('subir_foto'))

            timestamp = int(time.time())
            nombre_seguro = f"{timestamp}_{secure_filename(archivo.filename)}"
            
            carpeta_user = obtener_carpeta_usuario(id_actual)
            ruta_destino = os.path.join(carpeta_user, nombre_seguro)
            archivo.save(ruta_destino)

            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO fotos (nombre_archivo, titulo, fecha, usuario_id) VALUES (%s, %s, NOW(), %s)", 
                           (nombre_seguro, request.form.get('titulo'), id_actual))
            conexion.commit()
            cursor.close()
            conexion.close()
            return redirect(url_for('inicio'))
            
    return render_template('subir.html', lleno=esta_lleno)

@app.route('/borrar/<int:foto_id>')
def borrar_foto(foto_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    id_actual = session['usuario_id']
    conexion = conectar_bd()
    cursor_dict = conexion.cursor(dictionary=True)
    cursor_dict.execute("SELECT nombre_archivo FROM fotos WHERE id = %s AND usuario_id = %s", (foto_id, id_actual))
    foto = cursor_dict.fetchone()
    if foto:
        ruta = os.path.join(obtener_carpeta_usuario(id_actual), foto['nombre_archivo'])
        if os.path.exists(ruta):
            os.remove(ruta)
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM fotos WHERE id = %s", (foto_id,))
        conexion.commit()
        cursor.close()
    cursor_dict.close()
    conexion.close()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(host='192.168.1.39', port=5000, ssl_context=('cert.pem', 'key.pem'), debug=True)
#Ha pasado un fallo tecnico que he subido el codigo con la cuenta de Gonzalo, ya que el usó mi ordenador la semana pasada.