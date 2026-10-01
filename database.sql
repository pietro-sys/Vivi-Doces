-- Tabela de Clientes Corporativos
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa TEXT NOT NULL,
    cnpj TEXT,
    contato TEXT,
    telefone TEXT
);

-- Tabela de Produtos (Cardápio B2B)
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    quantidade_minima INTEGER DEFAULT 10,
    preco_unitario DECIMAL(10,2) NOT NULL,
    custo_producao DECIMAL(10,2) NOT NULL
);

-- Tabela de Vendas
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    valor_total DECIMAL(10,2) NOT NULL,
    status TEXT DEFAULT 'Orçamento',
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);