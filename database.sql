-- Estrutura do banco (versão 1). Usada só para criar um banco NOVO.
-- Bancos existentes são atualizados pelas migrações em db.py (nada é apagado).

-- Clientes corporativos (pessoa jurídica)
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa TEXT NOT NULL,
    cnpj TEXT,
    contato TEXT,
    telefone TEXT,
    email TEXT,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Catálogo B2B
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    quantidade_minima INTEGER DEFAULT 10,
    unidade_venda TEXT NOT NULL DEFAULT 'unidade',   -- unidade | cento | kit
    preco_unitario DECIMAL(10,2) NOT NULL,           -- preço por unidade_venda
    custo_producao DECIMAL(10,2) NOT NULL,           -- interno: nunca vai para o site
    categoria TEXT,
    imagem TEXT,                                     -- arquivo em static/img/produtos/
    ativo INTEGER NOT NULL DEFAULT 1                 -- 0 = escondido do site
);

-- Orçamentos e pedidos (a tabela se chama "vendas"; na tela aparece como "Pedidos")
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    data_venda DATE DEFAULT (DATE('now')),
    data_entrega DATE,
    valor_total DECIMAL(10,2) NOT NULL,
    forma_pagamento TEXT,
    status TEXT DEFAULT 'Orçamento',
    observacoes TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Itens de cada orçamento/pedido (guarda preço e custo da época)
CREATE TABLE IF NOT EXISTS itens_venda (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER NOT NULL,
    produto_id INTEGER,                              -- vazio = item avulso
    descricao TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    custo_unitario DECIMAL(10,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON vendas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_vendas_status ON vendas(status);
CREATE INDEX IF NOT EXISTS idx_itens_venda ON itens_venda(venda_id);
