# Tarefas da change

Esta lista planeja a sprint; itens permanecem abertos até serem concluídos e verificados. A proposta deve ser revisada antes da implementação.

## Contratos e persistência

- [ ] 1.1 Registrar ADR dos contratos públicos de eventos, relatórios e consistência no primeiro PR que os introduzir.
- [x] 1.2 Registrar ADR Repository + Factory com participantes, variantes escolhidas e composição RAM/SQLite.
- [x] 1.3 Implementar protocolo e repositórios de eventos, com testes de intervalo, persistência, banco legado e isolamento.
- [x] 1.4 Integrar fábrica e unidade de trabalho à composição de usuários, treinos e eventos, preservando a configuração e os testes anteriores.

## Registro e Adapter

- [x] 2.1 Implementar registro transacional nas quatro operações elegíveis, com testes de sucesso, exclusões e falhas em RAM e SQLite.
- [x] 2.2 Registrar ADR do Adapter e implementar porta e Adapter de log auxiliar sem dados sensíveis, com testes de falha.

## Relatórios

- [ ] 3.1 Implementar agregação e Template Method na camada business, com relógio controlável nos testes e resultados determinísticos.
- [ ] 3.2 Implementar renderizadores HTML e PDF, documentar dependência PDF e testar equivalência e período vazio.
- [ ] 3.3 Expor consulta pela fachada e API, testar validação, tipos de conteúdo e falhas, sem registrar acesso à consulta do relatório.

## Documentação e encerramento

- [ ] 4.1 Atualizar UC03–UC05 e UC07, adicionar UC09 e atualizar diagramas, arquitetura, README e tabela dos padrões usados.
- [ ] 4.2 Executar testes, Ruff, validação OpenSpec, links e verificações do CI; conferir cobertura e ausência de credenciais.
- [ ] 4.3 Integrar os PRs de implementação após revisão e checks; arquivar a change somente quando todos os requisitos estiverem implementados e validados.
- [ ] 4.4 Preparar PR `develop` → `main` e tag `v0.3.0` após a validação integrada.
