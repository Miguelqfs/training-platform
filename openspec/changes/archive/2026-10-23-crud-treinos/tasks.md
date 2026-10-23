# Tasks

Implementação e publicação autorizadas em 23/10/2026. As tarefas foram
organizadas em commits pequenos por responsabilidade. As mensagens junto aos
itens são referências do planejamento; o histórico Git registra as efetivas.

## 1. Primeiro PR: domínio e persistência

- [x] 1.1 Registrar ADR 0005 antes ou junto da primeira alteração de contrato, incluindo interfaces, mensagens públicas, relacionamento, escopo do Singleton e decisões de isolamento. Commit: `docs(adr): registrar contratos e fachada da sprint 3`
- [x] 1.2 Acrescentar `get_by_id` e `count` a `UserRepository` e `count_users` a `UserService`, com implementações RAM/SQLite e testes, inclusive o repositório substituto. Preservar cadastro e listagem. Commit: `feat(usuarios): consultar usuário por id e contar registros`
- [x] 1.3 Estender `PersistenceError` com mensagem pública padrão compatível com usuários, mantendo causa interna e aceitando somente mensagens públicas constantes nas chamadas novas. Incluir testes do contrato antes do primeiro uso nos repositórios de treinos. Commit: `refactor(erros): definir mensagens públicas de persistência`
- [x] 1.4 Criar constantes, DTOs congelados, exceções, protocolo e serviço de treinos. Incluir testes de normalização, tipos, limites, vínculo e contratos substitutos no mesmo commit. Commit: `feat(treinos): adicionar domínio e serviço de treinos`
- [x] 1.5 Implementar RAM com coleção própria, trava e IDs monotônicos. Incluir testes de CRUD, ordenação, exclusão do maior ID, concorrência e contagem. Commit: `feat(treinos): armazenar treinos em memória`
- [x] 1.6 Implementar SQLite com FK, pragma em cada conexão, transações e `AUTOINCREMENT`. Incluir testes de todas as operações, banco legado, reinício completo, exclusão persistida, falhas de leitura e rollback de INSERT/UPDATE/DELETE. Commit: `feat(treinos): armazenar treinos em sqlite`
- [x] 1.7 Atualizar responsabilidades dos módulos e o diagrama de projeto para o código deste PR, sem desenhar a fachada como implementada antes dela existir. Commit: `docs(projeto): representar a persistência de treinos`

## 2. Segundo PR: fachada, rotas e contagem

- [x] 2.1 Adicionar contexto e fachada sem estado global de negócio. Testar identidade via construtor e accessor, inclusive a primeira criação concorrente em processo novo, e operações delegadas aos contextos corretos. Commit: `feat(fachada): adicionar fachada única por processo`
- [x] 2.2 Fazer `create_app` resolver a configuração uma vez e compor os repositórios/serviços do contexto, sem reiniciar a fachada. Testar precedência dos argumentos, RAM independente, SQLite em arquivos diferentes e duas aplicações ativas no mesmo arquivo. Commit: `refactor(app): compor usuários e treinos no contexto`
- [x] 2.3 Adicionar esquemas, rotas e tratadores HTTP juntos aos testes de cada operação; passar também as rotas de usuários pela fachada. Cobrir campos desconhecidos/imutáveis, tipos estritos no JSON, PUT com substituição e conversão normal de ID na URL. Commit: `feat(api): expor crud de treinos pela fachada`
- [x] 2.4 Completar testes de indisponibilidade de todas as operações HTTP e de rollback nas três mutações, preservando a mensagem de usuários. Cobrir falha da busca do usuário durante cadastro de treino, sem falso 404. Commit: `test(api): verificar indisponibilidade e atomicidade de treinos`
- [x] 2.5 Verificar contagem após operações e reinício, ausência de credenciais, texto legítimo coincidente com senha, primeira aplicação após a segunda e uso efetivo da fachada por todas as rotas. Os testes básicos já acompanham as tarefas anteriores. Commit: `test(fachada): completar cenários de contagem e isolamento`
- [x] 2.6 Atualizar ADR 0005, diagrama real e tabela de Singleton/Facade junto da introdução da fachada. Commit: `docs(projeto): representar a fachada e seus participantes`

## 3. Terceiro PR: documentação e conclusão da change

- [x] 3.1 Detalhar UC01 e acrescentar UC03 e UC04; atualizar o diagrama geral distinguindo o que foi implementado do aplicativo e do agente já descritos na visão. Commit: `docs(casos-de-uso): detalhar usuários e treinos`
- [x] 3.2 Acrescentar wireframes TL01–TL03 em `docs/06-interface/`. Commit: `docs(interface): propor wireframes dos casos detalhados`
- [x] 3.3 Atualizar análise conceitual e conferir a correspondência entre diagrama real, imagem, tabela de padrões e ADR já presentes nos PRs de código. Commit: `docs(analise): representar os conceitos de treinos`
- [x] 3.4 Atualizar arquitetura lógica e física, a tabela dos RNFs, visão, glossário e README. Remeter `docs/07-arquitetura/` aos arquivos existentes, sem mover ADRs. Commit: `docs(arquitetura): relacionar requisitos e decisões da sprint 3`
- [x] 3.5 Acrescentar validação de documentação ao CI: parsing, tipos e conteúdo do YAML, OpenSpec e links locais, sem depender da existência de uma change específica. Fixar a versão da ferramenta, sem dependência de execução nova na API. Validar o job antes e depois do arquivamento. Commit: `chore(ci): validar configuração e especificações do projeto`
- [x] 3.6 Arquivar a change somente depois da implementação, dos testes e das validações finais, aplicando o delta em `openspec/specs/` sem perder requisitos inalterados. Revalidar as specs após arquivar. Commit: `docs(openspec): arquivar a change de treinos`

## 4. Verificação

- [x] 4.1 Com o Python 3.12 do ambiente, executar `python -m ruff check .`, `python -m ruff format --check .`, `python -m pytest` e `git diff --check`.
- [x] 4.2 Executar `openspec validate --all` com `@fission-ai/openspec@1.14.3`, fazer parsing real do YAML e confirmar contexto/regras por `openspec instructions` enquanto a change está aberta. Depois de arquivar, repetir a validação das specs/configuração sem depender daquele caminho de change. Relatar todos os avisos; validação das specs não substitui validação da configuração.
- [x] 4.3 Confirmar que a suíte anterior continua passando e que os cenários novos têm teste observável; executar cada cenário nos dois modos quando aplicável. Conferir a matriz abaixo.
- [x] 4.4 Conferir fontes/imagens dos diagramas, links locais e execução local dos passos do CI; medir cobertura comparável. A execução hospedada será conferida no PR, após autorização de publicação.

## Matriz de aceitação para a implementação

| Requisito | Evidência mínima a executar |
| --- | --- |
| RF08, RF09 | Criar com usuário real; nomes repetidos; trim; campos obrigatórios; limites; tipos JSON; campo extra; vínculo ausente; nenhuma escrita em rejeição. |
| RF10, RF11 | Consulta por ID, ausência real, ID inválido, lista vazia e ordenação após excluir um item. |
| RF12 | Atualização completa; descrição omitida vira vazia; id/user_id sempre recusados no corpo; todos os campos anteriores preservados em erro. |
| RF13, RF14 | Exclusão sem corpo, repetição 404, usuários e demais treinos intactos; IDs não reutilizados após excluir maior/anterior; criação concorrente RAM. |
| RF15, NF-CON-06 | Seleção única por configuração; banco legado sem tabela nova; reabertura sem esvaziar tabela existente; quatro campos e exclusões preservados; IDs e total corretos. |
| RF16 | Cadastro/listagem de usuários, cinco operações de treinos e contagem efetivamente passam pela fachada. |
| RF17 | Soma inclui student e admin; total vazio, pós-exclusão, pós-atualização, pós-rejeição e pós-reinício. |
| RF18 | Identidade única, construção concorrente inicial, contextos próprios, RAM e arquivos distintos isolados, mesmo SQLite compartilhado e primeira aplicação ainda funcional. |
| NF-CON-01, NF-CON-04 | Mensagem de usuários preservada; 503 em cada rota de treinos; erro ao buscar vínculo; contagem com falha em cada repositório; erro interno não confundido com ausência 404. |
| NF-CON-05 | Falhas após INSERT, UPDATE e DELETE com estado completo e total preservados; recuperação depois de remover o gatilho. |
| NF-SEG-01, NF-SEG-03 | Somente campos públicos; erros sem input/ctx e sem valor sensível extra; nome legítimo igual à senha continua aceito; exclusão com corpo vazio. |
| NF-MAN-01, NF-MAN-02 | Contratos substitutos completos, sem herança de classes concretas nem SQL/HTTP no serviço. |
| NF-USA-02 | Erros de campo na fronteira; uma regra por exceção de domínio, com precedência explícita e sem depender da ordem da suíte. |

Os cenários da matriz foram implementados e executados. A suíte passou de 42 para 210 testes; a linha de base foi executada separadamente para comparação de cobertura.

## Commits e pull requests

Os commits usam Conventional Commits, escopo do módulo e descrição em português no imperativo. Testes acompanham o código correspondente; commits adicionais de teste completam a cobertura, sem adiar toda a verificação. Cada PR precisa passar seus checks antes de entrar em `develop`. A divisão, as dependências entre PRs e a justificativa de tamanho estão em `proposal.md`. A proposta foi integrada no PR #11; persistência no PR #12; fachada/API no
PR #13, todos com CI aprovado. A documentação e o arquivamento são publicados
neste PR. A release fica para a validação integrada e o PR develop → main.


## Evidências de validação local — 23/10/2026

- Python 3.12: 210 testes aprovados com `-W error`, sem avisos; os 42 testes
  anteriores permanecem. Verificador da disciplina: 7 testes Node.js aprovados.
- Ruff e formatação aprovados; `git diff --check` sem erros.
- Coverage 7.17.0, `--branch --source=app`: linha de base em cópia isolada
  de `5a6292a`, 99,13% (208/209 linhas, 21/22 ramos); implementação, 99,51%
  (557/558 linhas, 52/54 ramos). O ramo concorrente inicial da fachada é
  exercitado em subprocesso novo, fora da coleta do processo principal.
  A linha não executada é a rejeição de Python diferente de 3.12 já presente.
- `scripts/check-docs.mjs`: YAML, tipos/conteúdo, links e OpenSpec aprovados
  antes e depois do arquivamento (7 specs aprovadas, 0 falhas). Testes negativos rejeitaram YAML quebrado,
  contexto/regras com tipos inválidos e link inexistente, restaurando os arquivos.
- `openspec instructions design --change crud-treinos --json`: contexto e
  regras efetivamente carregados da configuração, sem fallback silencioso.
- Servidor Uvicorn real nos dois modos: inicialização por ambiente, OpenAPI,
  cadastro de usuário, CRUD de treino e contagem aprovados por HTTP local.
- PlantUML 1.2026.2/Smetana: três fontes renderizadas e PNGs inspecionados.
- Arquivamento conferido: 14 IDs anteriores preservados, 11 requisitos não
  afetados idênticos, 17 adições e 3 alterações previstas. Nenhum requisito
  removido ou renumerado. OpenSpec normal: sem falhas. Avisos SHALL/MUST correspondem ao uso de DEVE;
  os dois avisos de texto longo são anteriores (RF03 e NF-USA-01).
- Os testes abrangem os dois modos, contratos substitutos, construção inicial
  concorrente, isolamento, banco legado, reinício, FK e rollback de três
  mutações com preservação dos outros treinos, usando gatilhos ABORT e FAIL.
  Depois de esvaziar a coleção, IDs continuam monotônicos nos dois modos. IDs positivos além de 64 bits
  retornam ausência real, sem overflow do driver nem alteração do contrato.

### Revisão de conformidade e robustez

Conferidos novamente o CONTRIBUTING e o checklist da Entrega 2 do
[modelo do professor](https://github.com/rkulesza/mps-modelo/blob/main/docs/00-entregas.md).

- A visão complementar de exceções mantém as validações da Sprint 2 e mostra
  as novas exceções e sua tradução HTTP, junto ao diagrama principal atualizado.
- Mensagens dos limites de treino derivam das mesmas constantes da validação.
  Não houve alteração dos limites nem dos textos públicos.
- O OpenAPI descreve IDs positivos, total não negativo e erros por operação.
  O esquema de 422 aceita tanto a mensagem de domínio quanto erros por campo,
  conforme respostas reais verificadas nos testes, sem mudar os corpos HTTP.
- A verificação de documentação exige IDs únicos, prioridade prevista e casos
  de uso nas specs em vigor. O verificador anterior aceitava prioridade “Alta”;
  a reprodução confirmou o defeito e o atual rejeita essa entrada. Sete testes
  automáticos cobrem aceitação e rejeição; estão integrados ao job de documentação.
- Conferidas as assinaturas de funções de produção e testes: até três parâmetros
  explícitos, desconsiderando `self` e `cls`; casos parametrizados foram agrupados.
- A cobertura combinada acima corresponde a linhas e ramificações Python;
  testes Node.js são relatados separadamente. Não há alegação de 100% de cobertura.

A integração foi organizada em commits pequenos, preservados por merge commits
nos PRs #11–#13. Cada commit passou localmente por testes, Ruff, formatação e
OpenSpec; cada PR passou no CI antes da integração. A documentação representa
o estado final do código. O CI desta etapa será conferido antes do merge;
a release v0.2.0 será criada somente após o PR develop → main aprovado nos checks.
