# Spec delta — segurança

## ADDED Requirements

### Requirement: NF-SEG-03 — Não expor credenciais nas respostas de treino

Cada treino retornado DEVE conter somente `id`, `user_id`, `name` e `description`, sem campos de credenciais ou o objeto usuário. A contagem DEVE conter somente `total`; exclusão bem-sucedida DEVE ter corpo vazio. Erros NÃO DEVEM reproduzir valores de campos extras de credenciais. Texto informado intencionalmente em nome ou descrição NÃO DEVE ser filtrado por coincidir com uma senha.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC04, UC08

#### Scenario: Resposta de treino

- **GIVEN** um usuário cadastrado com senha válida e um treino desse usuário
- **WHEN** o treino é criado, consultado, listado e atualizado
- **THEN** cada item tem exatamente os 4 campos públicos, sem `password`, `password_hash` ou objeto usuário aninhado

#### Scenario: Nome coincidente com uma senha

- **GIVEN** um usuário cuja senha é `Abcdef12`
- **WHEN** um treino válido é cadastrado com `name` igual a `Abcdef12` e descrição vazia
- **THEN** retorna HTTP 201 com esse nome, sem acrescentar campos de credenciais nem serializar o objeto usuário

#### Scenario: Contagem e exclusão

- **GIVEN** 1 usuário e 1 treino
- **WHEN** a contagem e a exclusão são solicitadas
- **THEN** a contagem tem exatamente a chave `total` e a exclusão responde HTTP 204 com corpo vazio

#### Scenario: Senha em campo extra

- **GIVEN** corpos de cadastro e atualização com nome `Peito`, descrição vazia e campo extra `password` ou `password_hash` de valor `Senha@2026`
- **WHEN** cada pedido é enviado separadamente
- **THEN** todos retornam HTTP 422 sem reproduzir o valor extra, sem criar treino nem alterar um treino existente

## MODIFIED Requirements

### Requirement: NF-SEG-01 — Não expor senhas

As respostas de cadastro e listagem de usuários DEVEM conter somente `id`, `username`, `email` e `role` por usuário, com 0 campos `password` ou `password_hash`. Respostas de validação de qualquer operação NÃO DEVEM reproduzir a entrada recebida (`input` ou `ctx` do Pydantic), inclusive quando `password` tem tipo inválido. Mensagens de domínio NÃO DEVEM interpolar a senha recebida. O conteúdo das respostas de treino está em NF-SEG-03.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Resposta e armazenamento

- **GIVEN** um cadastro com senha válida
- **WHEN** o usuário é cadastrado, listado ou ocorre erro de validação
- **THEN** os usuários retornados contêm apenas os 4 campos públicos e o erro não reproduz a senha enviada
