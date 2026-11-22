/* Painel: confirmações, cópia de texto e cálculo do formulário de pedido. */
(function () {
  'use strict';

  var moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  function brl(v) { return moeda.format(v).replace(/ /g, ' '); }
  function $(sel, raiz) { return (raiz || document).querySelector(sel); }
  function $$(sel, raiz) { return Array.prototype.slice.call((raiz || document).querySelectorAll(sel)); }

  /* Aceita "15", "15,50", "1.234,56" */
  function numero(texto) {
    var s = String(texto || '').replace(/R\$|\s/g, '');
    if (!s) { return 0; }
    if (s.indexOf(',') !== -1) { s = s.replace(/\./g, '').replace(',', '.'); }
    else if (/^\d{1,3}(\.\d{3})+$/.test(s)) { s = s.replace(/\./g, ''); }
    var n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }

  /* Pede confirmação antes de enviar formulários perigosos */
  document.addEventListener('submit', function (ev) {
    var msg = ev.target.getAttribute('data-confirmar');
    if (msg && !window.confirm(msg)) { ev.preventDefault(); }
  });

  /* Copiar texto do orçamento */
  document.addEventListener('click', function (ev) {
    var botao = ev.target.closest('[data-copiar]');
    if (!botao) { return; }
    var alvo = $(botao.getAttribute('data-copiar'));
    if (!alvo) { return; }
    var original = botao.textContent;
    function pronto() { botao.textContent = 'Copiado!'; setTimeout(function () { botao.textContent = original; }, 1600); }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(alvo.value).then(pronto);
    } else {
      alvo.select(); document.execCommand('copy'); pronto();
    }
  });

  /* Formulário de pedido */
  var form = $('[data-form-pedido]');
  if (!form) { return; }
  var lista = $('[data-itens]', form);

  function recalcular() {
    var total = 0, receita = 0, custo = 0;
    $$('[data-item]', lista).forEach(function (linha) {
      var qtd = parseInt($('[data-qtd]', linha).value, 10) || 0;
      var preco = numero($('[data-preco]', linha).value);
      var sub = qtd * preco;
      $('[data-sub]', linha).textContent = brl(sub);
      total += sub;
      if ($('[data-produto]', linha).value) {
        receita += sub;
        custo += qtd * numero($('[data-custo]', linha).value);
      }
    });
    $('[data-total]', form).textContent = brl(total);
    $('[data-margem]', form).textContent = receita > 0
      ? Math.round((receita - custo) / receita * 100) + '%  (lucro ' + brl(receita - custo) + ')'
      : '—';
  }

  function virgula(n) { return String(n).replace('.', ','); }

  lista.addEventListener('change', function (ev) {
    var campo = ev.target;
    if (!campo.matches('[data-produto]')) { return; }
    var linha = campo.closest('[data-item]');
    var opcao = campo.options[campo.selectedIndex];
    if (campo.value) {
      $('[data-desc]', linha).value = opcao.getAttribute('data-op-nome');
      $('[data-preco]', linha).value = opcao.getAttribute('data-op-preco');
      $('[data-custo]', linha).value = opcao.getAttribute('data-op-custo');
      var qtd = $('[data-qtd]', linha);
      if (!qtd.value) { qtd.value = opcao.getAttribute('data-op-min') || '1'; }
    } else {
      $('[data-custo]', linha).value = virgula(0);
    }
    recalcular();
  });

  lista.addEventListener('input', recalcular);

  lista.addEventListener('click', function (ev) {
    var remover = ev.target.closest('[data-remover-item]');
    if (!remover) { return; }
    var linhas = $$('[data-item]', lista);
    var linha = remover.closest('[data-item]');
    if (linhas.length === 1) {                       // última linha: só limpa
      $$('input[type="text"]', linha).forEach(function (i) { i.value = ''; });
      $('[data-custo]', linha).value = '';
      $('[data-produto]', linha).value = '';
    } else {
      linha.remove();
    }
    recalcular();
  });

  $('[data-add-item]', form).addEventListener('click', function () {
    var modelo = document.getElementById('linha-modelo');
    lista.appendChild(modelo.content.cloneNode(true));
    var linhas = $$('[data-item]', lista);
    $('[data-produto]', linhas[linhas.length - 1]).focus();
    recalcular();
  });

  recalcular();
}());
