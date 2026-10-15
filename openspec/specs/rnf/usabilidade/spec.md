# Clareza das mensagens de validação

## Purpose

Permitir que quem integra a API identifique qual regra precisa corrigir.

## Requirements

### Requirement: NF-USA-01 — Identificar a regra violada

Para entradas de cadastro inválidas, a resposta HTTP 422 DEVE identificar o campo
e a regra violada. Para credenciais validadas no domínio, a mensagem DEVE distinguir
login vazio, login longo, login com números, tamanho da senha, categorias da senha
e equivalência à identidade, informando a primeira regra violada. Para erros do
Pydantic, a resposta DEVE identificar o campo em `loc` e a regra em `type`/`msg`.
Uma mensagem genérica como “Credenciais inválidas” não atende ao requisito.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Login numérico

- **GIVEN** login `user١` e demais campos válidos
- **WHEN** o cadastro é enviado
- **THEN** retorna HTTP 422 com `detail: "Login não pode conter números"`

#### Scenario: Comprimento ou categorias da senha

- **GIVEN** senha `Abc1234` ou `Abcdefgh` e demais campos válidos
- **WHEN** o cadastro é enviado
- **THEN** retorna HTTP 422, indicando respectivamente tamanho de 8 a 128 caracteres ou mínimo de 3 categorias

#### Scenario: Campo inválido na fronteira HTTP

- **GIVEN** e-mail `not-an-email` ou papel `trainer`
- **WHEN** o cadastro é enviado com os outros campos válidos
- **THEN** retorna HTTP 422 com o campo correspondente em `loc` e a explicação em `msg`
