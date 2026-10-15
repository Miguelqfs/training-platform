# Manutenibilidade da persistência

## Purpose

Permitir substituir a persistência pelo contrato, sem acoplar o serviço à RAM ou ao SQLite.

## Requirements

### Requirement: NF-MAN-01 — Depender do contrato de persistência

`UserService` DEVE receber explicitamente um objeto compatível com `UserRepository` e ter 0 referências a `MemoryUserRepository` ou `SQLiteUserRepository`. Um terceiro repositório compatível DEVE poder executar cadastro e listagem com 0 alterações no serviço ou nas rotas. A seleção por configuração é RF05 e não constitui outro RNF.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Repositório substituto

- **GIVEN** um repositório de teste que implementa `add(NewUser)` e `list_users()` sem herdar dos repositórios existentes
- **WHEN** ele é fornecido a `UserService` para cadastrar e listar um usuário
- **THEN** ambas as operações usam esse repositório, sem modificar o serviço ou as rotas
