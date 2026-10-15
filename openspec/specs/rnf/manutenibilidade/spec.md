# Manutenibilidade da persistência

## Purpose

Permitir selecionar o mecanismo de armazenamento sem alteração de código.

## Requirements

### Requirement: NF-MAN-01 — Alternar mecanismo de armazenamento

O sistema DEVE alternar entre os 2 mecanismos de persistência previstos, RAM e SQLite, mediante configuração no início do processo, com 0 alterações no código da API e do serviço de usuários.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Troca de mecanismo

- **GIVEN** a aplicação configurada com `USER_STORAGE=memory`
- **WHEN** o operador altera a configuração para `USER_STORAGE=sqlite` e reinicia a aplicação
- **THEN** o armazenamento muda para SQLite com 0 alterações no código da API e do serviço
