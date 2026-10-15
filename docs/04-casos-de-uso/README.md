# Casos de uso: gerenciamento de usuários

O diagrama da Entrega 1 apresenta os dois tipos de usuário cadastrados, Aluno e Administrador, e os casos de uso de cadastro e listagem. Os atores expressam a proposta de uso e não representam permissões implementadas: a API atual não autentica nem autoriza operações por papel. A intenção mais recente do grupo é que o administrador realize cadastro e listagem; essa restrição ainda não está implementada e deve ser refletida em um diagrama futuro quando o controle de acesso for definido.

| ID | Caso de uso | Pré-condição atual | Resultado e alternativas | Requisitos |
| --- | --- | --- | --- | --- |
| UC01 | Cadastrar usuário | API iniciada com um repositório disponível; não exige sessão autenticada nesta versão. | Recebe login, e-mail, senha e papel; retorna 201 com ID gerado. Entrada inválida: 422; duplicidade: 409; falha de persistência em execução: 503. | RF01, RF02, RF03, RF05, RF06, RF07 |
| UC02 | Listar usuários | API iniciada; não exige sessão autenticada nesta versão. | Retorna 200 com todos os usuários ou lista vazia. Falha de persistência em execução: 503. | RF04, RF05 |

![Diagrama de casos de uso de usuários](../diagramas/diagrama-casos-de-uso.png)

Fonte editável: [PlantUML](../diagramas/casos-de-uso-usuarios.puml). Os requisitos observáveis estão em [Gerenciamento de usuários](../../openspec/specs/usuarios/spec.md).
