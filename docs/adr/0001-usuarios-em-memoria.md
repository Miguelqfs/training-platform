# ADR 0001: Usuários em memória na primeira sprint

## Estado

Decisão histórica da Sprint 1. Stack e organização Python substituídas pelo [ADR 0003](0003-rust-api.md); os papéis e as regras de negócio são mantidos.

## Contexto

A disciplina pede cadastro e listagem de usuários em uma coleção na RAM, além de diagramas de casos de uso e classes de análise. A API já possui `POST /users/` e `GET /users/`, com `username` e `email`, mas não representa os dois tipos de usuário nem separa responsabilidades.

## Decisão

- Manter a API FastAPI e as rotas existentes em `app/`. O aplicativo mobile será criado quando houver funcionalidade sua para implementar; a arquitetura prevista fica documentada.
- Adicionar o campo `role` com os valores `student` e `admin`. No cadastro ele é opcional, com padrão `student`, para preservar pedidos existentes. A resposta passa a incluir `role`.
- Manter os esquemas HTTP em `app/schemas.py` e as rotas em `app/routers/`. Colocar a entidade e o serviço de usuários no pacote `app/users/`. O serviço mantém a coleção em RAM nesta sprint.
- Garantir unicidade de `username` e e-mail sem diferenciar maiúsculas de minúsculas. A coleção pertence a uma instância da aplicação e dura somente enquanto seu processo estiver ativo.
- Não aplicar autenticação ou autorização nesta sprint. O papel `admin` não oferece proteção enquanto esses mecanismos não forem implementados.
- Incluir `httpx2` e `pytest` no arquivo único de dependências para executar os testes da API com `TestClient` do FastAPI.

## Consequências

A resposta de `POST /users/` e os itens de `GET /users/` ganham `role`, alterando o contrato público da API. O protótipo não é adequado para exposição pública com dados reais. Quando houver banco de dados, a coleção pode ser extraída do serviço para um repositório próprio.
