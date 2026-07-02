import os
import atexit
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse as urlparse
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'farmacia_hospitalar_chave_secreta'

def conectar():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("A variável de ambiente DATABASE_URL não foi configurada!")
    return psycopg2.connect(database_url)

def inicializar_banco():
    """Cria a estrutura do banco e insere dados de forma segura sem travar o app"""
    sql_tabelas = """
    CREATE TABLE IF NOT EXISTS PESSOAS (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(150) NOT NULL,
        cpf VARCHAR(11) UNIQUE NOT NULL,
        senha VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS FUNCIONARIOS (
        pessoa_id INTEGER PRIMARY KEY REFERENCES PESSOAS(id) ON DELETE CASCADE,
        senha VARCHAR(100) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS MEDICAMENTOS (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        descricao TEXT,
        dosagem VARCHAR(50),
        unidade VARCHAR(20),
        quantidade_caixa INTEGER,
        tipo VARCHAR(50),
        quantidade_atual INTEGER DEFAULT 0,
        alta_prioridade INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS LABORATORIOS (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(150) NOT NULL,
        descricao TEXT
    );

    CREATE TABLE IF NOT EXISTS MEDICAMENTO_LABORATORIO (
        id_medicamento INTEGER NOT NULL REFERENCES MEDICAMENTOS(id) ON DELETE CASCADE,
        id_laboratorio INTEGER NOT NULL REFERENCES LABORATORIOS(id) ON DELETE CASCADE,
        PRIMARY KEY (id_medicamento, id_laboratorio)
    );

    CREATE TABLE IF NOT EXISTS PACIENTES (
        pessoa_id INTEGER PRIMARY KEY REFERENCES PACIENTES(pessoa_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS MEDICOS (
        pessoa_id INTEGER PRIMARY KEY REFERENCES PESSOAS(id) ON DELETE CASCADE,
        crm VARCHAR(50) UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ENFERMEIROS (
        pessoa_id INTEGER PRIMARY KEY REFERENCES PESSOAS(id) ON DELETE CASCADE,
        coren VARCHAR(50) UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS RECEITAS (
        id SERIAL PRIMARY KEY,
        paciente_id INTEGER NOT NULL REFERENCES PACIENTES(pessoa_id),
        medico_id INTEGER NOT NULL REFERENCES MEDICOS(pessoa_id),
        data_emissao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ITENS_RECEITA (
        receita_id INTEGER NOT NULL REFERENCES RECEITAS(id) ON DELETE CASCADE,
        medicamento_id INTEGER NOT NULL REFERENCES MEDICAMENTOS(id),
        quantidade INTEGER NOT NULL,
        PRIMARY KEY (receita_id, medicamento_id)
    );

    CREATE TABLE IF NOT EXISTS UTENSILIOS (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        descricao TEXT,
        quantidade_atual INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS MOVIMENTACOES_MEDICAMENTOS (
        id SERIAL PRIMARY KEY,
        id_medicamento INTEGER NOT NULL REFERENCES MEDICAMENTOS(id) ON DELETE CASCADE,
        tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('entrada', 'saida')),
        quantidade INTEGER NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS MOVIMENTACOES_UTENSILIOS (
        id SERIAL PRIMARY KEY,
        id_utensilio INTEGER NOT NULL REFERENCES UTENSILIOS(id) ON DELETE CASCADE,
        tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('entrada', 'saida')),
        quantidade INTEGER NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS HISTORICO (
        id SERIAL PRIMARY KEY,
        id_medicamento INTEGER NOT NULL REFERENCES MEDICAMENTOS(id) ON DELETE CASCADE,
        tipo VARCHAR(10) NOT NULL,
        quantidade INTEGER NOT NULL,
        data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Passo 1: Criação das Tabelas e Registos Iniciais Base
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        cursor.execute(sql_tabelas)
        
        # Garante as colunas novas de forma individual e sem travar
        cursor.execute("ALTER TABLE MEDICAMENTOS ADD COLUMN IF NOT EXISTS data_validade DATE;")
        cursor.execute("ALTER TABLE MEDICAMENTOS ADD COLUMN IF NOT EXISTS descricao TEXT;")
        
        # Verifica Usuário João
        cursor.execute("SELECT id FROM PESSOAS WHERE cpf = '12345678999'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO PESSOAS (id, nome, cpf, senha) VALUES (1, 'Joao', '12345678999', 'Teste123!')")
            cursor.execute("INSERT INTO FUNCIONARIOS (pessoa_id, senha) VALUES (1, 'Teste123!')")
            cursor.execute("SELECT setval('pessoas_id_seq', (SELECT MAX(id) FROM PESSOAS))")
            
        # Verifica Medicamento de Teste de forma isolada
        cursor.execute("SELECT id FROM MEDICAMENTOS WHERE id = 3")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO MEDICAMENTOS (id, nome, quantidade_atual, alta_prioridade) VALUES (3, 'Maltodextrina', 0, 0)")
            cursor.execute("SELECT setval('medicamentos_id_seq', (SELECT MAX(id) FROM MEDICAMENTOS))")
            
        conn.commit()
        cursor.close()
        conn.close()
        print("Banco de dados base configurado com sucesso!")
    except Exception as e:
        print(f"Erro ao inicializar tabelas base: {e}")

    # Passo 2: Injeção Isolada da coluna 'ativo' nos Medicamentos (Soft Delete)
    try:
        conn_iso = conectar()
        cursor_iso = conn_iso.cursor()
        cursor_iso.execute("ALTER TABLE MEDICAMENTOS ADD COLUMN ativo INTEGER DEFAULT 1;")
        conn_iso.commit()
        cursor_iso.close()
        conn_iso.close()
    except Exception:
        pass # Ignora se a coluna já existir

    # Passo 3: Injeção Isolada da coluna 'ativo' nos Utensílios
    try:
        conn_iso = conectar()
        cursor_iso = conn_iso.cursor()
        cursor_iso.execute("ALTER TABLE UTENSILIOS ADD COLUMN ativo INTEGER DEFAULT 1;")
        conn_iso.commit()
        cursor_iso.close()
        conn_iso.close()
    except Exception:
        pass

def salvar_historico_fechamento():
    print("Gerando relatório de movimentações...")
    if not os.path.exists('relatorios'):
        os.makedirs('relatorios')
        
    try:
        conn = conectar()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
            SELECT m.nome, h.tipo, h.quantidade, h.data_hora 
            FROM HISTORICO h
            JOIN MEDICAMENTOS m ON h.id_medicamento = m.id
            ORDER BY h.data_hora DESC
        ''')
        movimentacoes = cursor.fetchall()
        conn.close()
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        caminho_arquivo = f"relatorios/historico_{timestamp}.txt"
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write("=== RELATÓRIO DE MOVIMENTAÇÕES DE ESTOQUE ===\n")
            f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")
            
            if not movimentacoes:
                f.write("Nenhuma movimentação registrada até o momento.\n")
            else:
                for mov in movimentacoes:
                    linha = f"[{mov['data_hora']}] Medicamento: {mov['nome']} | Tipo: {mov['tipo'].upper()} | Qtd: {mov['quantidade']}\n"
                    f.write(linha)
                    
        print(f"Histórico saved to: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")

atexit.register(salvar_historico_fechamento)

@app.route('/')
def index():
    return render_template('index.html', erro=None)

@app.route('/login', methods=['POST'])
def login():
    cpf_formatado = request.form['cpf']
    senha = request.form['senha']
    
    cpf_limpo = cpf_formatado.replace('.', '').replace('-', '')
    
    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('''
        SELECT p.id, p.nome, p.cpf 
        FROM PESSOAS p 
        JOIN FUNCIONARIOS f ON f.pessoa_id = p.id 
        WHERE p.cpf = %s AND f.senha = %s
    ''', (cpf_limpo, senha))

    funcionario = cursor.fetchone()
    conn.close()

    if not funcionario:
        return render_template('index.html', erro='CPF ou senha inválidos.')

    session['funcionario_id'] = funcionario['id']
    session['funcionario_cpf'] = funcionario['cpf']

    return redirect(url_for('estoque'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/estoque', methods=['GET', 'POST'])
def estoque():
    if 'funcionario_id' not in session:
        return redirect(url_for('index'))

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Se for um cadastro de utensílio (POST)
    if request.method == 'POST' and 'nome_utensilio' in request.form:
        nome_utensilio = request.form['nome_utensilio']
        quantidade_utensilio = int(request.form['quantidade_utensilio'])
        
        try:
            cursor.execute(
                'INSERT INTO UTENSILIOS (nome, quantidade_atual) VALUES (%s, %s)',
                (nome_utensilio, quantidade_utensilio)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Erro ao cadastrar utensílio: {e}")

    # --- BUSCA DOS DADOS PARA AS ABAS ---

    # 1. Busca APENAS os medicamentos ativos
    cursor.execute('SELECT * FROM MEDICAMENTOS WHERE ativo = 1 ORDER BY nome ASC')
    medicamentos = cursor.fetchall()

    # 2. Busca os utensílios ativos (caso aplique soft delete neles futuramente, adicione 'WHERE ativo = 1')
    cursor.execute('SELECT * FROM UTENSILIOS ORDER BY nome ASC')
    utensilios = cursor.fetchall()

    # 3. Busca o histórico de movimentações recente
    cursor.execute("""
        SELECT m.data_hora, med.nome AS medicamento_nome, m.tipo, m.quantidade 
        FROM MOVIMENTACOES_MEDICAMENTOS m
        JOIN MEDICAMENTOS med ON m.id_medicamento = med.id
        ORDER BY m.data_hora DESC 
        LIMIT 50
    """)
    historico = cursor.fetchall()

    # 4. Sistema de Alertas de estoque baixo/validade vencendo
    alerta = []
    for med in medicamentos:
        if med['alta_prioridade'] == 1 and med['quantidade_atual'] < 5:
            alerta.append(f"Alerta: O medicamento de alta prioridade '{med['nome']}' está com estoque crítico ({med['quantidade_atual']} un).")

    cursor.close()
    conn.close()

    return render_template(
        'estoque.html',
        medicamentos=medicamentos,
        utensilios=utensilios,
        historico=historico,
        alerta=alerta
    )
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    if 'funcionario_id' not in session:
        return redirect(url_for('index'))
        
    nome = request.form.get('nome')
    tipo_med = request.form.get('tipo_medicamento')  
    dosagem = request.form.get('dosagem')         
    quantidade = int(request.form.get('quantidade'))
    descricao = request.form.get('descricao')  
    data_validade = request.form.get('data_validade') 
    alta_prioridade = request.form.get('alta_prioridade', 0)
    
    alta_prioridade = 1 if alta_prioridade == '1' else 0

    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Insere o medicamento e retorna o ID
    cursor.execute("""
        INSERT INTO MEDICAMENTOS (nome, tipo, dosagem, descricao, quantidade_atual, alta_prioridade, data_validade) 
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
    """, (nome, tipo_med, dosagem, descricao, quantidade, alta_prioridade, data_validade if data_validade else None))
    
    novo_id = cursor.fetchone()[0]
    
    # 2. Registra na tabela oficial de movimentações
    cursor.execute("""
        INSERT INTO MOVIMENTACOES_MEDICAMENTOS (id_medicamento, tipo, quantidade)
        VALUES (%s, 'entrada', %s);
    """, (novo_id, quantidade))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('estoque'))
@app.route('/excluir/<int:id_medicamento>', methods=['POST'])
@app.route('/entrada_rapida', methods=['POST'])
def entrada_rapida():#nova função de entrada separada para não entrar em conflico com a função de carrinho
    if 'funcionario_id' not in session:
        return redirect(url_for('index'))

    id_item = int(request.form['id'])
    quantidade = int(request.form['quantidade'])
    tipo_item = request.form['tipo_item'] # 'medicamento' ou 'utensilio'

    if quantidade <= 0:
        return redirect(url_for('estoque'))

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        if tipo_item == 'medicamento':
            # Busca a quantidade atual
            cursor.execute('SELECT quantidade_atual FROM MEDICAMENTOS WHERE id = %s', (id_item,))
            med = cursor.fetchone()
            if med:
                nova_qtd = med['quantidade_atual'] + quantidade
                cursor.execute('UPDATE MEDICAMENTOS SET quantidade_atual = %s WHERE id = %s', (nova_qtd, id_item))
                cursor.execute('INSERT INTO MOVIMENTACOES_MEDICAMENTOS (id_medicamento, tipo, quantidade) VALUES (%s, \'entrada\', %s)', (id_item, quantidade))
        
        elif tipo_item == 'utensilio':
            # Busca a quantidade atual
            cursor.execute('SELECT quantidade_atual FROM UTENSILIOS WHERE id = %s', (id_item,))
            ut = cursor.fetchone()
            if ut:
                nova_qtd = ut['quantidade_atual'] + quantidade
                cursor.execute('UPDATE UTENSILIOS SET quantidade_atual = %s WHERE id = %s', (nova_qtd, id_item))
                cursor.execute('INSERT INTO MOVIMENTACOES_UTENSILIOS (id_utensilio, tipo, quantidade) VALUES (%s, \'entrada\', %s)', (id_item, quantidade))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Erro na entrada rápida: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('estoque'))
def excluir(id_medicamento):
    if 'funcionario_id' not in session:
        return redirect(url_for('index'))

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('DELETE FROM MEDICAMENTOS WHERE id = %s', (id_medicamento,))

    conn.commit()
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/movimentar', methods=['POST'])
def movimentar():
    if 'funcionario_id' not in session:
        return redirect(url_for('index'))

    # Recebe os dados do carrinho enviados via JSON
    dados = request.get_json()
    if not dados or 'itens' not in dados:
        return {"sucesso": False, "erro": "Nenhum dado enviado"}, 400

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Loop para processar cada item adicionado no carrinho
        for item in dados['itens']:
            id_item = int(item['id'])
            quantidade = int(item['quantidade'])
            tipo_item = item['tipo_item'] # 'medicamento' ou 'utensilio'

            if quantidade <= 0:
                continue

            if tipo_item == 'medicamento':
                # Verifica estoque do medicamento
                cursor.execute('SELECT quantidade_atual, nome FROM MEDICAMENTOS WHERE id = %s', (id_item,))
                med = cursor.fetchone()
                if not med or med['quantidade_atual'] < quantidade:
                    conn.rollback()
                    return {"sucesso": False, "erro": f"Estoque insuficiente para {med['nome'] if med else 'Medicamento'}"}, 400
                
                # Atualiza estoque e insere na tabela de movimentação correta
                nova_qtd = med['quantidade_atual'] - quantidade
                cursor.execute('UPDATE MEDICAMENTOS SET quantidade_atual = %s WHERE id = %s', (nova_qtd, id_item))
                cursor.execute('INSERT INTO MOVIMENTACOES_MEDICAMENTOS (id_medicamento, tipo, quantidade) VALUES (%s, \'saida\', %s)', (id_item, quantidade))
            
            elif tipo_item == 'utensilio':
                # Verifica estoque do utensílio
                cursor.execute('SELECT quantidade_atual, nome FROM UTENSILIOS WHERE id = %s', (id_item,))
                ut = cursor.fetchone()
                if not ut or ut['quantidade_atual'] < quantidade:
                    conn.rollback()
                    return {"sucesso": False, "erro": f"Estoque insuficiente para {ut['nome'] if ut else 'Utensílio'}"}, 400
                
                # Atualiza estoque e insere na tabela de movimentação de utensílios
                nova_qtd = ut['quantidade_atual'] - quantidade
                cursor.execute('UPDATE UTENSILIOS SET quantidade_atual = %s WHERE id = %s', (nova_qtd, id_item))
                cursor.execute('INSERT INTO MOVIMENTACOES_UTENSILIOS (id_utensilio, tipo, quantidade) VALUES (%s, \'saida\', %s)', (id_item, quantidade))

        conn.commit()
        return {"sucesso": True}
    except Exception as e:
        conn.rollback()
        return {"sucesso": False, "erro": str(e)}, 500
    finally:
        cursor.close()
        conn.close()
#para fechar o flask
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)