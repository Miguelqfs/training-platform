# UC09 — Gerar relatório de acessos

**Objetivo:** obter estatísticas de eventos de uso de treinos em um período, em HTML ou PDF.
**Ator principal previsto:** Administrador; no protótipo qualquer cliente local pode chamar a API.
**Gatilho:** `GET /statistics/accesses?start=&end=&format=`.
**Pré-condições de sucesso:** API iniciada; parâmetros válidos.
**Requisitos:** RF21, RF22, RF23 (falha de geração).
**Implementação prevista:** [Miguel — guia Sprint 4](../sprint4/miguel-relatorio.md).

> A API não autentica clientes. O relatório agrega eventos pelo **proprietário do treino**
> registrado nas operações, não por identidade do chamador.

## Fluxo principal

1. O ator informa `start` e `end` em RFC 3339 com fuso explícito e `format` (`html` ou `pdf`).
2. A fronteira valida tipos e delega à fachada.
3. O serviço de relatório normaliza o intervalo a UTC semiaberto `[start, end)`.
4. O repositório de eventos lista ocorrências no período.
5. O Template Method agrega total, contagens por usuário (ID crescente) e por operação.
6. O renderizador produz HTML ou PDF; a API retorna 200 com o tipo de conteúdo correspondente.

## Alternativas e exceções

- **A1 — período sem eventos (5–6):** total zero, sem usuários listados, quatro operações com contagem zero.
- **A2 — parâmetros inválidos (1–2):** início não anterior ao fim, instante sem fuso ou formato diferente de `html`/`pdf` → 422.
- **E1 — leitura ou renderização (3–6):** 503 com mensagem genérica, sem detalhes internos.

**Pós-condição de sucesso:** relatório reflete eventos já persistidos; **nenhum evento novo** é criado por esta operação.

**Garantia:** consulta de relatório não altera treinos nem eventos existentes.

[Delta normativo](../../openspec/changes/relatorio-de-acessos/specs/relatorio-de-acessos/spec.md) · [Índice](README.md)
