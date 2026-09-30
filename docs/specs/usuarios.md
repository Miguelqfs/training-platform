# Gerenciamento de usuários: Sprint 1

## Contexto

O produto terá alunos que acompanham seus treinos e administradores que operam a plataforma. O treinador será um agente de IA que trabalhará com os treinos em uma etapa futura; ele não é um tipo de usuário nesta sprint.

## Funcionalidades

- Adicionar um usuário com `username`, `email` e `role` (`student` ou `admin`). Se `role` for omitido, o usuário será `student`. Outros papéis são rejeitados com 422.
- Gerar um identificador inteiro único em cada instância da aplicação.
- Rejeitar `username` vazio, composto só de espaços ou com mais de 50 caracteres, e e-mail inválido.
- Rejeitar `username` ou e-mail já cadastrado, sem diferenciar maiúsculas de minúsculas e ignorando espaços nas extremidades.
- Remover espaços nas extremidades do nome antes de validar o comprimento. Preservar a caixa do nome e armazenar o e-mail em minúsculas.
- Listar todos os usuários cadastrados, incluindo seus identificadores e tipos.
- Guardar os usuários somente em uma coleção na memória do processo. Os dados são perdidos quando a API reinicia; processos distintos não compartilham a coleção.

## Atores e casos de uso

| Caso de uso | Atores |
| --- | --- |
| Cadastrar usuário | Aluno e administrador |
| Listar usuários cadastrados | Administrador |

Essas associações representam os casos de uso do produto. O aluno não participa
da listagem de usuários. O protótipo ainda não autentica o solicitante nem aplica
essas permissões. O [diagrama](../diagramas/casos-de-uso-usuarios.puml) apresenta
as entradas e os resultados de cada operação.

## API da sprint

| Operação | Resultado |
| --- | --- |
| `POST /users/` | `201` com o usuário criado; `409` em caso de duplicidade; `422` para entrada inválida |
| `GET /users/` | `200` com a lista de usuários, ou `[]` se estiver vazia |

Exemplo de cadastro:

```json
{"username": "maria", "email": "maria@example.com", "role": "student"}
```

Exemplo de cadastro de administrador:

```json
{"username": "ana", "email": "ana@example.com", "role": "admin"}
```

## Limites da sprint

Autenticação, autorização, senhas, banco de dados, aplicativo mobile, treinos e agente de IA não fazem parte desta implementação. Portanto, `role` classifica o usuário, mas ainda não concede nem restringe acesso. A API é um protótipo local e não deve ser publicada com dados reais antes de proteger cadastro e listagem. A migração para Rust e as diferenças de validação estão no [ADR 0003](../adr/0003-rust-api.md).
