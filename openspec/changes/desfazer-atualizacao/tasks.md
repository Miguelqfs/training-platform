# Tarefas da change

As tarefas seguintes são de implementação e integração, não representam trabalho concluído neste PR. A proposta deve ser revisada antes da implementação.

## Especificação e pré-requisito

- [ ] 1.1 Revisar proposta, cenários e contratos de desfazer com a equipe.
- [ ] 1.2 Concluir documentação e arquivar `relatorio-de-acessos`; atualizar o delta desta change para os requisitos incorporados, preservando IDs e cenários anteriores.

## Persistência e Memento

- [ ] 2.1 Registrar ADR dos contratos de persistência e restauração junto ao primeiro PR que os alterar.
- [ ] 2.2 Implementar Memento e armazenamento em RAM/SQLite, com criação compatível com bancos antigos e testes de reinício e isolamento.
- [ ] 2.3 Integrar captura, substituição, consumo e remoção de Memento à unidade de trabalho, com testes de rollback e concorrência.

## Command e desfazer

- [ ] 3.1 Registrar ADR da fachada baseada em Command com participantes e decisões de compatibilidade.
- [ ] 3.2 Encaminhar operações existentes e desfazer por comandos e testar fachada, contextos e contratos anteriores.
- [ ] 3.3 Implementar restauração e endpoint com testes de sucesso, ausência, repetição, falhas e treinos independentes.
- [ ] 3.4 Registrar evento `undo` atomicamente, atualizar relatórios HTML/PDF e testar dados existentes, operação zero e falha de log.

## Integração e entrega

- [ ] 4.1 Atualizar casos de uso, diagramas e tabela de padrões de acordo com as classes reais.
- [ ] 4.2 Executar testes, Ruff, validação OpenSpec, links e CI, incluindo cenários em RAM e SQLite.
- [ ] 4.3 Arquivar esta change após implementação e validação completas e revisar specs em vigor.
- [ ] 4.4 Preparar PR `develop` → `main` e tag `v0.4.0` depois da validação integrada.
