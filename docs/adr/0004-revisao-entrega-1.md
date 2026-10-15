# ADR 0004 — Correções da revisão da Entrega 1

## Estado

Aceito para a revisão das Sprints 1 e 2. Complementa o ADR 0003.

## Contexto

A avaliação apontou dependência direta de `UserService` com a implementação RAM,
muitos parâmetros no cadastro e concentração de responsabilidades na criação da
aplicação. A revisão não inclui a Sprint 3.

## Decisão

- Exigir um `UserRepository` no construtor de `UserService`. Somente a função
  `create_user_repository`, chamada na inicialização, escolhe RAM ou SQLite.
- Receber um objeto `UserRegistration` em `UserService.add_user` e um objeto
  `NewUser` em `UserRepository.add`. O primeiro contém a senha; o segundo contém
  somente seu hash. Ambos omitem esse campo na representação textual.
- Extrair os tratadores HTTP para `app/error_handlers.py`, mantendo a remoção
  dos valores de entrada dos erros de validação.

## Contratos afetados

Chamadas Python a `UserService()` devem fornecer um repositório. Chamadas a
`add_user` e `add` passam a usar os objetos descritos acima. Os dois repositórios,
as rotas e os testes são atualizados juntos.

O JSON de cadastro e resposta, as rotas e os códigos HTTP permanecem os mesmos.

## Consequências

O serviço depende apenas do contrato de persistência e pode receber outra
implementação sem alteração. Não há nova dependência de execução, migração de
banco, autenticação, nova entidade, Singleton ou Facade nesta revisão.
