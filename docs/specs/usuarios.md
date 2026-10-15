# Gerenciamento de usuários: Sprint 2

## Contexto

O produto terá alunos que acompanham seus treinos e administradores que operam a plataforma. O treinador será um agente de IA que trabalhará com os treinos em uma etapa futura; ele não é um tipo de usuário nesta sprint.

## Requisitos em vigor

A especificação normativa, com IDs, prioridades e cenários de sucesso, erro e
limites, está em [OpenSpec: usuários](../../openspec/specs/usuarios/spec.md).
Este documento é o ponto de entrada para o contrato da sprint, sem duplicar as
regras normativas.

| ID | Requisito funcional | Prioridade |
| --- | --- | --- |
| RF01 | Cadastrar usuário e gerar ID, rejeitando duplicidades. | Essencial |
| RF02 | Validar login. | Essencial |
| RF03 | Validar senha pela política IAM padrão. | Essencial |
| RF04 | Listar todos os usuários. | Essencial |
| RF05 | Selecionar RAM ou SQLite na inicialização. | Essencial |
| RF06 | Validar e-mail. | Essencial |
| RF07 | Validar papel. | Essencial |

Os RNFs ficam separados por categoria:

- [Segurança](../../openspec/specs/rnf/seguranca/spec.md): exposição de credenciais e armazenamento de hash.
- [Confiabilidade](../../openspec/specs/rnf/confiabilidade/spec.md): indisponibilidade, atomicidade e durabilidade SQLite.
- [Manutenibilidade](../../openspec/specs/rnf/manutenibilidade/spec.md): substituição do repositório pelo contrato.
- [Usabilidade](../../openspec/specs/rnf/usabilidade/spec.md): identificação da regra inválida nas respostas de validação.

Os contratos Python alterados na revisão estão no
[ADR 0004](../adr/0004-revisao-entrega-1.md).

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
