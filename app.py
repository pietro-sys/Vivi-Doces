"""Vivi Doces Gourmet — catálogo B2B (site) e painel interno (/admin)."""
import hmac
import os
import re
import secrets
import sqlite3
import tempfile
import time
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.utils import secure_filename

import db
from db import get_db

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ==========================================================================
# CONFIGURAÇÃO DO NEGÓCIO — é aqui que se muda texto, contato e prazos.
# Campos vazios ("") simplesmente não aparecem no site.
# ==========================================================================
NEGOCIO = {
    "nome": "Vivi Doces Gourmet",
    "whatsapp": "5511983340797",     # só números, com 55 + DDD
    "instagram": "",                 # ex.: "vivi.doces"
    "email": "",
    "cidade": "",                    # ex.: "São Paulo - SP"
    "razao_social": "",              # ex.: "Vivi Doces Gourmet LTDA"
    "cnpj": "",                      # ex.: "00.000.000/0001-00"
    "prazo_minimo_dias": 7,          # antecedência recomendada para encomendas
    "pedido_minimo": 10,             # usado nos textos da página inicial
}

CATEGORIAS_ORDEM = ["Doces Individuais", "Kits Corporativos", "Festas e Eventos"]
CATEGORIAS_TEXTO = {
    "Doces Individuais": "Ideais para brindes, reuniões e ações com a equipe. "
                         "Pedido mínimo de 10 unidades por produto.",
    "Kits Corporativos": "Combos de doces modelados em 2D ou 3D para eventos e ações da empresa.",
    "Festas e Eventos": "Centos de docinhos para confraternizações, inaugurações e eventos.",
}

STATUS = ["Orçamento", "Aprovado", "Em produção", "Entregue", "Pago", "Cancelado"]
STATUS_CLASSE = {
    "Orçamento": "orcamento", "Aprovado": "aprovado", "Em produção": "producao",
    "Entregue": "entregue", "Pago": "pago", "Cancelado": "cancelado",
}
UNIDADES = {"unidade": ("unidade", "unidades"), "cento": ("cento", "centos"),
            "kit": ("kit", "kits")}
FORMAS_PAGAMENTO = ["PIX", "Boleto", "Cartão", "Transferência", "Dinheiro", "A combinar"]
EXTENSOES_IMAGEM = (".jpg", ".jpeg", ".png", ".webp")

# ==========================================================================
# APLICAÇÃO
# ==========================================================================


def _carregar_secret_key():
    chave = os.getenv("SECRET_KEY")
    if chave:
        return chave
    pasta = BASE_DIR / "instance"
    pasta.mkdir(exist_ok=True)
    arquivo = pasta / "secret_key"
    if not arquivo.exists():
        arquivo.write_text(secrets.token_hex(32))
        try:
            arquivo.chmod(0o600)
        except OSError:
            pass
    return arquivo.read_text().strip()


app = Flask(__name__)
app.config.update(
    DATABASE=os.getenv("DATABASE_PATH", str(BASE_DIR / "database.db")),
    SECRET_KEY=_carregar_secret_key(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SEGURO") == "1",   # ligar quando houver HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    MAX_CONTENT_LENGTH=1024 * 1024,
)
app.teardown_appcontext(db.close_db)
db.init_db(app.config["DATABASE"])

# ==========================================================================
# FUNÇÕES AUXILIARES
# ==========================================================================


def D(valor):
    """Converte qualquer número do banco em Decimal com 2 casas."""
    try:
        return Decimal(str(valor if valor is not None else 0)).quantize(
            Decimal("0.01"), ROUND_HALF_UP)
    except InvalidOperation:
        return Decimal("0.00")


def parse_dinheiro(texto):
    """Aceita '15', '15,50', '1.234,56', 'R$ 15.00'. Devolve Decimal ou None."""
    s = (texto or "").strip().replace("R$", "").replace(" ", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):      # "1.500" = mil e quinhentos
        s = s.replace(".", "")
    try:
        valor = Decimal(s)
    except InvalidOperation:
        return None
    if not valor.is_finite() or valor < 0 or valor > Decimal("9999999.99"):
        return None
    return valor.quantize(Decimal("0.01"), ROUND_HALF_UP)


def parse_int(texto, minimo=0, maximo=100000):
    try:
        n = int(str(texto).strip())
    except ValueError:
        return None
    return n if minimo <= n <= maximo else None


def parse_data(texto):
    """Devolve (data ou None, valido). Vazio é válido."""
    texto = (texto or "").strip()
    if not texto:
        return None, True
    try:
        return date.fromisoformat(texto), True
    except ValueError:
        return None, False


def so_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def cnpj_valido(digitos):
    if len(digitos) != 14 or digitos == digitos[0] * 14:
        return False

    def digito(base, pesos):
        resto = sum(int(n) * p for n, p in zip(base, pesos)) % 11
        return "0" if resto < 2 else str(11 - resto)

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    return (digitos[12] == digito(digitos[:12], pesos1)
            and digitos[13] == digito(digitos[:13], [6] + pesos1))


def formatar_cnpj(d):
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def numero_whatsapp(telefone):
    d = so_digitos(telefone)
    if d.startswith("55") and len(d) in (12, 13):
        return d
    if len(d) in (10, 11):
        return "55" + d
    return d


def brl(valor):
    d = D(valor)
    sinal = "-" if d < 0 else ""
    inteiro, centavos = f"{abs(d):.2f}".split(".")
    return f"{sinal}R$ {int(inteiro):,}".replace(",", ".") + f",{centavos}"


def num_br(valor):
    """15.5 -> '15,50' (para campos de formulário)."""
    return f"{D(valor):.2f}".replace(".", ",")


def data_br(valor):
    if not valor:
        return ""
    if isinstance(valor, str):
        try:
            valor = date.fromisoformat(valor[:10])
        except ValueError:
            return valor
    return valor.strftime("%d/%m/%Y")


def qtd_un(qtd, unidade):
    singular, plural = UNIDADES.get(unidade, UNIDADES["unidade"])
    return f"{qtd} {singular if qtd == 1 else plural}"


app.jinja_env.filters.update(brl=brl, num_br=num_br, data_br=data_br, qtd_un=qtd_un)


@app.context_processor
def contexto():
    return {
        "NEGOCIO": NEGOCIO, "STATUS": STATUS, "STATUS_CLASSE": STATUS_CLASSE,
        "UNIDADES": UNIDADES, "FORMAS_PAGAMENTO": FORMAS_PAGAMENTO,
        "hoje": date.today(), "ano": date.today().year,
        "csrf_token": csrf_token,
    }


# ==========================================================================
# SEGURANÇA: CSRF, login, cabeçalhos
# ==========================================================================


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


@app.before_request
def proteger():
    if request.method == "POST":
        esperado = session.get("csrf", "")
        enviado = request.form.get("csrf_token", "")
        if not esperado or not hmac.compare_digest(esperado, enviado):
            abort(400)
    if request.path.startswith("/admin") and request.endpoint != "login":
        if not session.get("admin"):
            destino = request.full_path.rstrip("?")
            return redirect(url_for("login", next=destino))


@app.after_request
def cabecalhos(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    resp.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
        "form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
    if request.path.startswith("/admin"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


_falhas = {}                      # ip -> (tentativas, início da janela)
LIMITE_FALHAS, JANELA_SEG = 5, 15 * 60


def _bloqueado(ip):
    registro = _falhas.get(ip)
    if not registro:
        return False
    tentativas, inicio = registro
    if time.time() - inicio > JANELA_SEG:
        _falhas.pop(ip, None)
        return False
    return tentativas >= LIMITE_FALHAS


def _registrar_falha(ip):
    tentativas, inicio = _falhas.get(ip, (0, time.time()))
    if time.time() - inicio > JANELA_SEG:
        tentativas, inicio = 0, time.time()
    _falhas[ip] = (tentativas + 1, inicio)


def _destino_seguro(destino):
    if destino and destino.startswith("/admin") and not destino.startswith("//"):
        return destino
    return url_for("painel")


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    senha_config = os.getenv("ADMIN_PASSWORD", "")
    status = 200
    if request.method == "POST":
        ip = request.remote_addr or "?"
        senha = request.form.get("senha", "")
        if _bloqueado(ip):
            flash("Muitas tentativas. Aguarde alguns minutos e tente de novo.", "erro")
            status = 429
        elif not senha_config:
            flash("A senha do painel ainda não foi configurada (veja o README).", "erro")
        elif hmac.compare_digest(senha.encode(), senha_config.encode()):
            _falhas.pop(ip, None)
            session.clear()
            session["admin"] = True
            session.permanent = True
            return redirect(_destino_seguro(request.args.get("next")))
        else:
            _registrar_falha(ip)
            flash("Senha incorreta.", "erro")
            status = 401
    return render_template("admin/login.html", configurada=bool(senha_config)), status


@app.route("/admin/sair", methods=["POST"])
def sair():
    session.clear()
    return redirect(url_for("index"))


# ==========================================================================
# SITE PÚBLICO
# ==========================================================================


@app.route("/")
def index():
    linhas = get_db().execute(
        """SELECT id, nome, descricao, quantidade_minima, unidade_venda,
                  preco_unitario, categoria, imagem
           FROM produtos WHERE ativo = 1 ORDER BY id""").fetchall()
    pasta_img = BASE_DIR / "static" / "img" / "produtos"
    grupos = {}
    for linha in linhas:
        produto = dict(linha)
        produto["imagem_ok"] = bool(produto["imagem"]) and (pasta_img / produto["imagem"]).is_file()
        grupos.setdefault(produto["categoria"] or "Outros", []).append(produto)
    ordem = [c for c in CATEGORIAS_ORDEM if c in grupos]
    ordem += sorted(c for c in grupos if c not in CATEGORIAS_ORDEM)
    categorias = [{"nome": c, "texto": CATEGORIAS_TEXTO.get(c, ""), "indice": i,
                   "produtos": grupos[c]} for i, c in enumerate(ordem)]
    return render_template("index.html", categorias=categorias)


# ==========================================================================
# PAINEL — início
# ==========================================================================


@app.route("/admin")
def painel():
    conn = get_db()

    def resumo(*status):
        marcas = ",".join("?" * len(status))
        return conn.execute(
            f"SELECT COUNT(*) AS n, COALESCE(SUM(valor_total), 0) AS total "
            f"FROM vendas WHERE status IN ({marcas})", status).fetchone()

    entregas = conn.execute(
        """SELECT v.id, v.data_entrega, v.valor_total, v.status, c.empresa
           FROM vendas v LEFT JOIN clientes c ON c.id = v.cliente_id
           WHERE v.status IN ('Aprovado', 'Em produção') AND v.data_entrega IS NOT NULL
           ORDER BY v.data_entrega, v.id LIMIT 10""").fetchall()
    recentes = conn.execute(
        """SELECT v.id, v.data_venda, v.valor_total, v.status, c.empresa
           FROM vendas v LEFT JOIN clientes c ON c.id = v.cliente_id
           ORDER BY v.id DESC LIMIT 8""").fetchall()
    return render_template(
        "admin/painel.html", abertos=resumo("Orçamento"),
        andamento=resumo("Aprovado", "Em produção"), a_receber=resumo("Entregue"),
        entregas=entregas, recentes=recentes, hoje_iso=date.today().isoformat())


@app.route("/admin/backup")
def backup():
    """Baixa uma cópia consistente do banco (use de vez em quando)."""
    with tempfile.TemporaryDirectory() as pasta:
        destino = Path(pasta) / "backup.db"
        origem = sqlite3.connect(app.config["DATABASE"])
        copia = sqlite3.connect(destino)
        try:
            origem.backup(copia)
        finally:
            copia.close()
            origem.close()
        conteudo = destino.read_bytes()
    nome = f"vivi-doces-backup-{datetime.now():%Y%m%d-%H%M}.db"
    return Response(conteudo, mimetype="application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="{nome}"'})


# ==========================================================================
# PAINEL — pedidos (orçamentos e vendas)
# ==========================================================================


@app.route("/admin/pedidos")
def pedidos():
    status = request.args.get("status", "")
    busca = request.args.get("q", "").strip()
    if status not in STATUS:
        status = ""
    lista = get_db().execute(
        """SELECT v.id, v.data_venda, v.data_entrega, v.valor_total, v.status, c.empresa
           FROM vendas v LEFT JOIN clientes c ON c.id = v.cliente_id
           WHERE (:status = '' OR v.status = :status)
             AND (:q = '' OR c.empresa LIKE :like)
           ORDER BY v.id DESC LIMIT 300""",
        {"status": status, "q": busca, "like": f"%{busca}%"}).fetchall()
    return render_template("admin/pedidos.html", lista=lista, status_atual=status,
                           busca=busca, hoje_iso=date.today().isoformat())


def _pega(lista, i):
    return lista[i] if i < len(lista) else ""


def _ler_pedido_form(conn):
    """Lê e valida o formulário. Devolve (dados, itens_form, itens_validos, erros)."""
    f = request.form
    erros = []
    dados = {
        "cliente_id": f.get("cliente_id", "").strip(),
        "status": f.get("status", "").strip(),
        "data_entrega": f.get("data_entrega", "").strip(),
        "forma_pagamento": f.get("forma_pagamento", "").strip()[:60],
        "observacoes": f.get("observacoes", "").strip()[:2000],
    }
    cliente_id = parse_int(dados["cliente_id"], 1, 10 ** 9)
    if cliente_id is None or not conn.execute(
            "SELECT 1 FROM clientes WHERE id = ?", (cliente_id,)).fetchone():
        erros.append("Escolha o cliente.")
    if dados["status"] not in STATUS:
        erros.append("Status inválido.")
    entrega, entrega_ok = parse_data(dados["data_entrega"])
    if not entrega_ok:
        erros.append("Data de entrega inválida.")

    pids, descs = f.getlist("item_produto"), f.getlist("item_descricao")
    qtds, precos, custos = f.getlist("item_qtd"), f.getlist("item_preco"), f.getlist("item_custo")
    itens_form, validos = [], []
    for i in range(max(len(pids), len(descs), len(qtds), len(precos))):
        pid_txt, desc = _pega(pids, i).strip(), _pega(descs, i).strip()[:160]
        qtd_txt, preco_txt = _pega(qtds, i).strip(), _pega(precos, i).strip()
        custo_txt = _pega(custos, i).strip()
        if not any((pid_txt, desc, qtd_txt, preco_txt)):
            continue                                   # linha em branco
        itens_form.append({"produto_id": pid_txt, "descricao": desc, "quantidade": qtd_txt,
                           "preco": preco_txt, "custo": custo_txt})
        n = len(itens_form)

        produto = None
        if pid_txt:
            pid = parse_int(pid_txt, 1, 10 ** 9)
            produto = conn.execute("SELECT id, nome, custo_producao FROM produtos WHERE id = ?",
                                   (pid,)).fetchone() if pid else None
            if produto is None:
                erros.append(f"Item {n}: produto inválido.")
                continue
        if not desc and produto:
            desc = produto["nome"]
        qtd, preco = parse_int(qtd_txt, 1, 100000), parse_dinheiro(preco_txt)
        if not desc:
            erros.append(f"Item {n}: escreva a descrição.")
        if qtd is None:
            erros.append(f"Item {n}: quantidade inválida.")
        if preco is None:
            erros.append(f"Item {n}: preço inválido.")
        custo = parse_dinheiro(custo_txt) if custo_txt else None
        if custo is None:
            custo = D(produto["custo_producao"]) if produto else Decimal("0.00")
        if desc and qtd is not None and preco is not None:
            validos.append({"produto_id": produto["id"] if produto else None,
                            "descricao": desc, "quantidade": qtd, "preco": preco, "custo": custo})
    if not itens_form:
        erros.append("Adicione pelo menos um item.")
    dados["_cliente_id"], dados["_entrega"] = cliente_id, entrega
    return dados, itens_form, validos, erros


def montar_texto_orcamento(cliente, venda, itens):
    contato = (cliente["contato"] or "").strip() if cliente else ""
    abertura = f"Olá, {contato}!" if contato else "Olá!"
    para = f" para a {cliente['empresa']}" if cliente else ""
    linhas = [f"{abertura} Segue o orçamento da {NEGOCIO['nome']}{para}:", ""]
    for it in itens:
        subtotal = D(it["quantidade"]) * D(it["preco_unitario"])
        linhas.append(f"• {it['quantidade']}x {it['descricao']} — "
                      f"{brl(it['preco_unitario'])} = {brl(subtotal)}")
    linhas += ["", f"*Total: {brl(venda['valor_total'])}*"]
    if venda["data_entrega"]:
        linhas.append(f"Entrega prevista: {data_br(venda['data_entrega'])}")
    if venda["forma_pagamento"]:
        linhas.append(f"Pagamento: {venda['forma_pagamento']}")
    linhas += ["", "Qualquer dúvida, é só chamar!"]
    return "\n".join(linhas)


@app.route("/admin/pedidos/novo", methods=["GET", "POST"])
@app.route("/admin/pedidos/<int:venda_id>", methods=["GET", "POST"])
def pedido(venda_id=None):
    conn = get_db()
    venda = None
    if venda_id:
        venda = conn.execute("SELECT * FROM vendas WHERE id = ?", (venda_id,)).fetchone()
        if venda is None:
            abort(404)

    clientes = conn.execute(
        "SELECT id, empresa FROM clientes ORDER BY empresa COLLATE NOCASE").fetchall()
    produtos = [dict(p) for p in conn.execute(
        """SELECT id, nome, preco_unitario, custo_producao, unidade_venda,
                  quantidade_minima, ativo, COALESCE(categoria, 'Outros') AS categoria
           FROM produtos
           WHERE ativo = 1 OR id IN (SELECT produto_id FROM itens_venda WHERE venda_id = ?)
           ORDER BY categoria, nome COLLATE NOCASE""", (venda_id or 0,))]

    erros, status_http = [], 200
    if request.method == "POST":
        dados, itens, validos, erros = _ler_pedido_form(conn)
        if not erros:
            total = sum((i["quantidade"] * i["preco"] for i in validos), Decimal("0.00"))
            campos = (dados["_cliente_id"], float(total), dados["forma_pagamento"] or None,
                      dados["status"], dados["_entrega"].isoformat() if dados["_entrega"] else None,
                      dados["observacoes"] or None)
            if venda:
                conn.execute(
                    """UPDATE vendas SET cliente_id = ?, valor_total = ?, forma_pagamento = ?,
                       status = ?, data_entrega = ?, observacoes = ? WHERE id = ?""",
                    campos + (venda["id"],))
                conn.execute("DELETE FROM itens_venda WHERE venda_id = ?", (venda["id"],))
                novo_id = venda["id"]
            else:
                novo_id = conn.execute(
                    """INSERT INTO vendas (cliente_id, valor_total, forma_pagamento, status,
                       data_entrega, observacoes) VALUES (?, ?, ?, ?, ?, ?)""", campos).lastrowid
            conn.executemany(
                """INSERT INTO itens_venda (venda_id, produto_id, descricao, quantidade,
                   preco_unitario, custo_unitario) VALUES (?, ?, ?, ?, ?, ?)""",
                [(novo_id, i["produto_id"], i["descricao"], i["quantidade"],
                  float(i["preco"]), float(i["custo"])) for i in validos])
            conn.commit()
            flash("Pedido salvo.", "ok")
            return redirect(url_for("pedido", venda_id=novo_id))
        status_http = 422
    elif venda:
        dados = {"cliente_id": str(venda["cliente_id"] or ""), "status": venda["status"],
                 "data_entrega": venda["data_entrega"] or "",
                 "forma_pagamento": venda["forma_pagamento"] or "",
                 "observacoes": venda["observacoes"] or ""}
        itens = [{"produto_id": str(i["produto_id"] or ""), "descricao": i["descricao"],
                  "quantidade": str(i["quantidade"]), "preco": num_br(i["preco_unitario"]),
                  "custo": num_br(i["custo_unitario"])}
                 for i in conn.execute("SELECT * FROM itens_venda WHERE venda_id = ? ORDER BY id",
                                       (venda["id"],))]
    else:
        dados = {"cliente_id": request.args.get("cliente", ""), "status": "Orçamento",
                 "data_entrega": "", "forma_pagamento": "", "observacoes": ""}
        itens = []

    texto = wa_link = None
    if venda and request.method == "GET":
        cliente = conn.execute("SELECT * FROM clientes WHERE id = ?",
                               (venda["cliente_id"],)).fetchone()
        itens_db = conn.execute("SELECT * FROM itens_venda WHERE venda_id = ? ORDER BY id",
                                (venda["id"],)).fetchall()
        if itens_db:
            texto = montar_texto_orcamento(cliente, venda, itens_db)
            numero = numero_whatsapp(cliente["telefone"]) if cliente else ""
            wa_link = f"https://wa.me/{numero}?text={quote(texto)}"

    return render_template("admin/pedido_form.html", venda=venda, dados=dados, itens=itens,
                           clientes=clientes, produtos=produtos, erros=erros,
                           texto=texto, wa_link=wa_link), status_http


@app.route("/admin/pedidos/<int:venda_id>/excluir", methods=["POST"])
def pedido_excluir(venda_id):
    conn = get_db()
    conn.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))   # itens saem em cascata
    conn.commit()
    flash("Pedido excluído.", "ok")
    return redirect(url_for("pedidos"))


# ==========================================================================
# PAINEL — clientes
# ==========================================================================


@app.route("/admin/clientes")
def clientes():
    busca = request.args.get("q", "").strip()
    lista = get_db().execute(
        """SELECT c.id, c.empresa, c.cnpj, c.contato, c.telefone,
                  COUNT(CASE WHEN v.status NOT IN ('Orçamento', 'Cancelado') THEN 1 END) AS pedidos,
                  COALESCE(SUM(CASE WHEN v.status NOT IN ('Orçamento', 'Cancelado')
                                    THEN v.valor_total END), 0) AS total
           FROM clientes c LEFT JOIN vendas v ON v.cliente_id = c.id
           WHERE (:q = '' OR c.empresa LIKE :like OR c.contato LIKE :like OR c.cnpj LIKE :like)
           GROUP BY c.id ORDER BY c.empresa COLLATE NOCASE""",
        {"q": busca, "like": f"%{busca}%"}).fetchall()
    return render_template("admin/clientes.html", lista=lista, busca=busca)


@app.route("/admin/clientes/novo", methods=["GET", "POST"])
@app.route("/admin/clientes/<int:cliente_id>", methods=["GET", "POST"])
def cliente(cliente_id=None):
    conn = get_db()
    atual = None
    if cliente_id:
        atual = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        if atual is None:
            abort(404)

    erros, status_http = [], 200
    if request.method == "POST":
        f = request.form
        dados = {c: f.get(c, "").strip()[:n] for c, n in (
            ("empresa", 120), ("cnpj", 30), ("contato", 80), ("telefone", 30),
            ("email", 120), ("observacoes", 2000))}
        if not dados["empresa"]:
            erros.append("Informe o nome da empresa.")
        if dados["cnpj"]:
            digitos = so_digitos(dados["cnpj"])
            if not cnpj_valido(digitos):
                erros.append("CNPJ inválido. Confira os números.")
            else:
                dados["cnpj"] = formatar_cnpj(digitos)
                for outro in conn.execute("SELECT id, empresa, cnpj FROM clientes"):
                    if outro["id"] != cliente_id and so_digitos(outro["cnpj"]) == digitos:
                        erros.append(f"Esse CNPJ já está cadastrado ({outro['empresa']}).")
                        break
        if dados["telefone"] and not 10 <= len(so_digitos(dados["telefone"])) <= 13:
            erros.append("Telefone inválido. Use DDD + número.")
        if dados["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", dados["email"]):
            erros.append("E-mail inválido.")
        if not erros:
            valores = (dados["empresa"], dados["cnpj"] or None, dados["contato"] or None,
                       dados["telefone"] or None, dados["email"] or None,
                       dados["observacoes"] or None)
            if atual:
                conn.execute("""UPDATE clientes SET empresa = ?, cnpj = ?, contato = ?,
                                telefone = ?, email = ?, observacoes = ? WHERE id = ?""",
                             valores + (atual["id"],))
                novo_id = atual["id"]
            else:
                novo_id = conn.execute(
                    """INSERT INTO clientes (empresa, cnpj, contato, telefone, email, observacoes)
                       VALUES (?, ?, ?, ?, ?, ?)""", valores).lastrowid
            conn.commit()
            flash("Cliente salvo.", "ok")
            return redirect(url_for("cliente", cliente_id=novo_id))
        status_http = 422
    else:
        dados = dict(atual) if atual else {}

    historico = []
    if atual:
        historico = conn.execute(
            """SELECT id, data_venda, data_entrega, valor_total, status FROM vendas
               WHERE cliente_id = ? ORDER BY id DESC""", (atual["id"],)).fetchall()
    return render_template("admin/cliente_form.html", cliente=atual, dados=dados,
                           erros=erros, historico=historico), status_http


@app.route("/admin/clientes/<int:cliente_id>/excluir", methods=["POST"])
def cliente_excluir(cliente_id):
    conn = get_db()
    tem = conn.execute("SELECT COUNT(*) FROM vendas WHERE cliente_id = ?",
                       (cliente_id,)).fetchone()[0]
    if tem:
        flash("Esse cliente tem orçamentos/pedidos e não pode ser excluído.", "erro")
        return redirect(url_for("cliente", cliente_id=cliente_id))
    conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    flash("Cliente excluído.", "ok")
    return redirect(url_for("clientes"))


# ==========================================================================
# PAINEL — produtos
# ==========================================================================


@app.route("/admin/produtos")
def produtos():
    lista = get_db().execute(
        """SELECT id, nome, categoria, unidade_venda, quantidade_minima, preco_unitario,
                  custo_producao, ativo FROM produtos
           ORDER BY ativo DESC, categoria, nome COLLATE NOCASE""").fetchall()
    return render_template("admin/produtos.html", lista=lista)


@app.route("/admin/produtos/novo", methods=["GET", "POST"])
@app.route("/admin/produtos/<int:produto_id>", methods=["GET", "POST"])
def produto(produto_id=None):
    conn = get_db()
    atual = None
    if produto_id:
        atual = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if atual is None:
            abort(404)
    categorias = [r[0] for r in conn.execute(
        "SELECT DISTINCT categoria FROM produtos WHERE categoria IS NOT NULL ORDER BY 1")]

    erros, status_http = [], 200
    if request.method == "POST":
        f = request.form
        dados = {c: f.get(c, "").strip()[:n] for c, n in (
            ("nome", 120), ("descricao", 500), ("categoria", 60), ("unidade_venda", 10),
            ("quantidade_minima", 8), ("preco_unitario", 14), ("custo_producao", 14),
            ("imagem", 120))}
        dados["ativo"] = "1" if f.get("ativo") else ""
        if not dados["nome"]:
            erros.append("Informe o nome do produto.")
        if dados["unidade_venda"] not in UNIDADES:
            erros.append("Escolha como o produto é vendido.")
        minimo = parse_int(dados["quantidade_minima"], 1, 100000)
        preco, custo = parse_dinheiro(dados["preco_unitario"]), parse_dinheiro(dados["custo_producao"])
        if minimo is None:
            erros.append("Pedido mínimo inválido (use 1 ou mais).")
        if preco is None:
            erros.append("Preço inválido.")
        if custo is None:
            erros.append("Custo inválido (pode ser 0,00).")
        imagem = None
        if dados["imagem"]:
            imagem = secure_filename(dados["imagem"])
            if not imagem.lower().endswith(EXTENSOES_IMAGEM):
                erros.append("Imagem: use um arquivo .jpg, .png ou .webp.")
        if not erros:
            valores = (dados["nome"], dados["descricao"] or None, dados["categoria"] or None,
                       dados["unidade_venda"], minimo, float(preco), float(custo), imagem,
                       1 if dados["ativo"] else 0)
            if atual:
                conn.execute("""UPDATE produtos SET nome = ?, descricao = ?, categoria = ?,
                                unidade_venda = ?, quantidade_minima = ?, preco_unitario = ?,
                                custo_producao = ?, imagem = ?, ativo = ? WHERE id = ?""",
                             valores + (atual["id"],))
            else:
                conn.execute("""INSERT INTO produtos (nome, descricao, categoria, unidade_venda,
                                quantidade_minima, preco_unitario, custo_producao, imagem, ativo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", valores)
            conn.commit()
            flash("Produto salvo.", "ok")
            return redirect(url_for("produtos"))
        status_http = 422
    elif atual:
        dados = {"nome": atual["nome"], "descricao": atual["descricao"] or "",
                 "categoria": atual["categoria"] or "", "unidade_venda": atual["unidade_venda"],
                 "quantidade_minima": str(atual["quantidade_minima"]),
                 "preco_unitario": num_br(atual["preco_unitario"]),
                 "custo_producao": num_br(atual["custo_producao"]),
                 "imagem": atual["imagem"] or "", "ativo": "1" if atual["ativo"] else ""}
    else:
        dados = {"nome": "", "descricao": "", "categoria": "", "unidade_venda": "unidade",
                 "quantidade_minima": str(NEGOCIO["pedido_minimo"]), "preco_unitario": "",
                 "custo_producao": "", "imagem": "", "ativo": "1"}
    return render_template("admin/produto_form.html", produto=atual, dados=dados,
                           erros=erros, categorias=categorias), status_http


@app.route("/admin/produtos/<int:produto_id>/alternar", methods=["POST"])
def produto_alternar(produto_id):
    conn = get_db()
    conn.execute("UPDATE produtos SET ativo = 1 - ativo WHERE id = ?", (produto_id,))
    conn.commit()
    return redirect(url_for("produtos"))


# ==========================================================================
# ERROS
# ==========================================================================


@app.errorhandler(400)
def erro_400(_e):
    return render_template("erro.html", codigo=400, titulo="Não foi possível concluir",
                           mensagem="A página expirou. Volte, atualize e tente novamente."), 400


@app.errorhandler(404)
def erro_404(_e):
    return render_template("erro.html", codigo=404, titulo="Página não encontrada",
                           mensagem="Esse endereço não existe."), 404


@app.errorhandler(500)
def erro_500(_e):
    return render_template("erro.html", codigo=500, titulo="Algo deu errado",
                           mensagem="Tente de novo em instantes."), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
