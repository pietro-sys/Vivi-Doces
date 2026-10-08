-- Tabela de Clientes Corporativos (Pessoa Jurídica)
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa TEXT NOT NULL,
    cnpj TEXT,
    contato TEXT,
    telefone TEXT,
    total_pedidos INTEGER DEFAULT 0,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Produtos / Catálogo B2B
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    quantidade_minima INTEGER DEFAULT 10,
    preco_unitario DECIMAL(10,2) NOT NULL,
    custo_producao DECIMAL(10,2) NOT NULL,
    categoria TEXT
);

-- Tabela de Vendas
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    data_venda DATE DEFAULT (DATE('now')),
    valor_total DECIMAL(10,2) NOT NULL,
    forma_pagamento TEXT,
    status TEXT DEFAULT 'Orçamento',
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Inserção dos Produtos Reais da Planilha e Catálogo B2B
INSERT INTO produtos (nome, descricao, quantidade_minima, preco_unitario, custo_producao, categoria) VALUES
('Brownie Artesanal (6x6)', 'Com etiqueta de personalização com a logomarca da empresa.', 10, 15.00, 7.50, 'Lotes Individuais'),
('Pão de Mel Artesanal (6x6)', 'Sabor tradicional (Doce de Leite), com etiqueta personalizada.', 10, 9.50, 5.00, 'Lotes Individuais'),
('Cones Recheados Artesanais', 'Cones recheados com excelente padrão de qualidade.', 10, 19.08, 12.00, 'Lotes Individuais'),
('Cupcake Tradicional', 'Cupcake artesanal tradicional.', 10, 11.66, 5.50, 'Lotes Individuais'),
('Cupcake Personalizado', 'Personalizado com a logomarca da empresa.', 10, 14.50, 6.50, 'Lotes Individuais'),
('Bolo de Pote (250ml)', 'Camadas intercaladas de massa úmida e recheios artesanais.', 10, 10.60, 6.50, 'Lotes Individuais'),
('Mini Copo da Felicidade (200ml)', 'Explosão de texturas e sabores em camadas.', 10, 12.19, 7.00, 'Lotes Individuais'),
('Coxinha de Morango (Padrão)', 'Morango fresco envolto em brigadeiro gourmet ou Leite Ninho.', 10, 10.07, 6.50, 'Lotes Individuais'),
('Coxinha de Morango (Premium)', 'Morango selecionado de tamanho grande coberto com brigadeiro ou ninho.', 10, 15.90, 12.00, 'Lotes Individuais'),
('Palha Italiana de Brigadeiro (6x6)', 'O clássico com etiqueta personalizada com a logo da empresa.', 10, 9.50, 6.50, 'Lotes Individuais'),
('Palha Italiana de Pistache (6x6)', 'Versão sofisticada com o sabor autêntico do pistache.', 10, 11.30, 7.50, 'Lotes Individuais'),
('Pirulitos de Chocolate (2D)', 'Pirulitos em pasta americana com formato 2D.', 10, 16.08, 11.67, 'Lotes Individuais'),
('Cento de Docinhos Tradicionais (Festa)', 'Cento (100 unidades) tamanho festa, até 3 sabores.', 1, 190.80, 150.00, 'Festas e Eventos'),
('Cento de Docinhos Tradicionais (Médio)', 'Cento (100 unidades) tamanho médio, até 3 sabores.', 1, 243.80, 200.00, 'Festas e Eventos'),
('Cento de Brigadeiro Gourmet', 'Cento (100 unidades) de doces gourmet selecionados.', 1, 275.60, 220.00, 'Festas e Eventos'),
('Kit Festa Doces Modelados (2D - 30 doces)', 'Combo de 30 doces modelados projeto 2D.', 1, 424.00, 350.00, 'Kits Corporativos'),
('Kit Festa Doces Modelados (3D - 30 doces)', 'Combo de 30 doces modelados projeto 3D (com volume/bonequinhos).', 1, 477.00, 400.00, 'Kits Corporativos');