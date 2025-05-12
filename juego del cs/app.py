import re
import os
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, request, flash, make_response, jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from auth import auth_bp
import database
from dotenv import load_dotenv
from functools import wraps

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación   
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('EMAIL_USER'),
    MAIL_PASSWORD=os.getenv('EMAIL_PASS'),
    MAIL_DEFAULT_SENDER=os.getenv('EMAIL_USER'),
    MAX_BET=5000,
    MIN_BET=10,
    RETIRO_MAXIMO_DIARIO=50000
)

# Extensiones permitidas para archivos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
JUEGOS_PERMITIDOS = [
    'Blackjack.html',
    'Bingo.html',
    'tragamonedas.html',
    'Sweet.html',
    'Gana.html',
    "ayuda.html"	
]

# Inicializar extensiones
mail = Mail(app)
database.init_db()
app.register_blueprint(auth_bp)

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Rutas principales
@app.route('/')
def index():
    user_data = None
    if 'user_id' in session:
        balance = database.get_user_balance(session['user_id']) or 0
        user_data = {
            'username': session['username'],
            'balance': balance
        }
    return render_template('index.html', user=user_data)

# Sistema de Juegos
@app.route('/juegos/<nombre_juego>')
@login_required
def servir_juego(nombre_juego):
    if nombre_juego not in JUEGOS_PERMITIDOS:
        return "Juego no encontrado", 404
    
    balance = database.get_user_balance(session['user_id']) or 0
    ruta_juego = os.path.join('templates', 'juegos', nombre_juego)
    
    try:
        with open(ruta_juego, 'r', encoding='utf-8') as file:
            contenido = file.read().replace('{{ user_balance }}', str(balance))
        return make_response(contenido)
    except FileNotFoundError:
        return "Juego no disponible", 404

# API de Saldo
@app.route('/get_balance')
@login_required
def get_balance():
    balance = database.get_user_balance(session['user_id']) or 0
    return jsonify({'balance': balance})

@app.route('/actualizar_saldo', methods=['POST'])
@login_required
def actualizar_saldo():
    try:
        data = request.get_json()
        cambio = float(data.get('cambio', 0))
        user_id = session['user_id']
        
        saldo_actual = database.get_user_balance(user_id) or 0
        nuevo_saldo = saldo_actual + cambio
        
        if nuevo_saldo < 0:
            return jsonify({'error': 'Saldo insuficiente'}), 400
            
        if database.set_user_balance(user_id, nuevo_saldo):
            return jsonify({
                'success': True,
                'nuevo_saldo': nuevo_saldo
            })
        return jsonify({'error': 'Error en la base de datos'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Sistema de Recargas
@app.route('/enviar_comprobante', methods=['POST'])
@login_required
def enviar_comprobante():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cantidad = request.form.get('cantidad', '').strip()
    file = request.files.get('comprobante')

    # Validaciones
    if not cantidad.isdigit() or int(cantidad) <= 0:
        flash('Cantidad inválida', 'error')
        return redirect(url_for('index'))

    if not file or not allowed_file(file.filename):
        flash('Archivo inválido', 'error')
        return redirect(url_for('index'))

    try:
        # Procesar archivo
        filename = secure_filename(file.filename)
        file_data = file.read()

        # Enviar correo
        msg = Message(
            subject=f"Recarga de {cantidad} fichas - {session['username']}",
            recipients=[os.getenv('EMAIL_COMPROBANTE')],
            body=f"Usuario: {session['username']}\nCantidad: {cantidad} fichas"
        )
        msg.attach(filename, file.content_type, file_data)
        mail.send(msg)

        # Actualizar saldo
        if database.update_balance(session['user_id'], int(cantidad)):
            flash('Recarga procesada correctamente', 'success')
        else:
            flash('Error al actualizar saldo', 'warning')

    except Exception as e:
        app.logger.error(f"Error en recarga: {str(e)}")
        flash('Error al procesar la recarga', 'error')

    return redirect(url_for('index'))

# Sistema de Retiros
@app.route('/solicitar_retiro', methods=['POST'])
@login_required
def solicitar_retiro():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cbu = request.form.get('cbu', '').strip()
    cantidad = request.form.get('cantidad', '').strip()

    # Validaciones
    if not re.match(r'^\d{22}$', cbu):
        flash('CBU debe contener 22 dígitos', 'error')
        return redirect(url_for('index'))

    try:
        cantidad = float(cantidad)
        if cantidad <= 0:
            flash('Monto inválido', 'error')
            return redirect(url_for('index'))

        if cantidad > app.config['RETIRO_MAXIMO_DIARIO']:
            flash(f'Límite diario: ${app.config["RETIRO_MAXIMO_DIARIO"]}', 'error')
            return redirect(url_for('index'))

        balance_actual = database.get_user_balance(session['user_id']) or 0
        if cantidad > balance_actual:
            flash('Saldo insuficiente', 'error')
            return redirect(url_for('index'))

        # Procesar retiro
        nuevo_saldo = balance_actual - cantidad
        if not database.set_user_balance(session['user_id'], nuevo_saldo):
            flash('Error al procesar retiro', 'error')
            return redirect(url_for('index'))

        # Notificar por correo
        try:
            msg = Message(
                subject=f"Retiro de {cantidad} fichas - {session['username']}",
                recipients=[os.getenv('EMAIL_RETIRO')],
                body=f"""
                Usuario: {session['username']}
                ID: {session['user_id']}
                CBU: {cbu}
                Monto: {cantidad} fichas
                Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                """
            )
            mail.send(msg)
            flash('Retiro procesado correctamente', 'success')
        except Exception as e:
            app.logger.error(f"Error al enviar correo: {str(e)}")
            flash('Retiro procesado pero error al notificar', 'warning')

    except Exception as e:
        app.logger.error(f"Error en retiro: {str(e)}")
        flash('Error al procesar el retiro', 'error')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)