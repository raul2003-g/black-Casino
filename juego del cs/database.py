import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import session

# Configuración de la base de datos
def get_db_path():
    return os.path.join(os.path.dirname(__file__), 'instance', 'casino.db')

def init_db():
    """Inicializa la base de datos y crea tablas si no existen"""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Error al crear tablas: {e}")
        raise
    finally:
        conn.close()

# Funciones de usuario
def add_user(username, email, password):
    """Registra un nuevo usuario"""
    conn = sqlite3.connect(get_db_path())
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, generate_password_hash(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"Usuario/email ya existe: {e}")
        return False
    finally:
        conn.close()

def verify_user(username, password):
    """Verifica credenciales y devuelve datos del usuario"""
    conn = sqlite3.connect(get_db_path())
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, password_hash, balance FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()
        
        if user and check_password_hash(user[2], password):
            return {
                'id': user[0],
                'username': user[1],
                'balance': user[3]
            }
        return None
    finally:
        conn.close()

# Funciones de saldo
def get_user_balance(user_id):
    """Obtiene el saldo actual de un usuario"""
    conn = sqlite3.connect(get_db_path())
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT balance FROM users WHERE id = ?',
            (user_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        conn.close()

def update_balance(user_id, amount):
    """Suma/Resta una cantidad al saldo (para recargas/retiros)"""
    conn = sqlite3.connect(get_db_path())
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET balance = balance + ? WHERE id = ?',
            (amount, user_id)
        )
        conn.commit()
        
        # Actualiza la sesión si el usuario está logueado
        if 'user_id' in session and session['user_id'] == user_id:
            new_balance = get_user_balance(user_id)
            session['balance'] = new_balance
        
        return True
    except Exception as e:
        print(f"Error al actualizar saldo: {e}")
        return False
    finally:
        conn.close()

def set_user_balance(user_id, new_balance):
    """Establece un saldo específico (para juegos)"""
    conn = sqlite3.connect(get_db_path())
    try:
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET balance = ? WHERE id = ?',
            (new_balance, user_id)
        )
        conn.commit()
        
        # Actualiza la sesión
        if 'user_id' in session and session['user_id'] == user_id:
            session['balance'] = new_balance
        
        return True
    except Exception as e:
        print(f"Error al establecer saldo: {e}")
        return False
    finally:
        conn.close()