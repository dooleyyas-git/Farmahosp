import sqlite3
# Módulo nativo do Python para trabalhar com banco de dados SQLite

conn = sqlite3.connect('farmacia.db')
# Cria o arquivo farmacia.db na pasta do projeto (o banco de dados)

cursor = conn.cursor()
# Cursor é o objeto que envia comandos SQL ao banco

cursor.execute('''
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf VARCHAR(14) UNIQUE NOT NULL,
        senha VARCHAR(255) NOT NULL
    )
''')
# Cria a tabela de funcionários se ela ainda não existir
# AUTOINCREMENT: o id é gerado automaticamente
# UNIQUE: dois funcionários não podem ter o mesmo CPF

cursor.execute('''
    CREATE TABLE IF NOT EXISTS medicamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome VARCHAR(255) NOT NULL,
        quantidade_atual INTEGER NOT NULL DEFAULT 0
    )
''')
# Cria a tabela de medicamentos
# DEFAULT 0: a quantidade começa em zero se não for informada

cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_medicamento INTEGER NOT NULL,
        tipo VARCHAR(10) NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_medicamento) REFERENCES medicamentos(id)
    )
''')
# Cria a tabela de movimentações (histórico de entradas e saídas)
# CURRENT_TIMESTAMP: salva a data e hora automaticamente
# FOREIGN KEY: garante que id_medicamento sempre existe na tabela medicamentos

cursor.execute('''
    INSERT OR IGNORE INTO funcionarios (cpf, senha)
    VALUES ('123.456.789-99', 'Testezao123!')
''')
# Insere o usuário admin para teste
# OR IGNORE: caso o CPF já exista ignora ao inves de gerar um erro

conn.commit()
# Confirma e salva todas as operações no banco

conn.close()
# Fecha a conexão com o banco

print("Banco de dados criado com sucesso!")
print("CPF de teste: 123.456.789-99")
print("Senha de teste: Teste123!")
