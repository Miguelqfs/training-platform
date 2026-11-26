# Tarefas da change

O checklist acompanha a revisão, a implementação e a entrega desta change.

## Especificação e pré-requisito

- [x] 1.1 Revisar proposta, cenários e contratos de desfazer com a equipe. A proposta entrou em `develop` no PR #24 e os PRs #25, #26 e #27 implementaram esses contratos.
- [x] 1.2 Concluir documentação e arquivar `relatorio-de-acessos`; atualizar o delta desta change para os requisitos incorporados, preservando IDs e cenários anteriores.

## Persistência e Memento

- [x] 2.1 Registrar ADR dos contratos de persistência e restauração junto ao primeiro PR que os alterar.
- [x] 2.2 Implementar Memento e armazenamento em RAM/SQLite, com criação compatível com bancos antigos e testes de reinício e isolamento.
- [x] 2.3 Integrar captura, substituição, consumo e remoção de Memento à unidade de trabalho, com testes de rollback e concorrência.

## Command e desfazer

- [x] 3.1 Registrar ADR da fachada baseada em Command com participantes e decisões de compatibilidade.
- [x] 3.2 Encaminhar operações existentes e desfazer por comandos e testar fachada, contextos e contratos anteriores.
- [x] 3.3 Implementar restauração e endpoint com testes de sucesso, ausência, repetição, falhas e treinos independentes.
- [x] 3.4 Registrar evento `undo` atomicamente, atualizar relatórios HTML/PDF e testar dados existentes, operação zero e falha de log.

## Integração e entrega

- [x] 4.1 Atualizar casos de uso, diagramas e tabela de padrões de acordo com as classes reais.
- [x] 4.2 Executar testes, Ruff, validação OpenSpec, links e CI, incluindo cenários em RAM e SQLite.
- [x] 4.3 Arquivar esta change após implementação e validação completas e revisar specs em vigor.
- [ ] 4.4 Preparar PR `develop` → `main` e tag `v0.4.0` depois da validação integrada.

Evidência local do fechamento, em 25/11/2026: 456 testes aprovados, Ruff e
formatação sem pendências. Os testes de desfazer cobrem RAM e SQLite. O CI
deste fechamento acompanha o PR da branch `docs/sprint5-fechamento`. A release
`v0.4.0` fica para o PR `develop` → `main`, depois desse merge.
