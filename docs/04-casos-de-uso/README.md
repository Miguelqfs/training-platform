# Casos de uso

Os atores representam a intenção de uso do produto. A API atual não autentica
nem autoriza por papel; qualquer cliente local pode executar as operações.
O treinador IA é componente futuro, não um terceiro tipo de usuário.

| ID | Caso de uso | Resultado e alternativas | Requisitos |
| --- | --- | --- | --- |
| [UC01](UC01-cadastrar-usuario.md) | Cadastrar usuário | 201; inválido 422, duplicado 409, persistência 503. | RF01–RF03, RF05–RF07, RF16 |
| UC02 | Listar usuários | 200 e lista (inclusive vazia); persistência 503. | RF04, RF05, RF16 |
| [UC03](UC03-cadastrar-treino.md) | Cadastrar treino | 201; inválido 422, usuário ausente 404, persistência 503. | RF08, RF09, RF14–RF16 |
| [UC04](UC04-atualizar-treino.md) | Atualizar treino | 200; inválido 422, treino ausente 404, persistência 503. | RF09, RF12, RF15, RF16 |
| UC05 | Consultar treino | 200; ID inválido 422, ausente 404, persistência 503. | RF10, RF16 |
| UC06 | Listar treinos | 200 e lista ordenada por ID; persistência 503. | RF11, RF15, RF16 |
| UC07 | Excluir treino | 204 sem corpo; ID inválido 422, ausente/repetido 404, persistência 503. | RF13, RF14, RF16 |
| UC08 | Contar entidades | 200 com total inteiro de usuários + treinos; persistência 503. | RF17, RF18 |

Pré-condição comum: API iniciada com RAM ou SQLite. UC03 exige usuário existente;
UC04, UC05 e UC07 exigem treino existente para o fluxo de sucesso. Os casos
detalhados descrevem também a violação dessas pré-condições no acesso HTTP.

![Diagrama geral de casos de uso](../diagramas/diagrama-casos-de-uso.png)

[Fonte PlantUML](../diagramas/casos-de-uso-usuarios.puml).
O bloco futuro deriva da [visão](../01-visao.md), sem afirmar implementação.
A contagem vem do enunciado da Sprint 3. Os contratos normativos ficam em
[usuários](../../openspec/specs/usuarios/spec.md),
[treinos](../../openspec/specs/treinos/spec.md) e
[fachada](../../openspec/specs/fachada/spec.md).
