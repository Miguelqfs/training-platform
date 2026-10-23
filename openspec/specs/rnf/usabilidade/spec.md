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

### Requirement: NF-USA-02 — Identificar a regra de treino violada

Para entradas de treino inválidas, a resposta HTTP 422 DEVE identificar campo e regra. A fronteira PODE retornar vários erros, um por campo. No serviço, cada exceção DEVE informar só a primeira falha: tipo/valor do identificador, nome e descrição, antes da busca do vínculo ou treino. Campo imutável enviado na atualização DEVE ser recusado, mesmo sem mudança de valor.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC04

#### Scenario: Nome e descrição inválidos juntos

- **GIVEN** nome vazio e descrição com 1.001 caracteres
- **WHEN** o serviço recebe o cadastro com `user_id` válido
- **THEN** a exceção informa somente a regra do nome e não registra treino

#### Scenario: Nome inválido na fronteira HTTP

- **GIVEN** nome vazio e descrição com 1.001 caracteres
- **WHEN** `POST /workouts/` é enviado com `user_id` válido
- **THEN** retorna HTTP 422 identificando `name` e `description`, sem exigir ordem entre os itens de erro, e não registra treino

#### Scenario: Descrição acima do limite

- **GIVEN** nome válido e descrição com 1.001 caracteres
- **WHEN** o cadastro é enviado
- **THEN** retorna HTTP 422 identificando o campo `description`

#### Scenario: Campo desconhecido

- **GIVEN** um campo `series` além dos campos aceitos
- **WHEN** o cadastro ou a atualização é enviado
- **THEN** retorna HTTP 422 identificando `series` e o treino anterior, se existir, permanece igual
