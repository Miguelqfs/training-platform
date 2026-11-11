# ADR 0008: Contratos públicos do relatório e Template Method

## Status

Proposto — **completar no PR de implementação (Miguel)**. Cobre **tasks.md 1.1** (contratos públicos de eventos/relatório na API) e **3.1–3.2**.

## Contexto

RF21–RF22 exigem relatório por período em HTML e PDF com agregação única.
O repositório de eventos é a fonte de leitura; a geração fica na camada de negócio.

## Decisão

- _(Participantes do Template Method: classe base, renderizadores HTML/PDF.)_
- _(Biblioteca PDF e justificativa.)_
- _(Contrato HTTP `GET /statistics/accesses` e códigos de erro.)_

## Consequências

- _(Dependências, testes de equivalência entre formatos.)_

## Alternativas consideradas

- _(Gerar formatos em camadas distintas com consultas separadas — rejeitado pelo design.)_
