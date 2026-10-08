from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

# Função para garantir que a base de dados é recriada com a estrutura mais recente
def init_db():
    if os.path.exists('database.sql'):
        conn = sqlite3.connect('database.db')
        # Apaga as tabelas antigas para garantir que entram com a nova estrutura e colunas
        conn.executescript("""
            DROP TABLE IF EXISTS vendas;
            DROP TABLE IF EXISTS produtos;
            DROP TABLE IF EXISTS clientes;
        """)
        # Lê e executa o script atualizado do database.sql
        with open('database.sql', 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

# Executa a inicialização ao iniciar a aplicação
init_db()

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

# Rota 2: Painel Administrativo (Controle interno)
@app.route('/admin')
def admin():
    conn = get_db_connection()
    clientes = conn.execute('SELECT * FROM clientes').fetchall()
    vendas = conn.execute('SELECT * FROM vendas').fetchall()
    conn.close()
    return render_template('admin.html', clientes=clientes, vendas=vendas)

if __name__ == '__main__':
    app.run(debug=True)