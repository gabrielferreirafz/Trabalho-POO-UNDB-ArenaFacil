// Estado apenas da interface. As regras são revalidadas pela API.
const $ = (id) => document.getElementById(id);
const esportes = {
  FUTEVOLEI: "Futevôlei",
  VOLEI: "Vôlei",
  BEACH_TENIS: "Beach tênis",
};
let usuario = null;
let cadastro = false;
let arenaAtual = null;
let quadrasAtuais = [];
let reservasAtuais = [];
let quadraEditando = null;
let confirmarAcao = null;
let versaoHorarios = 0;

function escapar(valor) {
  return String(valor ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
}

function dinheiro(valor) {
  return Number(valor).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function agoraFortaleza() {
  // ISO local, independente do fuso configurado no computador do visitante.
  const partes = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "America/Fortaleza",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).format(new Date());
  return partes.replace(" ", "T");
}

function dataBonita(inicio) {
  const [ano, mes, dia] = inicio.slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}

function periodo(inicio) {
  const hora = Number(inicio.slice(11, 13));
  return `${String(hora).padStart(2, "0")}:00 – ${String(hora + 1).padStart(2, "0")}:00`;
}

function avisar(texto, erro = false) {
  $("mensagem").textContent = texto;
  $("mensagem").className = erro ? "error" : "";
  $("mensagem").hidden = false;
  $("mensagem").scrollIntoView({ block: "nearest" });
}

async function api(caminho, metodo = "GET", dados) {
  const headers = {};
  if (usuario) headers["X-Usuario-Id"] = String(usuario.id);
  if (dados !== undefined) headers["Content-Type"] = "application/json";
  let resposta;
  try {
    resposta = await fetch(`/api${caminho}`, {
      method: metodo,
      headers,
      body: dados === undefined ? undefined : JSON.stringify(dados),
    });
  } catch {
    throw new Error(
      "Não foi possível conectar à API. Confira se o servidor está em execução.",
    );
  }
  const resultado = await resposta.json();
  if (!resposta.ok)
    throw new Error(
      resultado.detail || "Não foi possível concluir a operação.",
    );
  return resultado;
}

function tratar(acao) {
  // Os eventos não deixam rejeições de Promise sem mensagem na tela.
  return async (evento) => {
    try {
      await acao(evento);
    } catch (erro) {
      avisar(erro.message, true);
    }
  };
}

function tela(nome) {
  versaoHorarios++;
  document.querySelectorAll(".screen").forEach((secao) => {
    secao.hidden = secao.id !== `tela-${nome}`;
  });
  $("mensagem").hidden = true;
  $("nav-principal").classList.toggle(
    "active",
    ["arenas", "arena", "dono"].includes(nome),
  );
  $("nav-reservas").classList.toggle("active", nome === "reservas");
  window.scrollTo(0, 0);
}

function vazio(titulo, descricao) {
  return `<div class="empty"><h3>${escapar(titulo)}</h3><p>${escapar(descricao)}</p></div>`;
}

function configurarEntrada(criar) {
  cadastro = criar;
  $("aba-entrar").classList.toggle("active", !criar);
  $("aba-cadastrar").classList.toggle("active", criar);
  $("campos-cadastro").hidden = !criar;
  $("form-entrada").elements.nome.required = criar;
  $("titulo-entrada").textContent = criar
    ? "Entre para o jogo."
    : "Vamos jogar?";
  $("subtitulo-entrada").textContent = criar
    ? "Um cadastro simples para começar."
    : "Entre com seu e-mail cadastrado.";
  $("botao-entrada").textContent = criar
    ? "Criar minha conta ↗"
    : "Entrar na arena ↗";
  configurarPerfil();
}

function configurarPerfil() {
  const dono = cadastro && $("form-entrada").elements.perfil.value === "DONO";
  $("campos-arena").hidden = !dono;
  $("campos-arena").disabled = !dono;
  ["arena_nome", "endereco", "abertura", "fechamento"].forEach((campo) => {
    $("form-entrada").elements[campo].required = dono;
  });
  // Campos ocultos não devem bloquear a validação HTML do formulário de entrada.
  $("form-entrada").elements.nome.disabled = !cadastro;
}

async function iniciarUsuario(dados) {
  usuario = dados;
  sessionStorage.setItem("arena_usuario", String(dados.id));
  $("nome-usuario").textContent = dados.nome.split(" ")[0];
  $("conta").hidden = false;
  $("navegacao").hidden = false;
  $("etiqueta-inicial").hidden = true;
  const dono = usuario.perfil === "DONO";
  $("nav-principal").textContent = dono ? "Minha arena" : "Encontrar arenas";
  $("nav-reservas").textContent = dono
    ? "Reservas da arena"
    : "Minhas reservas";
  $("titulo-reservas").innerHTML = dono
    ? 'Os jogos da <span class="accent">sua arena.</span>'
    : 'Seus próximos <span class="accent">jogos.</span>';
  $("descricao-reservas").textContent = dono
    ? "Acompanhe as reservas das suas quadras."
    : "Consulte suas reservas e relembre os jogos anteriores.";
  await abrirPrincipal();
}

async function abrirPrincipal() {
  if (usuario.perfil === "DONO") return abrirDono();
  tela("arenas");
  await buscarArenas();
}

async function buscarArenas() {
  $("lista-arenas").innerHTML = vazio("Buscando arenas…", "Só um instante.");
  const arenas = await api(
    `/arenas?nome=${encodeURIComponent($("busca").value)}`,
  );
  $("total-arenas").textContent =
    `${arenas.length} ${arenas.length === 1 ? "arena encontrada" : "arenas encontradas"}`;
  $("lista-arenas").innerHTML = arenas.length
    ? arenas
        .map(
          (arena, indice) => `
    <article class="card">
      <div class="card-mark"><span>ARENA / ${String(indice + 1).padStart(2, "0")}</span><span aria-hidden="true">↗</span></div>
      <div class="card-body"><h3>${escapar(arena.nome)}</h3><p>${escapar(arena.endereco)}</p><p>Todos os dias · ${arena.abertura.slice(0, 5)} às ${arena.fechamento.slice(0, 5)}</p></div>
      <div class="card-bottom"><span class="muted small">Seu lugar na areia</span><button type="button" class="secondary" data-arena="${arena.id}">Ver quadras ↗</button></div>
    </article>`,
        )
        .join("")
    : vazio(
        "Nenhuma arena por aqui ainda.",
        "Tente outro nome ou cadastre um dono com sua arena para começar.",
      );
}

async function abrirArena(id) {
  const [arena, quadras] = await Promise.all([
    api(`/arenas/${id}`),
    api(`/arenas/${id}/quadras`),
  ]);
  arenaAtual = arena;
  quadrasAtuais = quadras;
  $("arena-nome").textContent = arena.nome;
  $("arena-dados").textContent =
    `${arena.endereco} · Todos os dias, ${arena.abertura.slice(0, 5)} às ${arena.fechamento.slice(0, 5)}`;
  $("data-jogo").min = agoraFortaleza().slice(0, 10);
  $("data-jogo").value = $("data-jogo").min;
  $("modalidade-jogo").value = "";
  tela("arena");
  await mostrarQuadras();
}

async function mostrarQuadras() {
  const versao = ++versaoHorarios;
  const filtro = $("modalidade-jogo").value;
  const quadras = quadrasAtuais.filter(
    (q) => !filtro || q.modalidades.includes(filtro),
  );
  $("lista-quadras").innerHTML = quadras.length
    ? quadras
        .map(
          (q) => `
    <article class="card">
      <div class="card-body"><h3>${escapar(q.nome)}</h3><p>${escapar(q.descricao || "Seu espaço para o próximo jogo.")}</p><div class="price">${dinheiro(q.preco_hora)} <small>/ hora</small></div>
      <label style="margin-top:20px">Modalidade<select data-esporte-quadra="${q.id}">${q.modalidades.map((m) => `<option value="${m}" ${m === filtro ? "selected" : ""}>${esportes[m]}</option>`).join("")}</select></label></div>
      <div class="availability"><span class="eyebrow">HORÁRIOS DISPONÍVEIS</span><div class="slots" id="horarios-${q.id}"><p class="muted">Consultando…</p></div></div>
    </article>`,
        )
        .join("")
    : vazio(
        "Nenhuma quadra disponível.",
        "Esta arena ainda não possui quadras ativas para a modalidade selecionada.",
      );
  await Promise.all(quadras.map((q) => carregarHorarios(q.id, versao)));
}

async function carregarHorarios(id, versao = versaoHorarios) {
  const local = $(`horarios-${id}`);
  const modalidade = document.querySelector(
    `[data-esporte-quadra="${id}"]`,
  ).value;
  const data = $("data-jogo").value;
  if (!data) {
    local.innerHTML = '<p class="muted">Selecione uma data.</p>';
    return;
  }
  local.innerHTML = '<p class="muted">Consultando…</p>';
  try {
    const dados = await api(
      `/quadras/${id}/disponibilidade?data=${encodeURIComponent(data)}&modalidade=${modalidade}`,
    );
    if (
      versao !== versaoHorarios ||
      !local.isConnected ||
      modalidade !==
        document.querySelector(`[data-esporte-quadra="${id}"]`)?.value ||
      data !== $("data-jogo").value
    )
      return;
    local.innerHTML = dados.horarios.length
      ? dados.horarios
          .map(
            (inicio) =>
              `<button type="button" class="slot" data-horario="${inicio}" data-quadra="${id}" data-modalidade="${modalidade}">${inicio.slice(11, 16)}</button>`,
          )
          .join("")
      : '<p class="muted">Sem horários livres para esta data.</p>';
  } catch (erro) {
    if (versao === versaoHorarios && local.isConnected)
      local.innerHTML = `<p class="inline-error">${escapar(erro.message)}</p>`;
  }
}

function abrirConfirmacao(titulo, resumo, textoBotao, acao) {
  $("titulo-confirmacao").textContent = titulo;
  $("resumo-confirmacao").innerHTML = resumo;
  $("confirmar-acao").textContent = textoBotao;
  $("erro-confirmacao").hidden = true;
  confirmarAcao = acao;
  $("dialog-confirmacao").showModal();
}

function resumo(linhas) {
  return linhas
    .map(
      ([nome, valor]) =>
        `<div class="summary-row"><span>${escapar(nome)}</span><span>${escapar(valor)}</span></div>`,
    )
    .join("");
}

function escolherHorario(botao) {
  const id = Number(botao.dataset.quadra);
  const inicio = botao.dataset.horario;
  const modalidade = botao.dataset.modalidade;
  const quadra = quadrasAtuais.find((q) => q.id === id);
  abrirConfirmacao(
    "Confirme seu jogo",
    resumo([
      ["Arena", arenaAtual.nome],
      ["Quadra", quadra.nome],
      ["Modalidade", esportes[modalidade]],
      ["Data", dataBonita(inicio)],
      ["Horário", `${periodo(inicio)} · Fortaleza`],
      ["Total · 1 hora", dinheiro(quadra.preco_hora)],
    ]) +
      '<p class="muted small" style="margin-top:18px">Cancelamento com pelo menos duas horas de antecedência. A confirmação é imediata.</p>',
    "Confirmar reserva ↗",
    async () => {
      try {
        await api("/agendamentos", "POST", {
          quadra_id: id,
          modalidade,
          inicio,
        });
      } catch (erro) {
        await mostrarQuadras();
        throw erro;
      }
      $("dialog-confirmacao").close();
      await abrirReservas();
      avisar("Jogo marcado! Sua reserva foi confirmada.");
    },
  );
}

async function abrirDono() {
  const [arena, quadras] = await Promise.all([
    api("/dono/arena"),
    api("/dono/quadras"),
  ]);
  arenaAtual = arena;
  quadrasAtuais = quadras;
  $("dono-arena-nome").textContent = arena.nome;
  $("dono-arena-dados").textContent =
    `${arena.endereco} · Todos os dias, ${arena.abertura.slice(0, 5)} às ${arena.fechamento.slice(0, 5)}`;
  tela("dono");
  $("quadras-dono").innerHTML = quadras.length
    ? quadras
        .map(
          (q) => `
    <article class="card ${q.ativa ? "" : "inactive"}"><div class="card-mark"><span>${q.ativa ? "QUADRA ATIVA" : "QUADRA DESATIVADA"}</span><span aria-hidden="true">↗</span></div>
    <div class="card-body"><h3>${escapar(q.nome)}</h3><p>${escapar(q.descricao || "Sem descrição.")}</p><div class="price">${dinheiro(q.preco_hora)} <small>/ hora</small></div><div class="tags">${q.modalidades.map((m) => `<span class="tag">${esportes[m]}</span>`).join("")}</div></div>
    <div class="card-bottom">${q.ativa ? `<div class="card-actions"><button class="text-button" type="button" data-editar="${q.id}">Editar quadra</button><button class="text-button danger" type="button" data-excluir="${q.id}">Excluir</button></div>` : '<span class="muted small">Histórico preservado</span>'}</div></article>`,
        )
        .join("")
    : vazio(
        "Sua primeira quadra começa aqui.",
        "Clique em “Nova quadra” para disponibilizar horários para os clientes.",
      );
}

function formularioQuadra(id = null) {
  quadraEditando = id;
  const form = $("form-quadra");
  form.reset();
  $("erro-quadra").hidden = true;
  $("titulo-quadra").textContent = id ? "Editar quadra" : "Nova quadra";
  if (id) {
    const q = quadrasAtuais.find((q) => q.id === id);
    ["nome", "descricao", "preco_hora"].forEach((campo) => {
      form.elements[campo].value = q[campo] || "";
    });
    form.querySelectorAll('[name="modalidades"]').forEach((input) => {
      input.checked = q.modalidades.includes(input.value);
    });
  }
  $("dialog-quadra").showModal();
}

function excluirQuadra(id) {
  const quadra = quadrasAtuais.find((q) => q.id === id);
  abrirConfirmacao(
    "Excluir quadra?",
    `<p>${escapar(quadra.nome)}</p><p class="muted">Se houver histórico, a quadra será desativada. Reservas futuras confirmadas impedem a exclusão.</p>`,
    "Excluir quadra",
    async () => {
      const resultado = await api(`/quadras/${id}`, "DELETE");
      $("dialog-confirmacao").close();
      await abrirDono();
      avisar(resultado.mensagem);
    },
  );
}

async function abrirReservas() {
  reservasAtuais = await api("/agendamentos");
  tela("reservas");
  mostrarReservas();
}

function podeCancelar(reserva) {
  // Acrescentar Z apenas para calcular a diferença entre dois horários locais.
  return (
    usuario.perfil === "CLIENTE" &&
    reserva.status === "CONFIRMADO" &&
    new Date(`${reserva.inicio}Z`) - new Date(`${agoraFortaleza()}Z`) >= 7200000
  );
}

function mostrarReservas() {
  const agora = agoraFortaleza();
  const filtro = $("filtro-reservas").value;
  const data = $("data-reservas").value;
  const reservas = reservasAtuais.filter((r) => {
    const futura = r.status === "CONFIRMADO" && r.inicio > agora;
    return (
      (filtro === "todas" || (filtro === "proximas" ? futura : !futura)) &&
      (!data || r.inicio.startsWith(data))
    );
  });
  if (filtro === "proximas")
    reservas.sort((a, b) => a.inicio.localeCompare(b.inicio));
  $("lista-reservas").innerHTML = reservas.length
    ? reservas
        .map(
          (r) => `
    <article class="reservation"><div class="date-box"><strong>${r.inicio.slice(8, 10)}</strong><span>${r.inicio.slice(5, 7)} / ${r.inicio.slice(0, 4)}</span></div>
      <div class="reservation-info"><h3>${escapar(r.arena_nome)} · ${escapar(r.quadra_nome)}</h3><p>${esportes[r.modalidade]} · ${periodo(r.inicio)} · Fortaleza</p><p>${usuario.perfil === "DONO" ? `Cliente: ${escapar(r.cliente_nome)}` : escapar(r.endereco)}</p></div>
      <div class="reservation-end"><div class="price">${dinheiro(r.preco_reservado)}</div><span class="status ${r.status === "CANCELADO" ? "cancelled" : ""}">${r.status === "CANCELADO" ? "Cancelada" : r.inicio > agora ? "Confirmada" : "No histórico"}</span>
      ${podeCancelar(r) ? `<button type="button" class="text-button danger" data-cancelar="${r.id}">Cancelar reserva</button>` : usuario.perfil === "CLIENTE" && r.status === "CONFIRMADO" && r.inicio > agora ? '<div class="cancellation-note">Prazo de cancelamento encerrado.</div>' : ""}</div>
    </article>`,
        )
        .join("")
    : vazio(
        "Nenhuma reserva nesta seleção.",
        usuario.perfil === "CLIENTE"
          ? "Encontre uma arena e marque seu próximo jogo."
          : "Os agendamentos dos clientes aparecerão aqui.",
      );
}

function cancelarReserva(id) {
  const r = reservasAtuais.find((reserva) => reserva.id === id);
  abrirConfirmacao(
    "Cancelar este jogo?",
    resumo([
      ["Quadra", r.quadra_nome],
      ["Data", dataBonita(r.inicio)],
      ["Horário", periodo(r.inicio)],
    ]),
    "Cancelar reserva",
    async () => {
      await api(`/agendamentos/${id}/cancelar`, "POST");
      $("dialog-confirmacao").close();
      await abrirReservas();
      avisar("Reserva cancelada. O horário voltou a ficar disponível.");
    },
  );
}

$("aba-entrar").onclick = () => configurarEntrada(false);
$("aba-cadastrar").onclick = () => configurarEntrada(true);
$("form-entrada").elements.perfil.onchange = configurarPerfil;
$("form-entrada").onsubmit = async (evento) => {
  evento.preventDefault();
  const botao = $("botao-entrada");
  botao.disabled = true;
  try {
    const form = new FormData(evento.currentTarget);
    const dados = { email: form.get("email") };
    let caminho = "/entrada";
    if (cadastro) {
      dados.nome = form.get("nome");
      const dono = form.get("perfil") === "DONO";
      caminho = dono ? "/donos" : "/clientes";
      if (dono)
        ["arena_nome", "endereco", "abertura", "fechamento"].forEach(
          (campo) => {
            dados[campo] = form.get(campo);
          },
        );
    }
    await iniciarUsuario(await api(caminho, "POST", dados));
    $("form-entrada").reset();
  } catch (erro) {
    avisar(erro.message, true);
  } finally {
    botao.disabled = false;
  }
};

$("sair").onclick = () => {
  usuario = null;
  sessionStorage.removeItem("arena_usuario");
  $("conta").hidden = true;
  $("navegacao").hidden = true;
  $("etiqueta-inicial").hidden = false;
  $("form-entrada").reset();
  $("busca").value = "";
  $("filtro-reservas").value = "proximas";
  $("data-reservas").value = "";
  configurarEntrada(false);
  tela("entrada");
};
$("nav-principal").onclick = tratar(abrirPrincipal);
$("nav-reservas").onclick = tratar(abrirReservas);
$("voltar-arenas").onclick = tratar(abrirPrincipal);
$("form-busca").onsubmit = tratar(async (e) => {
  e.preventDefault();
  await buscarArenas();
});
$("lista-arenas").onclick = tratar(async (e) => {
  const b = e.target.closest("[data-arena]");
  if (b) await abrirArena(Number(b.dataset.arena));
});
$("data-jogo").onchange = tratar(mostrarQuadras);
$("modalidade-jogo").onchange = tratar(mostrarQuadras);
$("lista-quadras").onchange = tratar(async (e) => {
  if (e.target.dataset.esporteQuadra)
    await carregarHorarios(Number(e.target.dataset.esporteQuadra));
});
$("lista-quadras").onclick = (e) => {
  const b = e.target.closest("[data-horario]");
  if (b) escolherHorario(b);
};
$("nova-quadra").onclick = () => formularioQuadra();
$("quadras-dono").onclick = (e) => {
  const editar = e.target.closest("[data-editar]");
  const excluir = e.target.closest("[data-excluir]");
  if (editar) formularioQuadra(Number(editar.dataset.editar));
  if (excluir) excluirQuadra(Number(excluir.dataset.excluir));
};
$("form-quadra").onsubmit = async (e) => {
  e.preventDefault();
  const botao = e.currentTarget.querySelector('[type="submit"]');
  botao.disabled = true;
  try {
    const f = new FormData(e.currentTarget);
    const modalidades = f.getAll("modalidades");
    if (!modalidades.length)
      throw new Error("Escolha pelo menos uma modalidade.");
    await api(
      quadraEditando ? `/quadras/${quadraEditando}` : "/quadras",
      quadraEditando ? "PUT" : "POST",
      {
        nome: f.get("nome"),
        descricao: f.get("descricao"),
        preco_hora: f.get("preco_hora"),
        modalidades,
      },
    );
    $("dialog-quadra").close();
    await abrirDono();
    avisar("Quadra salva com sucesso.");
  } catch (erro) {
    $("erro-quadra").textContent = erro.message;
    $("erro-quadra").hidden = false;
  } finally {
    botao.disabled = false;
  }
};
$("confirmar-acao").onclick = async () => {
  $("confirmar-acao").disabled = true;
  try {
    await confirmarAcao();
  } catch (erro) {
    $("erro-confirmacao").textContent = erro.message;
    $("erro-confirmacao").hidden = false;
  } finally {
    $("confirmar-acao").disabled = false;
  }
};
document.querySelectorAll(".close-dialog").forEach((b) => {
  b.onclick = () => b.closest("dialog").close();
});
$("filtro-reservas").onchange = mostrarReservas;
$("lista-reservas").onclick = (e) => {
  const botao = e.target.closest("[data-cancelar]");
  if (botao) cancelarReserva(Number(botao.dataset.cancelar));
};
$("data-reservas").onchange = mostrarReservas;
$("limpar-data").onclick = () => {
  $("data-reservas").value = "";
  mostrarReservas();
};

async function restaurarSessao() {
  configurarEntrada(false);
  const id = sessionStorage.getItem("arena_usuario");
  if (!id) return;
  usuario = { id };
  try {
    await iniciarUsuario(await api("/usuarios/eu"));
  } catch (erro) {
    $("sair").click();
    avisar(erro.message, true);
  }
}
restaurarSessao();
