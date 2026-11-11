# Miguel — relatório (Template Method) e API

Referências: [design](../../openspec/changes/relatorio-de-acessos/design.md) (contrato HTTP e agregação), [spec delta](../../openspec/changes/relatorio-de-acessos/specs/relatorio-de-acessos/spec.md), [UC09](../04-casos-de-uso/UC09-gerar-relatorio-acessos.md), esboço [ADR 0008](../adr/0008-relatorio-template-method.md).

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

Sugestão de rota: estender [`app/routers/statistics.py`](../../app/routers/statistics.py) (prefixo já é `/statistics`).

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

- Classe base (ex. em `app/accesses/` ou `app/reports/`) com fluxo: validar período → buscar → agregar → chamar `render(aggregated)`.
- Subclasses `Html…` e `Pdf…` só implementam renderização.
- Escolha da biblioteca PDF documentada no ADR 0008 e no README da sprint.

## Fachada e contexto

- Novo método em `FacadeSingletonController` delegando ao serviço de relatório do `ApplicationContext`.
- Registrar o serviço em `create_app` junto a `UserService` / `WorkoutService`.
- Não alterar `count_entities` (continua usuários + treinos, sem eventos).

## Testes mínimos

- Dois formatos, mesmo período: totais e tabelas equivalentes.
- Filtro de intervalo (inclui início, exclui fim).
- Período sem eventos.
- 422: período inválido, formato inválido.
- 503: falha simulada de repositório ou renderer.
- Garantir que chamar o relatório não aumenta eventos.

## Ao abrir o PR

- [ ] Marcar `tasks.md` 3.1–3.3 e 1.1 se aplicável.
- [ ] Completar [ADR 0008](../adr/0008-relatorio-template-method.md).
- [ ] Atualizar README (tabela do endpoint) — ou avisar Rafael para o passo único pós-merge.
- [ ] Base: `develop`.
