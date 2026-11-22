/* Lista de orçamento: o cliente monta a lista e envia pelo WhatsApp.
   Nada é enviado para o servidor; a lista fica só no navegador. */
(function () {
  'use strict';

  var CHAVE = 'vd_orcamento_v1';
  var PLURAL = { unidade: ['unidade', 'unidades'], cento: ['cento', 'centos'], kit: ['kit', 'kits'] };
  var moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

  var produtos = {};   // id -> { id, nome, preco, minimo, unidade, el }
  var itens = {};      // id -> quantidade
  var campos = { empresa: '', contato: '', data: '', obs: '' };

  var dlg = document.getElementById('orcamento');
  var form = dlg && dlg.querySelector('[data-form-orcamento]');

  function $(sel, raiz) { return (raiz || document).querySelector(sel); }
  function $$(sel, raiz) { return Array.prototype.slice.call((raiz || document).querySelectorAll(sel)); }
  function dinheiro(v) { return moeda.format(v).replace(/ /g, ' '); }
  function rotulo(qtd, unidade) {
    var p = PLURAL[unidade] || PLURAL.unidade;
    return qtd + ' ' + (qtd === 1 ? p[0] : p[1]);
  }
  function inteiro(valor, minimo) {
    var n = parseInt(valor, 10);
    return isNaN(n) || n < minimo ? minimo : n;
  }

  /* ---------- persistência (light, por navegador) ---------- */
  function salvar() {
    try { localStorage.setItem(CHAVE, JSON.stringify({ itens: itens, campos: campos })); } catch (e) { /* ignora */ }
  }
  function carregar() {
    try {
      var salvo = JSON.parse(localStorage.getItem(CHAVE) || 'null');
      if (!salvo) { return; }
      Object.keys(salvo.itens || {}).forEach(function (id) {
        var p = produtos[id];
        if (p) { itens[id] = inteiro(salvo.itens[id], p.minimo); }
      });
      ['empresa', 'contato', 'data', 'obs'].forEach(function (c) {
        campos[c] = String((salvo.campos || {})[c] || '');
      });
    } catch (e) { /* ignora */ }
  }

  /* ---------- cálculos ---------- */
  function ids() { return Object.keys(itens); }
  function total() {
    return ids().reduce(function (soma, id) { return soma + itens[id] * produtos[id].preco; }, 0);
  }

  /* ---------- catálogo ---------- */
  function atualizarCards() {
    Object.keys(produtos).forEach(function (id) {
      var p = produtos[id];
      var estado = $('[data-estado]', p.el);
      var botao = $('[data-adicionar]', p.el);
      var no = itens[id] !== undefined;
      p.el.classList.toggle('no-orcamento', no);
      estado.hidden = !no;
      estado.textContent = no ? 'No orçamento: ' + rotulo(itens[id], p.unidade) : '';
      botao.textContent = no ? 'Atualizar' : 'Adicionar';
      if (no) { $('[data-quantidade]', p.el).value = itens[id]; }
    });
  }

  function atualizarBarra() {
    var n = ids().length;
    $$('[data-contador]').forEach(function (el) { el.textContent = n; });
    var barra = $('[data-barra]');
    barra.hidden = n === 0;
    $('[data-barra-itens]').textContent = n + (n === 1 ? ' item' : ' itens');
    $('[data-barra-total]').textContent = dinheiro(total());
  }

  /* ---------- janela do orçamento ---------- */
  function linhaItem(id) {
    var p = produtos[id];
    var li = document.createElement('li');
    li.dataset.id = id;

    var info = document.createElement('div');
    var nome = document.createElement('div');
    nome.className = 'item__nome';
    nome.textContent = p.nome;
    var preco = document.createElement('div');
    preco.className = 'item__preco';
    preco.textContent = dinheiro(p.preco) + ' / ' + PLURAL[p.unidade][0] + ' · mín. ' + rotulo(p.minimo, p.unidade);
    info.appendChild(nome);
    info.appendChild(preco);

    var sub = document.createElement('div');
    sub.className = 'item__sub';
    sub.textContent = dinheiro(itens[id] * p.preco);

    var controles = document.createElement('div');
    controles.className = 'item__controles';
    var q = document.createElement('div');
    q.className = 'quantidade';
    var menos = document.createElement('button');
    menos.type = 'button'; menos.textContent = '−'; menos.dataset.listaMenos = id;
    menos.setAttribute('aria-label', 'Diminuir a quantidade de ' + p.nome);
    var campo = document.createElement('input');
    campo.type = 'number'; campo.min = p.minimo; campo.step = 1; campo.value = itens[id];
    campo.dataset.listaQtd = id; campo.setAttribute('inputmode', 'numeric');
    campo.setAttribute('aria-label', 'Quantidade de ' + p.nome);
    var mais = document.createElement('button');
    mais.type = 'button'; mais.textContent = '+'; mais.dataset.listaMais = id;
    mais.setAttribute('aria-label', 'Aumentar a quantidade de ' + p.nome);
    q.appendChild(menos); q.appendChild(campo); q.appendChild(mais);
    var remover = document.createElement('button');
    remover.type = 'button'; remover.className = 'item__remover'; remover.textContent = 'Remover';
    remover.dataset.remover = id;
    remover.setAttribute('aria-label', 'Remover ' + p.nome + ' da lista');
    controles.appendChild(q); controles.appendChild(remover);

    li.appendChild(info); li.appendChild(sub); li.appendChild(controles);
    return li;
  }

  function renderizarLista() {
    var lista = $('[data-lista]', dlg);
    lista.textContent = '';
    ids().forEach(function (id) { lista.appendChild(linhaItem(id)); });
    var vazio = ids().length === 0;
    $('[data-vazio]', dlg).hidden = !vazio;
    $('[data-total-linha]', dlg).hidden = vazio;
    $('[data-total]', dlg).textContent = dinheiro(total());
    $('[data-enviar]', dlg).disabled = vazio;
  }

  function avisoPrazo() {
    var aviso = $('[data-aviso-prazo]', dlg);
    var valor = campos.data;
    if (!valor) { aviso.hidden = true; return; }
    var prazo = parseInt(dlg.dataset.prazo, 10) || 7;
    var hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    var partes = valor.split('-');
    var escolhida = new Date(+partes[0], +partes[1] - 1, +partes[2]);
    aviso.hidden = Math.round((escolhida - hoje) / 86400000) >= prazo;
  }

  function preencherCampos() {
    Object.keys(campos).forEach(function (c) {
      var el = $('[data-campo="' + c + '"]', dlg);
      if (el) { el.value = campos[c]; }
    });
    var data = $('[data-data]', dlg);
    var d = new Date();
    data.min = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
    avisoPrazo();
  }

  function abrir() {
    renderizarLista();
    preencherCampos();
    document.body.classList.add('modal-aberto');
    if (typeof dlg.showModal === 'function') { dlg.showModal(); } else { dlg.setAttribute('open', ''); }
  }
  function fechar() {
    if (typeof dlg.close === 'function') { dlg.close(); } else { dlg.removeAttribute('open'); }
    document.body.classList.remove('modal-aberto');
  }

  function mudou() { salvar(); atualizarCards(); atualizarBarra(); }

  function definirQtd(id, qtd) {
    var p = produtos[id];
    itens[id] = inteiro(qtd, p.minimo);
    mudou();
  }

  /* ---------- mensagem do WhatsApp ---------- */
  function dataBr(iso) {
    var p = iso.split('-');
    return p[2] + '/' + p[1] + '/' + p[0];
  }
  function montarMensagem() {
    var linhas = ['Olá! Gostaria de um orçamento da ' + dlg.dataset.negocio + '.', ''];
    linhas.push('Empresa: ' + campos.empresa.trim());
    linhas.push('Contato: ' + campos.contato.trim());
    if (campos.data) { linhas.push('Entrega desejada: ' + dataBr(campos.data)); }
    linhas.push('', 'Itens:');
    ids().forEach(function (id) {
      linhas.push('• ' + itens[id] + 'x ' + produtos[id].nome);
    });
    linhas.push('', 'Estimativa pela tabela: ' + dinheiro(total()));
    if (campos.obs.trim()) { linhas.push('', 'Observações: ' + campos.obs.trim()); }
    return linhas.join('\n');
  }
  function enviar() {
    var url = 'https://wa.me/' + dlg.dataset.whatsapp + '?text=' + encodeURIComponent(montarMensagem());
    var a = document.createElement('a');
    a.href = url; a.target = '_blank'; a.rel = 'noopener';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  }

  /* ---------- eventos ---------- */
  document.addEventListener('click', function (ev) {
    var alvo = ev.target.closest('button');
    if (!alvo) {
      if (ev.target === dlg) { fechar(); }   // clique no fundo escuro
      return;
    }
    var card = alvo.closest('[data-produto]');

    if (card && alvo.hasAttribute('data-menos')) {
      var qm = $('[data-quantidade]', card), pm = produtos[card.dataset.id];
      qm.value = Math.max(pm.minimo, inteiro(qm.value, pm.minimo) - 1);
    } else if (card && alvo.hasAttribute('data-mais')) {
      var qp = $('[data-quantidade]', card);
      qp.value = inteiro(qp.value, produtos[card.dataset.id].minimo) + 1;
    } else if (card && alvo.hasAttribute('data-adicionar')) {
      var qa = $('[data-quantidade]', card), pa = produtos[card.dataset.id];
      qa.value = inteiro(qa.value, pa.minimo);
      definirQtd(pa.id, qa.value);
    } else if (alvo.hasAttribute('data-abrir-orcamento')) {
      abrir();
    } else if (alvo.hasAttribute('data-fechar')) {
      fechar();
    } else if (alvo.hasAttribute('data-limpar')) {
      itens = {}; mudou(); renderizarLista();
    } else if (alvo.dataset.remover) {
      delete itens[alvo.dataset.remover]; mudou(); renderizarLista();
    } else if (alvo.dataset.listaMenos) {
      definirQtd(alvo.dataset.listaMenos, itens[alvo.dataset.listaMenos] - 1); renderizarLista();
    } else if (alvo.dataset.listaMais) {
      definirQtd(alvo.dataset.listaMais, itens[alvo.dataset.listaMais] + 1); renderizarLista();
    } else if (alvo.hasAttribute('data-categoria')) {
      var cat = alvo.dataset.categoria;
      $$('[data-categoria]').forEach(function (b) {
        var ativo = b === alvo;
        b.classList.toggle('is-ativo', ativo);
        b.setAttribute('aria-pressed', ativo ? 'true' : 'false');
      });
      $$('[data-secao]').forEach(function (s) { s.hidden = cat !== 'todas' && s.dataset.secao !== cat; });
    }
  });

  document.addEventListener('change', function (ev) {
    var campo = ev.target;
    if (campo.dataset && campo.dataset.listaQtd) {
      definirQtd(campo.dataset.listaQtd, campo.value); renderizarLista();
    } else if (campo.hasAttribute && campo.hasAttribute('data-quantidade')) {
      var p = produtos[campo.closest('[data-produto]').dataset.id];
      campo.value = inteiro(campo.value, p.minimo);
    }
  });

  if (dlg) {
    dlg.addEventListener('close', function () { document.body.classList.remove('modal-aberto'); });
    dlg.addEventListener('input', function (ev) {
      var nome = ev.target.getAttribute('data-campo');
      if (nome) {
        campos[nome] = ev.target.value;
        salvar();
        if (nome === 'data') { avisoPrazo(); }
      }
    });
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (ids().length) { enviar(); }
    });
  }

  /* ---------- início ---------- */
  $$('[data-produto]').forEach(function (el) {
    produtos[el.dataset.id] = {
      id: el.dataset.id, nome: el.dataset.nome, preco: parseFloat(el.dataset.preco),
      minimo: parseInt(el.dataset.minimo, 10) || 1, unidade: el.dataset.unidade, el: el
    };
  });
  carregar();
  atualizarCards();
  atualizarBarra();
}());
