# ADR 0007: Adapter para log auxiliar de eventos

## Status

Proposto — **completar no PR de implementação (Luigi)**.

## Contexto

Eventos de uso de treino são persistidos para relatório ([ADR 0006](0006-repository-factory.md)).
A change [relatorio-de-acessos](../../openspec/changes/relatorio-de-acessos/design.md) prevê log
auxiliar sem dados sensíveis, com falha que não altera a resposta da operação.

## Decisão

- _(Participantes: porta, Adapter, biblioteca escolhida.)_
- _(Campos logados: apenas identificador do proprietário, operação e instante UTC.)_
- _(Comportamento em falha: ….)_

## Consequências

- _(Testes com substituto; impacto em dependências do projeto.)_

## Alternativas consideradas

- _(Registrar apenas em repositório, sem log externo — rejeitado pela sprint.)_
