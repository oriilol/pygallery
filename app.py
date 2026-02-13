from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import os
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

# EXTENSIONES PERMITIDAS.
EXTENSIONES_FOTO = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
EXTENSIONES_VIDEO = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
EXTENSIONES_VALIDAS = EXTENSIONES_FOTO.union(EXTENSIONES_VIDEO)


def conectar_bd():
    return mysql.connector.connect(**CONFIG_BD)

def archivo_permitido(nombre_archivo):
    return '.' in nombre_archivo and \
           nombre_archivo.rsplit('.', 1)[1].lower() in EXTENSIONES_VALIDAS

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
        else:
            return jsonify({'status': 'error', 'message': 'Credenciales incorrectas'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/')
def inicio():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        
        id_actual = session['usuario_id']
        sql = "SELECT * FROM fotos WHERE usuario_id = %s ORDER BY fecha DESC"
        cursor.execute(sql, (id_actual,))
        lista_fotos = cursor.fetchall()
        
        cursor.close()
        conexion.close()
        return render_template('index.html', fotos=lista_fotos)
    except Exception as e:
        return f"Error de conexión: {e}"

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nuevo_usuario = request.form['username']
        nueva_clave = request.form['password']
        
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            sql = "INSERT INTO usuarios (username, password) VALUES (%s, %s)"
            cursor.execute(sql, (nuevo_usuario, nueva_clave))
            conexion.commit()
            cursor.close()
            conexion.close()
            flash("Cuenta creada. Por favor inicia sesión.")
            return redirect(url_for('login'))
        except mysql.connector.Error:
            flash("Error: Ese usuario ya existe.")

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
            flash("Usuario o contraseña incorrectos")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

@app.route('/subir', methods=['GET', 'POST'])
def subir_foto():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'archivo' not in request.files:
            return 'No hay archivo', 400
        
        archivo = request.files['archivo']
        titulo = request.form.get('titulo', 'Sin titulo')

        if archivo.filename == '':
            return 'No seleccionaste nada', 400

        if not archivo_permitido(archivo.filename):
            flash("TIPO DE ARCHIVO NO PERMITIDO. Solo sube imágenes o vídeos.")
            return redirect(request.url)

        if archivo:
            nombre_seguro = secure_filename(archivo.filename)
            ruta_destino = os.path.join(app.config['UPLOAD_FOLDER'], nombre_seguro)
            archivo.save(ruta_destino)

            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                id_actual = session['usuario_id']
                
                sql = "INSERT INTO fotos (nombre_archivo, titulo, fecha, usuario_id) VALUES (%s, %s, NOW(), %s)"
                cursor.execute(sql, (nombre_seguro, titulo, id_actual))
                
                conexion.commit()
                cursor.close()
                conexion.close()
                return redirect(url_for('inicio'))
            except Exception as e:
                return f"Error guardando: {e}"

    return render_template('subir.html')

@app.route('/borrar/<int:foto_id>')
def borrar_foto(foto_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    try:
        conexion = conectar_bd()
        cursor_dict = conexion.cursor(dictionary=True)
        cursor = conexion.cursor()

        usuario_actual = session['usuario_id']
        cursor_dict.execute("SELECT nombre_archivo FROM fotos WHERE id = %s AND usuario_id = %s", (foto_id, usuario_actual))
        foto = cursor_dict.fetchone()

        if foto:
            nombre_archivo = foto['nombre_archivo']
            ruta_completa = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)

            if os.path.exists(ruta_completa):
                os.remove(ruta_completa)
            
            cursor.execute("DELETE FROM fotos WHERE id = %s", (foto_id,))
            conexion.commit()
        else:
            flash("No puedes borrar esta foto (o no existe).")

        cursor_dict.close()
        cursor.close()
        conexion.close()
        return redirect(url_for('inicio'))

    except Exception as e:
        return f"Error al borrar: {e}"

if __name__ == '__main__':
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    certificado = os.path.join(directorio_actual, 'cert.pem')
    llave = os.path.join(directorio_actual, 'key.pem')

app.run(host='192.168.1.39', port=5000, ssl_context=(certificado, llave), debug=True, threaded=True)