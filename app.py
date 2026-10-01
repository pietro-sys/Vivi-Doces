import sqlite3

with open('database.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

conexao = sqlite3.connect('database.sql')

conexao.executescript(sql_script)

conexao.commit()
conexao.close()

print('Banco de dados criado com sucesso')