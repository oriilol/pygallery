from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import os
import time
import shutil
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secreto_clave_clase_smr'

CONFIG_BD = {
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

@app.template_filter('tamano_archivo')
def tamano_archivo(nombre_archivo, usuario_id):
    ruta = os.path.join(obtener_carpeta_usuario(usuario_id), nombre_archivo)
    if os.path.exists(ruta):
        return formatear_espacio(os.path.getsize(ruta))
    return "0 MB"

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        datos = request.json
        usuario = datos.get('username')
        clave = datos.get('password')
        os_name = datos.get('os_name', 'Desconocido')
        
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (usuario, clave))
        user = cursor.fetchone()
        
        if user:
            token = uuid.uuid4().hex
            cursor.execute("INSERT INTO sesiones_sync (usuario_id, os_name, token) VALUES (%s, %s, %s)", (user['id'], os_name, token))
            conexion.commit()
            cursor.close()
            conexion.close()
            return jsonify({'status': 'ok', 'user_id': user['id'], 'username': user['username'], 'token': token})
            
        cursor.close()
        conexion.close()
        return jsonify({'status': 'error', 'message': 'Credenciales incorrectas'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/check_token', methods=['POST'])
def check_token():
    try:
        datos = request.json
        token = datos.get('token')
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id FROM sesiones_sync WHERE token = %s", (token,))
        sesion = cursor.fetchone()
        cursor.close()
        conexion.close()
        
        if sesion:
            return jsonify({'status': 'ok'})
        return jsonify({'status': 'error'}), 401
    except:
        return jsonify({'status': 'error'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    try:
        datos = request.json
        token = datos.get('token')
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM sesiones_sync WHERE token = %s", (token,))
        conexion.commit()
        cursor.close()
        conexion.close()
        return jsonify({'status': 'ok'})
    except:
        return jsonify({'status': 'error'}), 500

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return render_template('index.html')

    usuario_id = session['usuario_id']
    page = request.args.get('page', 1, type=int)
    per_page = 12
    offset = (page - 1) * per_page

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as total FROM fotos WHERE usuario_id = %s AND eliminado = FALSE", (usuario_id,))
    total_fotos = cursor.fetchone()['total']
    total_pages = (total_fotos + per_page - 1) // per_page
    if total_pages == 0:
        total_pages = 1

    cursor.execute("SELECT * FROM fotos WHERE usuario_id = %s AND eliminado = FALSE ORDER BY fecha DESC LIMIT %s OFFSET %s", (usuario_id, per_page, offset))
    fotos = cursor.fetchall()
    cursor.close()
    conexion.close()

    espacio_usado_bytes = calcular_espacio_usuario(usuario_id)
    espacio_usado = formatear_espacio(espacio_usado_bytes)
    porcentaje = (espacio_usado_bytes / LIMITE_ESPACIO_BYTES) * 100

    return render_template('index.html', fotos=fotos, espacio_usado=espacio_usado, porcentaje=porcentaje, page=page, total_pages=total_pages)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'usuario_id' in session:
        return redirect(url_for('index'))

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
            flash("Cuenta creada con exito. Inicia sesion.", "exito")
            return redirect(url_for('login'))
        except mysql.connector.Error:
            flash("El usuario ya existe.", "error")
            return render_template('registro.html')
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('index'))

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
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/ajustes')
def ajustes():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sesiones_sync WHERE usuario_id = %s ORDER BY fecha_conexion DESC", (session['usuario_id'],))
    sesiones_activas = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    return render_template('ajustes.html', sesiones=sesiones_activas)

@app.route('/revocar_sesion/<token>', methods=['POST'])
def revocar_sesion(token):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM sesiones_sync WHERE token = %s AND usuario_id = %s", (token, session['usuario_id']))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    flash("Sincronizador desvinculado correctamente.", "exito")
    return redirect(url_for('ajustes'))

@app.route('/subir', methods=['GET', 'POST'])
def subir_foto():
    user_id = None
    token_sync = request.form.get('token')
    
    if token_sync:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT usuario_id FROM sesiones_sync WHERE token = %s", (token_sync,))
        sesion_encontrada = cursor.fetchone()
        cursor.close()
        conexion.close()
        if sesion_encontrada:
            user_id = sesion_encontrada['usuario_id']

    if not user_id and 'usuario_id' in session:
        user_id = session['usuario_id']

    if not user_id:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

    bytes_usados = calcular_espacio_usuario(user_id)
    esta_lleno = bytes_usados >= LIMITE_ESPACIO_BYTES

    if request.method == 'POST':
        if esta_lleno:
            return jsonify({'status': 'error', 'message': 'Espacio lleno'}), 400

        archivo = request.files.get('archivo')
        if archivo and archivo_permitido(archivo.filename):
            archivo.seek(0, os.SEEK_END)
            tamano_nuevo = archivo.tell()
            archivo.seek(0)

            if (bytes_usados + tamano_nuevo) > LIMITE_ESPACIO_BYTES:
                return jsonify({'status': 'error', 'message': 'Supera limite'}), 400

            timestamp = int(time.time())
            nombre_seguro = f"{timestamp}_{secure_filename(archivo.filename)}"
            
            carpeta_user = obtener_carpeta_usuario(user_id)
            ruta_destino = os.path.join(carpeta_user, nombre_seguro)
            archivo.save(ruta_destino)

            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO fotos (nombre_archivo, titulo, fecha, usuario_id) VALUES (%s, %s, NOW(), %s)", 
                           (nombre_seguro, request.form.get('titulo', 'Sin titulo'), user_id))
            conexion.commit()
            cursor.close()
            conexion.close()
            return jsonify({'status': 'ok', 'filename': nombre_seguro})
            
    return render_template('subir.html', lleno=esta_lleno)

@app.route('/papelera')
def papelera():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    id_actual = session['usuario_id']
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fotos WHERE usuario_id = %s AND eliminado = TRUE ORDER BY fecha DESC", (id_actual,))
    fotos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('papelera.html', fotos=fotos)

@app.route('/borrar/<int:foto_id>')
def borrar_foto(foto_id):
    if 'usuario_id' not in session: return redirect(url_for('login'))
    id_actual = session['usuario_id']
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("UPDATE fotos SET eliminado = TRUE WHERE id = %s AND usuario_id = %s", (foto_id, id_actual))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('index'))

@app.route('/restaurar/<int:foto_id>')
def restaurar_foto(foto_id):
    if 'usuario_id' not in session: return redirect(url_for('login'))
    id_actual = session['usuario_id']
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("UPDATE fotos SET eliminado = FALSE WHERE id = %s AND usuario_id = %s", (foto_id, id_actual))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('papelera'))

@app.route('/borrar_definitivo/<int:foto_id>')
def borrar_definitivo(foto_id):
    if 'usuario_id' not in session: return redirect(url_for('login'))
    id_actual = session['usuario_id']
    conexion = conectar_bd()
    cursor_dict = conexion.cursor(dictionary=True)
    cursor_dict.execute("SELECT nombre_archivo FROM fotos WHERE id = %s AND usuario_id = %s AND eliminado = TRUE", (foto_id, id_actual))
    foto = cursor_dict.fetchone()
    if foto:
        ruta = os.path.join(obtener_carpeta_usuario(id_actual), foto['nombre_archivo'])
        if os.path.exists(ruta): os.remove(ruta)
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM fotos WHERE id = %s", (foto_id,))
        conexion.commit()
        cursor.close()
    cursor_dict.close()
    conexion.close()
    return redirect(url_for('papelera'))

@app.route('/borrar_cuenta', methods=['POST'])
def borrar_cuenta():
    if 'usuario_id' not in session: return redirect(url_for('login'))
    id_actual = session['usuario_id']
    password_ingresada = request.form.get('password')
    
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT password FROM usuarios WHERE id = %s", (id_actual,))
    user = cursor.fetchone()
    
    if not user or user['password'] != password_ingresada:
        flash("Contraseña incorrecta.", "error")
        cursor.close()
        conexion.close()
        return redirect(url_for('ajustes'))
        
    cursor.execute("DELETE FROM fotos WHERE usuario_id = %s", (id_actual,))
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_actual,))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    ruta_usuario = obtener_carpeta_usuario(id_actual)
    if os.path.exists(ruta_usuario): shutil.rmtree(ruta_usuario)
    session.clear()
    flash("Tu cuenta y todos tus archivos han sido eliminados.", "exito")
    return redirect(url_for('login'))

@app.route('/compartir/<int:foto_id>', methods=['POST'])
def compartir_foto(foto_id):
    if 'usuario_id' not in session: return redirect(url_for('login'))
    enlace_unico = uuid.uuid4().hex
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("UPDATE fotos SET enlace_compartido = %s WHERE id = %s AND usuario_id = %s", (enlace_unico, foto_id, session['usuario_id']))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('index'))

@app.route('/dejar_compartir/<int:foto_id>', methods=['POST'])
def dejar_compartir(foto_id):
    if 'usuario_id' not in session: return redirect(url_for('login'))
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("UPDATE fotos SET enlace_compartido = NULL WHERE id = %s AND usuario_id = %s", (foto_id, session['usuario_id']))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for('index'))

@app.route('/v/<enlace>')
def ver_compartido(enlace):
    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT f.*, u.username FROM fotos f JOIN usuarios u ON f.usuario_id = u.id WHERE f.enlace_compartido = %s", (enlace,))
    foto = cursor.fetchone()
    cursor.close()
    conexion.close()
    if not foto:
        return "Este enlace ya no es valido o el usuario ha dejado de compartirlo.", 404
    return render_template('compartido.html', foto=foto)

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)