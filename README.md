# Vivi Doces Gourmet

Catálogo B2B (site) e painel interno para orçamentos e pedidos de empresas.
Feito com Flask + SQLite.

## Como rodar

```
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # Windows   (Linux/Mac: cp .env.example .env)
```

Abra o arquivo `.env` e troque `ADMIN_PASSWORD` por uma senha sua. Depois:

```
python app.py
```

- Site: http://127.0.0.1:5000
- Painel: http://127.0.0.1:5000/admin (senha do `.env`; a mesma para a família toda)

Para o servidor recarregar sozinho ao editar o código, coloque `FLASK_DEBUG=1` no `.env`.

## Como funciona

**Site:** o cliente monta uma lista de produtos e envia pelo WhatsApp, com empresa,
contato e data desejada. Nada é gravado no servidor nessa etapa.

**Painel:** `Pedidos` (orçamentos e vendas, com itens e status), `Clientes` e `Produtos`
(preços, mínimo, custo e se aparece no site). Em cada pedido há um texto de orçamento
pronto para copiar ou abrir direto no WhatsApp do cliente.

Status do pedido: Orçamento → Aprovado → Em produção → Entregue → Pago (ou Cancelado).

## Onde mudar as coisas

- **Textos de contato, prazo (7 dias), pedido mínimo, CNPJ, Instagram:** bloco
  `NEGOCIO` no começo do `app.py`. Campo vazio não aparece no site.
- **Preços e produtos:** painel, aba Produtos. Alterar um preço não muda orçamentos antigos.
- **Fotos:** copie o arquivo para `static/img/produtos/` e escreva o nome dele no cadastro
  do produto. Sem foto, o site mostra um cartão com a inicial do produto.
- **Perguntas frequentes e textos da página:** `templates/index.html`.

## Banco de dados

- O arquivo `database.db` é criado sozinho na primeira execução (`database.sql` + `seed.sql`).
- Um banco existente é atualizado automaticamente, **sem apagar nada** (migrações em `db.py`).
- Backup: no rodapé do painel, "Baixar backup". Faça de vez em quando e guarde em local seguro.
- `database.db` e `.env` estão no `.gitignore`: não vão para o GitHub (têm dados de clientes e a senha).

## Segurança já incluída

Login no painel (com bloqueio após tentativas erradas), proteção CSRF em todos os
formulários, consultas parametrizadas, validação de CNPJ/telefone/valores no servidor,
cabeçalhos de segurança (CSP) e custo de produção nunca enviado ao site público.

## Antes de publicar na internet

- Usar um servidor de produção (por exemplo `gunicorn` em Linux) em vez de `python app.py`.
- Servir por HTTPS e colocar `COOKIE_SEGURO=1` no `.env`.
- Definir um `SECRET_KEY` fixo no `.env`.
- Escolher uma senha longa em `ADMIN_PASSWORD`.
- Incluir uma política de privacidade simples (LGPD), já que o painel guarda contatos de empresas.

## Arquivos

```
app.py            rotas, validações e configuração do negócio
db.py             conexão e migrações do banco
database.sql      estrutura do banco (banco novo)
seed.sql          catálogo inicial (banco novo)
templates/        index.html (site) e admin/ (painel)
static/           css, js e img/produtos/
```
