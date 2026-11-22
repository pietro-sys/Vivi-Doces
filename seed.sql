-- Catálogo inicial. Só é carregado quando o banco é criado do zero.
-- Depois disso, preços e produtos são editados pelo painel (/admin/produtos).

INSERT INTO produtos (nome, descricao, quantidade_minima, unidade_venda, preco_unitario, custo_producao, categoria) VALUES
('Brownie Artesanal (6x6)', 'Com etiqueta de personalização com a logomarca da empresa.', 10, 'unidade', 15.00, 7.50, 'Doces Individuais'),
('Pão de Mel Artesanal (6x6)', 'Sabor tradicional (Doce de Leite), com etiqueta personalizada.', 10, 'unidade', 9.50, 5.00, 'Doces Individuais'),
('Cones Recheados Artesanais', 'Cones recheados com excelente padrão de qualidade.', 10, 'unidade', 19.08, 12.00, 'Doces Individuais'),
('Cupcake Tradicional', 'Cupcake artesanal tradicional.', 10, 'unidade', 11.66, 5.50, 'Doces Individuais'),
('Cupcake Personalizado', 'Personalizado com a logomarca da empresa.', 10, 'unidade', 14.50, 6.50, 'Doces Individuais'),
('Bolo de Pote (250ml)', 'Camadas intercaladas de massa úmida e recheios artesanais.', 10, 'unidade', 10.60, 6.50, 'Doces Individuais'),
('Mini Copo da Felicidade (200ml)', 'Explosão de texturas e sabores em camadas.', 10, 'unidade', 12.19, 7.00, 'Doces Individuais'),
('Coxinha de Morango (Padrão)', 'Morango fresco envolto em brigadeiro gourmet ou Leite Ninho.', 10, 'unidade', 10.07, 6.50, 'Doces Individuais'),
('Coxinha de Morango (Premium)', 'Morango selecionado de tamanho grande coberto com brigadeiro ou ninho.', 10, 'unidade', 15.90, 12.00, 'Doces Individuais'),
('Palha Italiana de Brigadeiro (6x6)', 'O clássico com etiqueta personalizada com a logo da empresa.', 10, 'unidade', 9.50, 6.50, 'Doces Individuais'),
('Palha Italiana de Pistache (6x6)', 'Versão sofisticada com o sabor autêntico do pistache.', 10, 'unidade', 11.30, 7.50, 'Doces Individuais'),
('Pirulitos de Chocolate (2D)', 'Pirulitos em pasta americana com formato 2D.', 10, 'unidade', 16.08, 11.67, 'Doces Individuais'),
('Cento de Docinhos Tradicionais (Festa)', 'Cento (100 unidades) tamanho festa, até 3 sabores.', 1, 'cento', 190.80, 150.00, 'Festas e Eventos'),
('Cento de Docinhos Tradicionais (Médio)', 'Cento (100 unidades) tamanho médio, até 3 sabores.', 1, 'cento', 243.80, 200.00, 'Festas e Eventos'),
('Cento de Brigadeiro Gourmet', 'Cento (100 unidades) de doces gourmet selecionados.', 1, 'cento', 275.60, 220.00, 'Festas e Eventos'),
('Kit Festa Doces Modelados (2D - 30 doces)', 'Combo de 30 doces modelados projeto 2D.', 1, 'kit', 424.00, 350.00, 'Kits Corporativos'),
('Kit Festa Doces Modelados (3D - 30 doces)', 'Combo de 30 doces modelados projeto 3D (com volume/bonequinhos).', 1, 'kit', 477.00, 400.00, 'Kits Corporativos');
