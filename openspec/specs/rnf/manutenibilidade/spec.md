# Manutenibilidade da persistência

## Purpose

Permitir substituir a persistência pelo contrato, sem acoplar o serviço à RAM ou ao SQLite.

## Requirements

### Requirement: NF-MAN-01 — Depender do contrato de persistência

`UserService` DEVE receber `UserRepository`, com 0 referências às implementações concretas. Um repositório substituto DEVE permitir cadastro, listagem, busca por ID e contagem com 0 alterações no serviço. Cadastro e listagem também DEVEM preservar as rotas. A seleção por configuração pertence a RF05.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Repositório substituto

- **GIVEN** um repositório de teste que implementa `add(NewUser)`, `list_users()`, `get_by_id` e `count` sem herdar dos repositórios existentes
- **WHEN** ele é fornecido a `UserService` para cadastrar e listar um usuário
- **THEN** ambas as operações usam esse repositório, sem modificar o serviço ou as rotas

#### Scenario: Busca e contagem substitutas

- **GIVEN** um repositório de teste que implementa todo o contrato `UserRepository` sem herdar dos repositórios existentes e contém 2 usuários
- **WHEN** a busca usa o `id` do primeiro e a contagem é solicitada
- **THEN** a busca retorna esse usuário e a contagem retorna 2, sem modificar o serviço

### Requirement: NF-MAN-02 — Depender dos contratos de treino e de usuário

`WorkoutService` DEVE receber `WorkoutRepository` e `UserRepository` e ter 0 referências às implementações concretas. A existência do usuário DEVE ser verificada por `get_by_id`, sem consulta HTTP e sem SQL no serviço. Um repositório substituto DEVE executar o CRUD e a contagem sem alterar o serviço ou as rotas.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC04

#### Scenario: Repositório substituto de treinos

- **GIVEN** um repositório de teste que implementa o contrato de treinos sem herdar dos repositórios existentes e um repositório de usuários que encontra o `id` informado
- **WHEN** ele é fornecido a `WorkoutService` para cadastrar, consultar por ID, listar, atualizar, excluir e contar um treino
- **THEN** as operações usam esses repositórios, sem modificar o serviço ou as rotas

#### Scenario: Usuário ausente sem SQL no serviço

- **GIVEN** um `UserRepository` substituto cuja busca por ID não encontra o usuário
- **WHEN** o serviço tenta cadastrar um treino
- **THEN** a operação falha com usuário não encontrado e o repositório de treinos recebe 0 gravações
