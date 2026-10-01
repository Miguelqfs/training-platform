# Gerenciamento de usuários: Laboratório 2

## Contexto

O produto terá alunos que acompanham seus treinos e administradores que operam a plataforma. O treinador será um agente de IA que trabalhará com os treinos em uma etapa futura; ele não é um tipo de usuário nesta sprint.

## Funcionalidades

- Adicionar um usuário com `username` (login), `email`, `password` e `role` (`student` ou `admin`). Se `role` for omitido, o usuário será `student`, preservando o contrato inicial da API.
- Gerar um identificador inteiro único em cada instância da aplicação.
- Rejeitar `username` vazio, composto só de espaços ou com mais de 12 caracteres ou com números Unicode, e e-mail inválido.
- Rejeitar `username` ou e-mail já cadastrado, sem diferenciar maiúsculas de minúsculas e ignorando espaços nas extremidades.
- Listar todos os usuários cadastrados, incluindo seus identificadores e tipos.
- Selecionar RAM (`USER_STORAGE=memory`, padrão) ou SQLite (`USER_STORAGE=sqlite`, caminho `USER_DATABASE`) no início da execução. RAM é isolada por processo; SQLite preserva os usuários e IDs entre reinicializações.
- Validar senha conforme política padrão IAM: 8 a 128 caracteres, três das quatro categorias (`A-Z`, `a-z`, `0-9`, `!@#$%^&*()_+-=[]{}|'`), diferente de login ou e-mail normalizados. Senhas não expiram.
- Tratar validação com `InvalidCredentialsError`, duplicidade com `DuplicateUserError` e erros SQLite com `PersistenceError`, preservando a causa original.
- Armazenar somente hash de senha com salt aleatório; nunca retornar senha ou hash.

## API da sprint

| Operação | Resultado |
| --- | --- |
| `POST /users/` | `201` com o usuário criado; `409` em caso de duplicidade; `422` para entrada inválida; `503` para falha de persistência |
| `GET /users/` | `200` com a lista de usuários, ou `[]` se estiver vazia; `503` para falha de persistência |

Exemplo de cadastro:

```json
{"username": "maria", "email": "maria@example.com", "role": "student", "password": "Abcdef12"}
```

## Limites da sprint

Autenticação, autorização por tipo, aplicativo mobile, treinos e agente de IA não fazem parte desta implementação. Portanto, `role` classifica o usuário, mas ainda não concede nem restringe acesso. A API é um protótipo local e não deve ser publicada com dados reais antes de proteger cadastro e listagem.
