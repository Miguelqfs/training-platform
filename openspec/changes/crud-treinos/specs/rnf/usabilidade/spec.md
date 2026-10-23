# Spec delta — usabilidade

## ADDED Requirements

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
