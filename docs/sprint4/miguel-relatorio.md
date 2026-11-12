# Miguel — relatório (Template Method) e API

Referências: [design](../../openspec/changes/relatorio-de-acessos/design.md) (contrato HTTP e agregação), [spec delta](../../openspec/changes/relatorio-de-acessos/specs/relatorio-de-acessos/spec.md), [UC09](../04-casos-de-uso/UC09-gerar-relatorio-acessos.md), [ADR 0008](../adr/0008-relatorio-template-method.md).

Implementado neste PR sobre `develop`, após a integração do registro de Luigi (#21).
O arquivamento da change e a release permanecem no fechamento do Rafael.

**Pré-requisito:** eventos persistidos nas operações de treino (PR do Luigi).

## Escopo do PR

- **3.1:** agregação + Template Method na camada de negócio.
- **3.2:** renderizadores HTML e PDF (mesmos dados).
- **3.3:** fachada + `GET /statistics/accesses` — **tasks.md 1.1** (contratos públicos) no mesmo PR.

## HTTP

```
GET /statistics/accesses?start=<RFC3339>&end=<RFC3339>&format=html|pdf
```

- `start` e `end` obrigatórios, fuso explícito, normalizados a UTC; `start` < `end` (mesma regra que [`interval()`](../../app/accesses/domain.py)).
- `format` ∈ `html` | `pdf` apenas.
- 422 entrada inválida; 503 leitura ou renderização; 200 com `Content-Type` adequado.
- **Não** registrar evento de acesso para esta rota.

A rota está em [`app/routers/statistics.py`](../../app/routers/statistics.py).

## Agregação (única para os dois formatos)

1. Normalizar período (`interval`).
2. `repositories.accesses.list_between(start, end)` — intervalo **semiaberto** `[start, end)`.
3. Montar estrutura imutável com:
   - início e fim em UTC exibidos no relatório;
   - total de eventos;
   - contagens por `user_id` (ordenar ID crescente; omitir usuários sem evento no período);
   - contagens por operação na ordem `create`, `get`, `update`, `delete` (zero explícito).
4. Invariantes: soma por usuário = soma por operação = total.

Período vazio: total 0, sem usuários, quatro operações com 0.

## Template Method

- [`AccessReportTemplate`](../../app/reports/template.py): validar período → buscar uma vez → agregar → chamar `render(aggregated)`.
- [`HtmlAccessReport` e `PdfAccessReport`](../../app/reports/renderers.py) só implementam renderização.
- ReportLab (`reportlab>=4.4,<5`) gera PDF em memória com tabelas paginadas e fontes incorporadas; `pypdf` é usado apenas nos testes. Decisão no ADR 0008.

## Fachada e contexto

- `FacadeSingletonController.generate_access_report(context, request)` delega a `context.reports.generate(request)`.
- `create_app` compõe `AccessReportService` com os templates HTML/PDF e o repositório de eventos da aplicação.
- Não alterar `count_entities` (continua usuários + treinos, sem eventos).

## Testes mínimos

- Dois formatos, mesmo período: totais e tabelas equivalentes.
- Filtro de intervalo (inclui início, exclui fim).
- Período sem eventos.
- 422: período inválido, formato inválido.
- 503: falha simulada de repositório ou renderer.
- Garantir que chamar o relatório não aumenta eventos.

## Ao abrir o PR

- [x] Marcar `tasks.md` 3.1–3.3 e 1.1.
- [x] Completar [ADR 0008](../adr/0008-relatorio-template-method.md).
- [x] Atualizar README (tabela do endpoint e exemplos).
- [x] Base: `develop`.

Testes em [`test_access_reports.py`](../../tests/test_access_reports.py), incluindo
fluxo de eventos reais, equivalência dos formatos, falhas, OpenAPI e paginação.
