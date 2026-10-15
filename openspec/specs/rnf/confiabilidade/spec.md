# Confiabilidade do armazenamento

## Purpose

Evitar cadastro parcial e comunicar indisponibilidade do armazenamento de modo previsível.

## Requirements

### Requirement: NF-CON-01 — Tratar falhas de persistência

O sistema DEVE retornar HTTP 503 em 100% das falhas de leitura e escrita SQLite detectadas durante requisições, sem expor comandos SQL ou caminhos internos. Uma gravação malsucedida DEVE deixar 0 cadastros parciais.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Banco indisponível

- **GIVEN** uma falha de leitura ou escrita SQLite simulada
- **WHEN** o cadastro ou a listagem é solicitado
- **THEN** 100% das requisições afetadas retornam HTTP 503 com mensagem genérica e 0 cadastros parciais permanecem
