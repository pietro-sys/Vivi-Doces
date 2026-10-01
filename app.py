from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

# Função auxiliar para conectar no banco e facilitar a leitura das colunas
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Rota 1: O Portfólio B2B (Página principal para as empresas visualizarem)
@app.route('/')
def index():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos)

# Rota 2: Painel Administrativo (Controle interno para gerenciar clientes e vendas)
@app.route('/admin')
def admin():
    conn = get_db_connection()
    clientes = conn.execute('SELECT * FROM clientes').fetchall()
    vendas = conn.execute('SELECT * FROM vendas').fetchall()
    conn.close()
    return render_template('admin.html', clientes=clientes, vendas=vendas)

if __name__ == '__main__':
    app.run(debug=True)