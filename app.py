import os
import atexit
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse as urlparse
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

# Flask          → cria a aplicação web
# render_template → carrega arquivos HTML da pasta templates/
# request        → lê dados enviados pelos formulários
# redirect       → redireciona o usuário para outra página
# url_for        → gera a URL de uma rota pelo nome da função
# session        → guarda dados do usuário entre uma página e outra

app = Flask(__name__)
app.secret_key = 'farmacia_hospitalar_chave_secreta'

# secret_key é obrigatória para o Flask usar sessões com segurança

def conectar():
    # Função auxiliar para abrir a conexão com o banco PostgreSQL no Render
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        raise ValueError("A variável de ambiente DATABASE_URL não foi configurada!")

    url = urlparse.urlparse(database_url)
    dbname = url.path[1:]
    user = url.username
    password = url.password
    host = url.hostname
    port = url.port

    return psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )

def salvar_historico_fechamento():
    print("Gerando relatório de movimentações...")
    
    # Cria a pasta 'relatorios' se ela não existir
    if not os.path.exists('relatorios'):
        os.makedirs('relatorios')
        
    try:
        # Conecta ao banco PostgreSQL utilizando a função global ajustada
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
        
        # Define o nome do arquivo com a data e hora atual
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        caminho_arquivo = f"relatorios/historico_{timestamp}.txt"
        
        # Escreve os dados no arquivo de texto
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
                    
        print(f"Histórico salvo com sucesso em: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")

# Registra a função para rodar automaticamente quando o app for encerrado
atexit.register(salvar_historico_fechamento)

@app.route('/')
def index():
    # Rota da página inicial (tela de login)
    return render_template('index.html', erro=None)

@app.route('/login', methods=['POST'])
def login():
    # Rota que recebe e valida os dados do formulário de login
    cpf_formatado = request.form['cpf']
    senha = request.form['senha']
    
    # Remove os pontos e o traço para buscar no banco apenas os números
    cpf_limpo = cpf_formatado.replace('.', '').replace('-', '')
    print(f"DEBUG - CPF digitado (limpo): {cpf_limpo}")
    print(f"DEBUG - Senha digitada: {senha}")
    
    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Busca usando o CPF limpo (Trocado ? por %s)
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
    # Apaga todos os dados da sessão (desloga o usuário)
    session.clear()
    return redirect(url_for('index'))

@app.route('/estoque')
def estoque():
    if 'funcionario_id' not in session:
        # Bloqueia o acesso se o usuário não estiver logado
        return redirect(url_for('index'))

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute('SELECT * FROM MEDICAMENTOS ORDER BY nome ASC')
    medicamentos = cursor.fetchall()

    medicamentos_criticos = ['Paracetamol', 'Dipirona', 'Amoxicilina']
    ESTOQUE_MINIMO = 5
    alerta = []

    for med in medicamentos:
        if med['nome'] in medicamentos_criticos and med['quantidade_atual'] < ESTOQUE_MINIMO:
            alerta.append(f"⚠️ O medicamento '{med['nome']}' está abaixo do estoque mínimo ({ESTOQUE_MINIMO}). Comprar imediatamente!")

    conn.close()

    return render_template('estoque.html', medicamentos=medicamentos, alerta=alerta)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    if 'funcionario_id' not in session:
        return redirect(url_for('index'))

    nome = request.form['nome']
    quantidade = int(request.form['quantidade'])
    
    # Lê o checkbox do HTML. Se estiver marcado, salva 1, se não, salva 0
    alta_prioridade = 1 if 'alta_prioridade' in request.form else 0

    if not nome or quantidade < 0:
        return redirect(url_for('estoque'))

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Trocado ? por %s
    cursor.execute(
        'INSERT INTO MEDICAMENTOS (nome, quantidade_atual, alta_prioridade) VALUES (%s, %s, %s)',
        (nome, quantidade, alta_prioridade)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('estoque'))

@app.route('/excluir/<int:id_medicamento>', methods=['POST'])
def excluir(id_medicamento):
    if 'funcionario_id' not in session:
        return redirect(url_for('index'))

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Trocado ? por %s
    cursor.execute('DELETE FROM MEDICAMENTOS WHERE id = %s', (id_medicamento,))

    conn.commit()
    conn.close()

    return redirect(url_for('estoque'))

@app.route('/movimentar', methods=['POST'])
def movimentar():
    if 'funcionario_id' not in session:
        return redirect(url_for('index'))

    id_medicamento = int(request.form['id_medicamento'])
    tipo = request.form['tipo']
    quantidade = int(request.form['quantidade'])

    if quantidade <= 0:
        return redirect(url_for('estoque'))

    conn = conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Trocado ? por %s
    cursor.execute(
        'SELECT quantidade_atual FROM MEDICAMENTOS WHERE id = %s',
        (id_medicamento,)
    )

    medicamento = cursor.fetchone()

    if not medicamento:
        conn.close()
        return redirect(url_for('estoque'))

    if tipo == 'saida' and medicamento['quantidade_atual'] < quantidade:
        conn.close()
        return redirect(url_for('estoque'))

    nova_quantidade = medicamento['quantidade_atual'] + quantidade

    if tipo == 'saida':
        nova_quantidade = medicamento['quantidade_atual'] - quantidade

    # Trocado ? por %s
    cursor.execute(
        'UPDATE MEDICAMENTOS SET quantidade_atual = %s WHERE id = %s',
        (nova_quantidade, id_medicamento)
    )

    # Trocado ? por %s
    cursor.execute(
        'INSERT INTO MOVIMENTACOES_MEDICAMENTOS (id_medicamento, tipo, quantidade) VALUES (%s, %s, %s)',
        (id_medicamento, tipo, quantidade)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('estoque'))

if __name__ == '__main__':
    # O Render configura dinamicamente a porta necessária do ambiente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)