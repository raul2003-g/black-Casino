from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import verify_user, add_user
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['balance'] = user['balance']
            return redirect(url_for('index'))
        
        flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
        elif len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
        else:
            if add_user(username, email, password):
                flash('Cuenta creada exitosamente. Por favor inicia sesión.', 'success')
                return redirect(url_for('auth.login'))
            flash('El nombre de usuario o email ya están en uso', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))