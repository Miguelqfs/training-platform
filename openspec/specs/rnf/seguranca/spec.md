# Segurança dos dados de usuário

## Purpose

Impedir a exposição de credenciais e proteger a senha armazenada.

## Requirements

### Requirement: NF-SEG-01 — Não expor senhas

As respostas de cadastro e listagem DEVEM conter somente `id`, `username`, `email` e `role` por usuário, com 0 campos `password` ou `password_hash`. Respostas de validação NÃO DEVEM reproduzir a entrada recebida (`input` ou `ctx` do Pydantic), inclusive quando `password` tem tipo inválido. Mensagens de domínio NÃO DEVEM interpolar a senha recebida.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Resposta e armazenamento

- **GIVEN** um cadastro com senha válida
- **WHEN** o usuário é cadastrado, listado ou ocorre erro de validação
- **THEN** os usuários retornados contêm apenas os 4 campos públicos e o erro não reproduz a senha enviada

### Requirement: NF-SEG-02 — Armazenar hash com salt

Nos modos RAM e SQLite, a senha DEVE ser armazenada somente como hash PBKDF2-HMAC-SHA256, com 600.000 iterações e salt aleatório de 16 bytes por cadastro. Dois cadastros com a mesma senha DEVEM receber salts distintos.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Hash verificável

- **GIVEN** cadastro com senha válida em cada um dos 2 mecanismos
- **WHEN** o registro persistido é inspecionado
- **THEN** o campo de senha contém o hash no formato `pbkdf2_sha256$600000$salt$hash`, o salt tem 16 bytes e a derivação recalculada corresponde ao hash

#### Scenario: Mesma senha em usuários diferentes

- **GIVEN** 2 cadastros distintos com a mesma senha válida
- **WHEN** seus hashes são inspecionados em RAM ou SQLite
- **THEN** os 2 salts são diferentes
