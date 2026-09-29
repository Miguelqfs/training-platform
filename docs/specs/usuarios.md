# Gerenciamento de usuários — Sprint 1

## Contexto

O produto terá alunos que acompanham seus treinos e administradores que operam a plataforma. O treinador será um agente de IA que trabalhará com os treinos em uma etapa futura; ele não é um tipo de usuário nesta sprint.

## Funcionalidades

- Adicionar um usuário com `username`, `email` e `role` (`student` ou `admin`). Se `role` for omitido, o usuário será `student`, preservando o contrato inicial da API.
- Gerar um identificador inteiro único em cada instância da aplicação.
- Rejeitar `username` vazio, composto só de espaços ou com mais de 50 caracteres, e e-mail inválido.
- Rejeitar `username` ou e-mail já cadastrado, sem diferenciar maiúsculas de minúsculas e ignorando espaços nas extremidades.
- Listar todos os usuários cadastrados, incluindo seus identificadores e tipos.
- Guardar os usuários somente em uma coleção na memória do processo. Os dados são perdidos quando a API reinicia; processos distintos não compartilham a coleção.

## API da sprint

| Operação | Resultado |
| --- | --- |
| `POST /users/` | `201` com o usuário criado; `409` em caso de duplicidade; `422` para entrada inválida |
| `GET /users/` | `200` com a lista de usuários, ou `[]` se estiver vazia |

Exemplo de cadastro:

```json
{"username": "maria", "email": "maria@example.com", "role": "student"}
```

## Limites da sprint

Autenticação, autorização por tipo, senhas, banco de dados, aplicativo mobile, treinos e agente de IA não fazem parte desta implementação. Portanto, `role` classifica o usuário, mas ainda não concede nem restringe acesso. A API é um protótipo local e não deve ser publicada com dados reais antes de proteger cadastro e listagem.
