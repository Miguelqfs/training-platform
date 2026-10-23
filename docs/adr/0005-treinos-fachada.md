# ADR 0005: CRUD de treinos e fachada única

## Estado

Aceito para implementação local em 23/10/2026, após revisão da proposta
`crud-treinos` e solicitação de concluir a Sprint 3. Publicação, merges e tag
continuam sujeitos ao fluxo de contribuição.

## Contexto

A Sprint 3 exige CRUD de nova entidade relacionada e uma
`FacadeSingletonController` com Singleton, Facade e contagem de entidades.
A API existente possui usuários, serviços independentes de persistência e
aplicações de teste criadas no mesmo processo.

## Decisão

Introduzir `Workout`, plano com `id`, `user_id`, `name` e `description`.
Nome normalizado tem 1–100 caracteres; descrição normalizada tem até 1.000.
Omissão da descrição significa texto vazio, também em PUT. Nomes repetidos são
permitidos. IDs e vínculo são imutáveis. Não há autenticação, autorização,
exercícios ou execução de treinos nesta entrega.

Adicionar `get_by_id` e `count` ao protocolo `UserRepository`, preservando
`add` e `list_users`; acrescentar `count_users` ao serviço. `WorkoutRepository`
expõe `add`, `get_by_id`, `list_workouts`, `update`, `delete` e `count`.
Os serviços recebem protocolos por injeção; DTOs são dataclasses congeladas.
Ausência retorna None/False nos repositórios e exceção de domínio no serviço.

Resolver USER_STORAGE/USER_DATABASE uma vez por aplicação. RAM mantém coleções
próprias e trava; treinos usam contador monotônico. SQLite usa o mesmo arquivo,
CREATE TABLE IF NOT EXISTS, AUTOINCREMENT e FK para users, habilitada em cada
conexão. Escritas parametrizadas usam transações. IDs são vinculados como
texto decimal no SQL: a afinidade INTEGER mantém o valor e evita overflow
do driver ao consultar IDs positivos maiores que 64 bits, que continuam
ausentes (404), sem introduzir um limite público novo. Não apagar tabelas existentes.
Somente SQLITE_CONSTRAINT_FOREIGNKEY vira usuário ausente; demais falhas de
banco preservam a causa em PersistenceError.

PersistenceError ganha public_message, restrita às mensagens constantes
“Armazenamento de usuários indisponível” (padrão compatível) e
“Armazenamento de treinos indisponível”. Falha ao buscar o vínculo durante
cadastro publica a mensagem de treinos. Contagem consulta usuários primeiro.
SQL, caminhos, causas e entrada sensível não são publicados.

A fachada tem instância única por processo, com construção protegida por trava,
sem contexto nem dados de negócio globais. ApplicationContext, congelado quanto
às referências, pertence a app.state.context. Todas as rotas delegam à fachada,
que delega aos serviços do contexto recebido. count_entities(context) retorna
um int: usuários student/admin mais treinos. Não há contador global nem garantia
de fotografia transacional entre consultas concorrentes de duas coleções.

RAM e arquivos diferentes ficam isolados. Duas aplicações configuradas com o
mesmo SQLite compartilham intencionalmente registros, preservando seus contextos.
Criar outra aplicação não reinicia a fachada nem redireciona a primeira.

HTTP novo: POST/GET /workouts/, GET/PUT/DELETE /workouts/{id} e
GET /statistics/entities. Sucessos: 201/200/204; entrada inválida: 422;
ausência: 404; persistência em execução: 503. JSON de treinos recusa extras,
null e coerções de user_id; PUT só aceita name/description. IDs na URL usam
conversão normal para inteiro positivo. Título OpenAPI: Training Platform.
As respostas de usuários permanecem compatíveis e não expõem credenciais.
O OpenAPI descreve erros 404/409/422/503 conforme cada operação; validação 422
pode ter `detail` textual (domínio) ou lista de erros de campo (fronteira).
IDs de resposta são positivos e o total não é negativo, como os registros gerados.
Essas declarações documentam os corpos e limites já previstos, sem alterá-los.

## Alternativas e consequências

Guardar repositórios no Singleton misturaria aplicações; recriá-lo a cada app
quebraria sua identidade. Um contexto explícito evita ambos. O escopo é o
processo, sem Singleton distribuído. A fachada não oferece reset público.

AUTOINCREMENT evita reutilizar IDs de cadastros confirmados excluídos, sem
prometer sequência sem lacunas. A tabela adicional não exige migrar usuários.
PUT sem descrição apaga o texto anterior, conforme contrato explícito.
Diagrama de classes, especificações e testes acompanham estes contratos.
