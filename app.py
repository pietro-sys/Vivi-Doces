from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

def init_db():
    if os.path.exists('database.sql'):
        conn = sqlite3.connect('database.db')
        conn.executescript("""
            DROP TABLE IF EXISTS vendas;
            DROP TABLE IF EXISTS produtos;
            DROP TABLE IF EXISTS clientes;
        """)
        with open('database.sql', 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    clientes = conn.execute('SELECT * FROM clientes').fetchall()
    vendas = conn.execute('SELECT * FROM vendas').fetchall()
    conn.close()
    return render_template('admin.html', clientes=clientes, vendas=vendas)

# Rota para adicionar novo cliente corporativo
@app.route('/adicionar_cliente', methods=['POST'])
def adicionar_cliente():
    empresa = request.form['empresa']
    cnpj = request.form['cnpj']
    contato = request.form['contato']
    telefone = request.form['telefone']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO clientes (empresa, cnpj, contato, telefone) VALUES (?, ?, ?, ?)',
                 (empresa, cnpj, contato, telefone))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# Rota para registar nova venda/orçamento
@app.route('/adicionar_venda', methods=['POST'])
def adicionar_venda():
    cliente_id = request.form['cliente_id']
    valor_total = request.form['valor_total']
    status = request.form['status']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO vendas (cliente_id, valor_total, status) VALUES (?, ?, ?)',
                 (cliente_id, valor_total, status))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)