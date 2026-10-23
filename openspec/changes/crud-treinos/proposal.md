# Proposta: crud-treinos

**Estado: proposta para revisão e integração em develop.** O escopo foi
revisado com a equipe e a implementação já foi preparada e validada localmente.
Este PR contém somente a proposta; código, testes novos e requisitos em vigor
serão integrados nos PRs seguintes, após sua revisão. O arquivamento é a última
etapa da implementação, e não faz parte deste PR.

## Why

O produto pretende reunir o acompanhamento de treinos. A elicitação já registrada aponta a dispersão das rotinas entre planilhas, notas e plataformas (P1, em `docs/01-visao.md` e `docs/03-elicitacao.md`). A API em vigor só cadastra e lista usuários.

A Entrega 2 do modelo da disciplina pede, para a Sprint 3, o CRUD de uma entidade principal relacionada a usuário, uma fachada única com Singleton e Facade, a classe `FacadeSingletonController` com um método que retorna a quantidade de entidades cadastradas, o repositório atualizado e a documentação correspondente. A change sugerida pelo modelo para essa capacidade é `crud-<entidade>`.

Esta proposta escolhe **Treino** (`Workout`): um plano com nome e descrição, ligado a um usuário já cadastrado. A entrevista e o questionário não definem campos, limites, unicidade nem contagem. Esses pontos estão marcados abaixo como decisões desta proposta.

## What Changes

- Nova capacidade `treinos`, com os requisitos **RF08** a **RF15**: cadastro, validação, consulta, listagem, atualização, exclusão, geração de ID e persistência de treinos.
- Nova capacidade `fachada`, com **RF16** a **RF18**: operações de usuários e treinos pela `FacadeSingletonController`, contagem de entidades e isolamento entre aplicações.
- RNFs novos: **NF-SEG-03**, **NF-CON-04**, **NF-CON-05**, **NF-CON-06**, **NF-MAN-02** e **NF-USA-02**.
- Ajustes de escopo, sem mudar o comportamento já aceito de usuários:
  - **NF-SEG-01** passa a nomear explicitamente as respostas de usuários.
  - **NF-CON-01** passa a nomear explicitamente as requisições de usuários.
  - **NF-MAN-01** passa a incluir busca por ID e contagem no contrato de `UserRepository`.
- Documentação da Entrega 2 depois da aprovação: casos de uso, wireframes, arquitetura, diagrama de classes, ADR 0005, glossário, visão e README. O ADR acompanha o primeiro contrato alterado; o diagrama de projeto acompanha os PRs de código.
- `openspec/config.yaml`, ausente no repositório, para a validação OpenSpec deste projeto.
- Verificação automatizada da documentação: configuração YAML válida e carregada, validação das specs e links locais, sem dependências novas na API.

**Fora do escopo:** aplicativo mobile, agente de IA, autenticação, autorização por papel, exercícios, séries, cargas, execução, histórico, exclusão de usuários, cascata, relatórios de acesso, desfazer atualização, Adapter, Template Method, Command, Memento, PostgreSQL, ORM, framework de injeção e repositório genérico.

Não há `GET /users/{id}`. A busca de usuário por ID existe para o vínculo e para a contagem, no contrato Python.

## Origem de cada decisão

| Tema | Origem |
| --- | --- |
| CRUD de entidade relacionada, fachada, Singleton e método de contagem | Enunciado da Sprint 3 no modelo da disciplina |
| Entidade Treino e vínculo com usuário | Proposta desta change, motivada por P1 e pelo enunciado |
| Limites de 1–100 e 1.000 caracteres, descrição vazia por omissão e nomes repetidos permitidos | Proposta desta change |
| Contagem = usuários + treinos | Interpretação proposta; o enunciado não define o que é contado |
| RAM e SQLite no mesmo `USER_STORAGE` e no mesmo arquivo | Continuidade do ADR 0003; não é exigência nova do enunciado |
| Papéis sem restringir operações | Comportamento já documentado; esta change não adiciona autorização |
| Data 30/10/2026 e tag `v0.2.0` | `docs/00-entregas.md` do modelo, consultado em 22/10/2026 |
| Data 28/10 | Citada no pedido desta sprint; não há registro no repositório |

## Capabilities

### New Capabilities

- `treinos`: plano de treino vinculado a um usuário.
- `fachada`: ponto único das operações de negócio e contagem de entidades.

### Modified Capabilities

- `rnf/seguranca`: delimita NF-SEG-01 às respostas de usuários e adiciona NF-SEG-03.
- `rnf/confiabilidade`: delimita NF-CON-01 às requisições de usuários e adiciona falha, atomicidade e durabilidade de treinos.
- `rnf/manutenibilidade`: inclui busca e contagem em NF-MAN-01 e adiciona NF-MAN-02.
- `rnf/usabilidade`: adiciona NF-USA-02 para os erros de treino.

Os requisitos RF01–RF07 e os demais RNFs permanecem com os mesmos IDs e cenários observáveis. UC01 e UC02 permanecem. Os próximos IDs usados são RF08, UC03, TL01, NF-SEG-03, NF-CON-04 e ADR 0005. ADR 0005 está livre: existem 0001 a 0004.

## Impact

- Novos módulos em `app/workouts/`, no mesmo desenho de `app/users/`.
- `app/users/repository.py` ganha `get_by_id` e `count`. `UserService` ganha `count_users`. `add_user(UserRegistration)` e o construtor com `UserRepository` obrigatório permanecem.
- Rotas atuais e novas chamam `FacadeSingletonController`. `create_app(storage, database_path)` permanece. `app.state.user_service` deixa de ser o acesso das rotas; o contexto da aplicação fica em `app.state.context`.
- Mesma seleção `USER_STORAGE` (`memory` ou `sqlite`) e o mesmo `USER_DATABASE` para usuários e treinos.
- Contratos JSON de `POST /users/` e `GET /users/` permanecem, inclusive papéis, normalização e ausência de senha e hash.
- A documentação nova adapta os caminhos do modelo aos arquivos já usados: `docs/arquitetura.md`, `docs/adr/` e `docs/08-projeto.md`. O checklist pede `docs/07-arquitetura/`; a implementação deve acrescentar esse caminho apenas como remissão, sem mover os ADRs.

## Contrato HTTP proposto

| Operação | Endpoint | Sucesso | Erros |
| --- | --- | --- | --- |
| Criar treino | `POST /workouts/` | 201 com o treino | 422 inválido; 404 usuário inexistente; 503 falha de armazenamento |
| Listar treinos | `GET /workouts/` | 200 e lista ordenada por `id`; `[]` se vazia | 503 |
| Consultar treino | `GET /workouts/{id}` | 200 com o treino | 422 id inválido; 404 inexistente; 503 |
| Atualizar treino | `PUT /workouts/{id}` | 200 com o treino atualizado | 422 inválido ou campo imutável; 404; 503 |
| Excluir treino | `DELETE /workouts/{id}` | 204 sem corpo | 422 id inválido; 404, inclusive na exclusão repetida; 503 |
| Contar entidades | `GET /statistics/entities` | 200 com `{"total": N}` | 503 |

Nomes repetidos continuam 201. Não há 409 para treino.

Cada resposta de sucesso com um treino contém exatamente `id`, `user_id`, `name` e `description`; a listagem contém objetos com esses mesmos campos. A resposta da contagem contém exatamente `total`.

No cadastro, o corpo aceita `user_id`, `name` e `description`. Na atualização, aceita apenas `name` e `description`. `name` é obrigatório nos dois casos. Descrição omitida significa `""`; `null` não é aceito. Qualquer campo desconhecido é recusado, inclusive `id` no cadastro e `id` ou `user_id` na atualização, mesmo que repitam o valor existente.

## Fachada e isolamento

`FacadeSingletonController` é a única entrada de negócio usada pelas rotas. Ela delega a `UserService` e ao serviço de treinos recebidos em um contexto por aplicação. A instância da fachada é única no processo e não guarda repositórios nem dados. Cada chamada a `create_app` cria um contexto distinto. Aplicações RAM e aplicações SQLite com arquivos diferentes têm dados independentes; aplicações configuradas com o mesmo arquivo SQLite compartilham intencionalmente os dados persistidos, sem trocar seus contextos. O desenho, as alternativas recusadas e o método `count_entities` estão em [design.md](design.md).

`count_entities` é o nome proposto do método público que retorna um inteiro. O enunciado fixa o nome da classe, não o do método. A contagem proposta é a soma dos usuários, dos dois papéis, com os treinos persistidos naquela aplicação.

## Prazos

O modelo registra a Entrega 2 em **30/10/2026**, com tag `v0.2.0`, por PR de `develop` para `main` depois da revisão. O pedido desta sprint informa que o histórico da equipe também citou **28/10**. O repositório não contém essa data. Esta proposta não escolhe entre as duas. A confirmação fica para o canal oficial da disciplina.

A tag `v0.1.0` permanece na Entrega 1 e não será reutilizada.

## Organização sugerida dos pull requests

O preparo local antecedeu a publicação. Este PR formaliza a revisão da proposta,
sem apresentar uma aprovação de GitHub anterior que não ocorreu. A publicação
da implementação seguirá a integração desta proposta, com checks em cada PR.

1. `rafa/docs-sprint3-proposta` → `develop`. Somente esta change e `openspec/config.yaml`. A proposta já ultrapassa a referência de cerca de 400 linhas: sua descrição de PR deve justificar que contrato, cenários e decisões precisam ser revisados em conjunto antes do código. Não dividir a aprovação em fragmentos incompatíveis apenas para reduzir linhas.
2. Depois da aprovação e do merge da proposta, três PRs para `develop`, nesta ordem, cada um partindo da `develop` atualizada após o merge anterior:
   - `rafa/feat-treinos-persistencia`: ADR 0005, contratos de usuários e de erros, domínio, repositórios, serviço, testes desses contratos e documentação de projeto correspondente.
   - `rafa/feat-treinos-fachada`: fachada, contexto, rotas, esquemas HTTP, testes de CRUD, contagem e isolamento, atualização do ADR e do diagrama de projeto.
   - `rafa/docs-treinos-entrega-2`: casos de uso, wireframes, documentos de produto e arquitetura, validação automatizada da documentação e `openspec archive crud-treinos`.
   Testes e documentação estrutural acompanham os respectivos PRs de código. A referência de tamanho será reavaliada com o diff real de cada PR; exceções precisam de justificativa, sem separar um contrato de suas implementações e testes.
3. A ida a `main`, com tag `v0.2.0`, continua posterior: PR de `develop`, CI e autorização. Não faz parte destes PRs.

Commits sugeridos estão em [tasks.md](tasks.md). Descrição em português, no imperativo, com até 72 caracteres.

## Decisões submetidas à revisão

- Nome do método: `count_entities(context) -> int`.
- Interpretação: total = usuários + treinos.
- `PUT` sem `description` grava descrição vazia.
- Campos desconhecidos e `id` ou `user_id` no corpo da atualização respondem 422 e não alteram o treino.
- Mensagem 503 de treino: `Armazenamento de treinos indisponível`. A mensagem de usuários permanece.
- Ausência de filtro por usuário, de paginação e de restrição por papel.

Essas decisões já estão especificadas nos deltas e no design. Após a aprovação da proposta, não precisam ser novamente decididas durante cada tarefa. Uma mudança posterior de contrato deve voltar à revisão.

## Critérios para concluir a change

- RF08–RF18 e os RNFs afetados têm cenários com testes correspondentes, nos dois modos quando aplicável.
- Os 42 testes da linha de base continuam aprovados; novos testes não substituem comportamentos anteriores sem justificativa.
- Falhas de criação, atualização e exclusão não deixam alterações parciais. A reinicialização recupera todos os campos e a contagem.
- Identidade única da fachada, contextos independentes e compartilhamento intencional do mesmo arquivo SQLite estão demonstrados.
- O ADR existe antes ou junto das mudanças de contrato. Diagramas e documentação representam o código de cada PR.
- A configuração YAML é parseável e seu contexto é realmente carregado; o sucesso de `validate --all` sozinho não comprova isso.
- A validação normal do OpenSpec, Ruff, formatação, testes, links locais e verificações de diff passam. Avisos existentes devem ser relatados, sem confundir avisos de idioma com erros ou ocultar outros avisos.
- A change é arquivada somente após sua implementação completa, com todos os requisitos em vigor atualizados e sem perder requisitos que não foram modificados.
- Aprovação técnica e publicação são etapas distintas: aprovação não autoriza automaticamente commit, push, merge ou tag.
