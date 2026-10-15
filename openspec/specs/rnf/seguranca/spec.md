# Segurança dos dados de usuário

## Purpose

Impedir a exposição da senha de cadastro na resposta da API e no armazenamento.

## Requirements

### Requirement: NF-SEG-01 — Não expor senhas

O sistema DEVE apresentar 0 ocorrências da senha original e 0 campos de hash de senha nas respostas de cadastro, listagem e erro. No armazenamento, DEVE guardar 0 senhas em texto puro.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Resposta e armazenamento

- **GIVEN** um cadastro com senha válida
- **WHEN** o usuário é cadastrado, listado ou ocorre erro de validação
- **THEN** as respostas contêm 0 valores de senha e 0 hashes; o armazenamento contém 0 senhas em texto puro
