# Explicação do Código — Farmácia Hospitalar

## Visão Geral

O sistema é dividido em arquivos e pastas principais:

| Arquivo/Pasta | Função |
|---|---|
| `setup_banco.py` | Cria o banco de dados e as tabelas |
| `app.py` | Motor da aplicação (rotas e lógica) |
| `templates/index.html` | Tela de login |
| `templates/estoque.html` | Tela principal do sistema |
| `static/` | Contém os arquivos de estilo (`.css`) responsáveis pelo design e layout das telas |

## Arquitetura de Dados (Bônus)

Junto a esta documentação, enviamos em anexo o **Mapa de Arquitetura (Diagrama de Entidade-Relacionamento - DER) em formato PDF**. Este documento visual mapeia profissionalmente todas as entidades, atributos, chaves primárias (PK), chaves estrangeiras (FK) e as cardinalidades do banco de dados relacional, servindo como o artefato definitivo para a validação da lógica do projeto pela banca avaliadora.

---

## setup_banco.py

Script executado **uma única vez** para preparar o banco de dados.

### O que ele faz, em ordem:

**1. Cria o arquivo do banco**
```python
conn = sqlite3.connect('farmacia.db')
```
O SQLite não precisa de servidor. O banco inteiro é um único arquivo `.db` salvo na pasta do projeto.

**2. Cria as 3 tabelas**

**`funcionarios`** — armazena quem pode acessar o sistema
| Coluna | Tipo | Detalhe |
|---|---|---|
| id | INTEGER | Gerado automaticamente |
| cpf | VARCHAR | Único, não pode repetir |
| senha | VARCHAR | Obrigatória |

**`medicamentos`** — armazena o estoque
| Coluna | Tipo | Detalhe |
|---|---|---|
| id | INTEGER | Gerado automaticamente |
| nome | VARCHAR | Obrigatório |
| quantidade_atual | INTEGER | Começa em 0 por padrão |

**`movimentacoes`** — histórico de entradas e saídas
| Coluna | Tipo | Detalhe |
|---|---|---|
| id | INTEGER | Gerado automaticamente |
| id_medicamento | INTEGER | Referência à tabela medicamentos |
| tipo | VARCHAR | Só aceita "entrada" ou "saida" |
| data_hora | TIMESTAMP | Preenchida automaticamente |

**3. Insere o usuário admin de teste**
```
CPF:   000.000.000-00
Senha: admin123
```

---

## app.py

Arquivo principal da aplicação Flask. Define todas as rotas e a lógica do sistema.

### Função `conectar()`
Abre a conexão com o banco de dados. É chamada dentro de cada rota para não deixar conexões abertas desnecessariamente.
```python
conn.row_factory = sqlite3.Row
```
Essa linha permite acessar os dados pelo nome da coluna (`row['nome']`) em vez de por índice numérico (`row[0]`).

---

### Rotas

#### `GET /` → Tela de login
Simplesmente carrega o `index.html`. Passa `erro=None` para garantir que a variável sempre existe no template.

---

#### `POST /login` → Valida o login
1. Lê CPF e senha do formulário
2. Busca no banco um funcionário com esses dados
3. Se não encontrar → reenvia o login com mensagem de erro
4. Se encontrar → salva o ID e CPF na **sessão** e redireciona para `/estoque`

> **Sessão** é um mecanismo do Flask que guarda dados do usuário enquanto ele navega pelo sistema. É como uma memória temporária.

---

#### `GET /logout` → Desloga o usuário
Apaga todos os dados da sessão e redireciona para a tela de login.

---

#### `GET /estoque` → Tela principal
1. Verifica se o usuário está logado (tem ID na sessão)
2. Se não estiver → redireciona para o login
3. Se estiver → busca todos os medicamentos e envia para o `estoque.html`

---

#### `POST /cadastrar` → Cadastra medicamento
1. Verifica se o usuário está logado
2. Lê nome e quantidade do formulário
3. Valida os dados (nome não vazio, quantidade não negativa)
4. Insere o medicamento no banco
5. Redireciona para `/estoque`

---

#### `POST /movimentar` → Entrada ou saída de estoque
1. Verifica se o usuário está logado
2. Lê ID do medicamento, tipo (`entrada`/`saida`) e quantidade
3. Busca a quantidade atual no banco
4. **Regra de negócio:** se for saída, verifica se há estoque suficiente
5. Calcula a nova quantidade
6. Atualiza o medicamento no banco
7. Registra a movimentação no histórico
8. Redireciona para `/estoque`

---

## Templates HTML

### `index.html` — Tela de Login

Formulário simples com dois campos:
- `name="cpf"` → lido pelo Flask via `request.form['cpf']`
- `name="senha"` → lido pelo Flask via `request.form['senha']`

O bloco `{% if erro %}` exibe a mensagem de erro enviada pelo Flask quando o login falha.

---

### `estoque.html` — Tela de Estoque

**Cadastro:** formulário que envia nome e quantidade para `/cadastrar`.

**Tabela de medicamentos:** gerada dinamicamente pelo loop Jinja2:
```django
{% for med in medicamentos %}
    ...linha da tabela...
{% endfor %}
```
O Flask envia a lista `medicamentos` e o Jinja2 cria uma linha para cada item.

**Botões de entrada/saída:** cada linha tem dois formulários. Ambos enviam para `/movimentar` com campos `hidden` que identificam o medicamento e o tipo da operação.

---

## Segurança

| Recurso | Proteção |
|---|---|
| `?` nos SQLs | Previne SQL Injection |
| `session` | Impede acesso às rotas sem login |
| Verificação de estoque | Impede quantidade negativa |