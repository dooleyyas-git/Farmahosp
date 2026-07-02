CREATE SCHEMA integrador;
USE SCHEMA integrador;

CREATE TABLE FUNCIONARIOS (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cpf VARCHAR(20) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL
);

CREATE TABLE MEDICAMENTOS (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    quantidade_atual INTEGER DEFAULT 0
);

CREATE TABLE UTENSILIOS (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    quantidade_atual INTEGER DEFAULT 0
);

CREATE TABLE MOVIMENTACOES_UTENSILIOS (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_utensilio INTEGER NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tipo_utensilio CHECK (tipo IN ('entrada', 'saida')),
    CONSTRAINT fk_utensilio
        FOREIGN KEY (id_utensilio)
        REFERENCES UTENSILIOS(id)
);

CREATE TABLE MOVIMENTACOES (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_medicamento INTEGER NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tipo CHECK (tipo IN ('entrada', 'saida')),
    CONSTRAINT fk_medicamento
        FOREIGN KEY (id_medicamento)
        REFERENCES MEDICAMENTOS(id)
);

/* Opção com tudo em um "movimentações" mas não sei qual ficaria melhor"
CREATE TABLE MOVIMENTACOES (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_medicamento INTEGER,
    id_utensilio INTEGER,
    tipo VARCHAR(10) NOT NULL,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tipo CHECK (tipo IN ('entrada', 'saida')),
    CONSTRAINT fk_medicamento
        FOREIGN KEY (id_medicamento)
        REFERENCES MEDICAMENTOS(id),
    CONSTRAINT fk_utensilio
        FOREIGN KEY (id_utensilio)
        REFERENCES UTENSILIOS(id),
    CONSTRAINT chk_apenas_um CHECK (
        (id_medicamento IS NOT NULL AND id_utensilio IS NULL) OR
        (id_medicamento IS NULL AND id_utensilio IS NOT NULL)
    )
);*/

