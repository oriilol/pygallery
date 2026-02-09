from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# CLAVE SECRETA. Por si acaso.
app.secret_key = 'JuanLimonApruebanos'

CONFIG_BD = {
    'host': 'localhost',
    'user': 'pyuser',      
    'password': '1234',    
    'database': 'pygallery_db'
}

CARPETA_IMAGENES = os.path.join('static', 'imagenes')
app.config['UPLOAD_FOLDER'] = CARPETA_IMAGENES
EXTENSIONES_VALIDAS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(CARPETA_IMAGENES, exist_ok=True)

def conectar_bd():
    return mysql.connector.connect(**CONFIG_BD)

def archivo_permitido(nombre_archivo):
    return '.' in nombre_archivo and nombre_archivo.rsplit('.', 1)[1].lower() in EXTENSIONES_VALIDAS

# RUTAS DEL LOGIN.

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        clave = request.form['password']
        
        conexion = conectar_bd()
        cursor = conexion.cursor(dictionary=True)
        
        # BUSCAR USUARIO EN LA BASE DE DATOS.
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (usuario, clave))
        user_encontrado = cursor.fetchone()
        
        cursor.close()
        conexion.close()
        
        if user_encontrado:
            session['usuario_id'] = user_encontrado['id']
            session['usuario_nombre'] = user_encontrado['username']
            return redirect(url_for('inicio'))
        else:
            return "Usuario o contraseña incorrectos <a href='/login'>Intentar de nuevo</a>"
            
    return render_template('login.html')

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
            
            return "Usuario creado correctamente. <a href='/login'>Inicia Sesión aquí</a>"
        
        except mysql.connector.Error as err:
            return f"Error: Seguramente ese nombre ya existe. <a href='/registro'>Prueba otro</a>"

    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))


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
        return f"Error: {e}"

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

        if archivo and archivo_permitido(archivo.filename):
            nombre_seguro = secure_filename(archivo.filename)
            ruta_destino = os.path.join(app.config['UPLOAD_FOLDER'], nombre_seguro)
            archivo.save(ruta_destino)

            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                
                id_usuario_actual = session['usuario_id']
                
                sql = "INSERT INTO fotos (nombre_archivo, titulo, fecha, usuario_id) VALUES (%s, %s, NOW(), %s)"
                valores = (nombre_seguro, titulo, id_usuario_actual)
                
                cursor.execute(sql, valores)
                conexion.commit()
                
                cursor.close()
                conexion.close()
                
                return redirect(url_for('inicio'))
            
            except mysql.connector.Error as err:
                return f"Error guardando en la base de datos: {err}"

    return render_template('subir.html')

@app.route('/borrar/<int:foto_id>')
def borrar_foto(foto_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    try:
        conexion = conectar_bd()
        cursor_dict = conexion.cursor(dictionary=True)
        cursor = conexion.cursor()

        cursor_dict.execute("SELECT nombre_archivo FROM fotos WHERE id = %s", (foto_id,))
        foto = cursor_dict.fetchone()

        if foto:
            nombre_archivo = foto['nombre_archivo']
            ruta_completa = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)

            if os.path.exists(ruta_completa):
                os.remove(ruta_completa)
                print(f"Archivo {nombre_archivo} eliminado del disco.")

            cursor.execute("DELETE FROM fotos WHERE id = %s", (foto_id,))
            conexion.commit()
            print(f"Registro ID {foto_id} eliminado de la BD.")

        cursor_dict.close()
        cursor.close()
        conexion.close()
        
        return redirect(url_for('inicio'))

    except Exception as e:
        return f"Error al intentar borrar: {e}"

if __name__ == '__main__':
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    certificado = os.path.join(directorio_actual, 'cert.pem')
    llave = os.path.join(directorio_actual, 'key.pem')
app.run(host='0.0.0.0', port=5000, ssl_context=(certificado, llave), debug=True)