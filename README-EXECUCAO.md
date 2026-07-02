# Como Rodar o Sistema — Farmácia Hospitalar

## Pré-requisitos

Antes de começar, você precisa ter instalado:

- [Python 3.8 ou superior](https://www.python.org/downloads/)
- pip (gerenciador de pacotes do Python — já vem instalado com o Python)

Para verificar se o Python está instalado, abra o terminal e digite:
```bash
python --version
```

---

## Estrutura de Pastas

O projeto deve estar organizado assim antes de rodar:
```
farmacia/
│
├── app.py
├── setup_banco.py
│
├── templates/
│   ├── index.html
│   └── estoque.html
│
└── static/
    ├── style.css
    └── style2.css
```

---

## Instalação

### 1. Abra o terminal na pasta do projeto

No Windows, você pode:
- Navegar até a pasta pelo Explorador de Arquivos
- Clicar com o botão direito dentro da pasta
- Selecionar **"Abrir no Terminal"** ou **"Git Bash Here"**

### 2. Crie um ambiente virtual *(recomendado)*
```bash
python -m venv venv
```

Ative o ambiente virtual:

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

> Quando ativado, o terminal mostrará `(venv)` no início da linha.

### 3. Instale o Flask
```bash
pip install flask
```

---

## Criando o Banco de Dados

Execute o script de setup **uma única vez**:
```bash
python setup_banco.py
```

Se tudo correu bem, você verá no terminal:
```
Banco de dados criado com sucesso!
CPF de teste: 000.000.000-00
Senha de teste: admin123
```

Um arquivo `farmacia.db` será criado na pasta do projeto.

> Não é necessário rodar esse script novamente. Se rodar de novo, ele simplesmente ignora o que já existe.

---

## ▶ Rodando a Aplicação
```bash
python app.py
```

Você verá no terminal:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Abra o navegador e acesse:
```
http://localhost:5000
```

---

## Acesso de Teste

Use as credenciais criadas pelo `setup_banco.py`:

| Campo | Valor |
|---|---|
| CPF | 000.000.000-00 |
| Senha | admin123 |

---

## Encerrando o Sistema

No terminal onde o servidor está rodando, pressione:
```
Ctrl + C
```

---

## Problemas Comuns

**`ModuleNotFoundError: No module named 'flask'`**
→ O Flask não está instalado. Rode `pip install flask` e tente novamente.

**`python não é reconhecido como comando`**
→ O Python não está no PATH. Tente usar `python3` no lugar de `python`.

**Página não abre no navegador**
→ Verifique se o terminal mostra `Running on http://127.0.0.1:5000` e acesse exatamente esse endereço.

**`OperationalError: no such table`**
→ O banco não foi criado. Rode `python setup_banco.py` antes de iniciar o app.