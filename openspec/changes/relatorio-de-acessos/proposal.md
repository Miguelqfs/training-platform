# Proposta: relatório de acessos

**Estado: proposta para revisão; nenhuma funcionalidade desta change está implementada.**

## Why

A [Sprint 4 do professor](https://github.com/rkulesza/mps-modelo/blob/main/docs/00-entregas.md) pede estatísticas de acesso de usuários, Repository e Factory, Adapter e Template Method em relatórios com mais de um formato. A contagem atual de entidades não mede acessos. A API ainda não autentica clientes: o identificador associado a um treino não prova quem fez uma requisição.

## What Changes

- Criar eventos para operações bem-sucedidas de criação, consulta individual, atualização e exclusão de treino, associados ao dono do treino.
- Registrar identificador do dono, operação e instante UTC, sem senha, hash ou corpo da requisição; armazenar em RAM ou SQLite conforme a configuração existente.
- Gerar relatório filtrado por período em HTML e PDF, com total e contagens por usuário e operação, inclusive para período sem eventos.
- Aplicar Repository a usuários, treinos e eventos; Factory Method ou Abstract Factory na composição; Adapter ao log; Template Method à geração dos relatórios na camada de negócio.
- Adicionar a capacidade `relatorio-de-acessos` com RF19–RF23 e a referência proposta UC09. UC03–UC05 e UC07 são os casos existentes cujas operações produzem eventos; a listagem UC06 não produz evento.
- Registrar ADRs Repository + Factory e Adapter junto aos primeiros PRs que alterarem os respectivos contratos, além do ADR necessário para os contratos públicos de eventos e relatórios.

**Fora do escopo:** autenticação, autorização, identificação do autor real da requisição, login, telemetria histórica anterior à implantação, captura de listagens, exercícios, execução de treinos, IA, Command e Memento. Não se promete que a métrica corresponda a pessoas únicas ou sessões.

## Origem das decisões

| Tema | Origem |
| --- | --- |
| Estatísticas de acesso, padrões e separação business/infra | Checklist da Sprint 4 do professor |
| Operações de treino e associação ao proprietário, sem identidade autenticada | Interpretação proposta e escolhida pela equipe para o protótipo atual |
| HTML e PDF, dados exibidos, intervalo e regras de falha | Decisões desta proposta, sujeitas à revisão |
| RAM e SQLite, fachada e contexto por aplicação | Contratos já existentes, a preservar |

## Capabilities

### New Capabilities

- `relatorio-de-acessos`: registro de eventos de uso de treinos e geração de estatísticas.

### Modified Capabilities

- Nenhuma spec em vigor é alterada nesta proposta. O delta novo acrescenta obrigações às operações existentes sem substituir seus requisitos; mudanças de contrato necessárias serão registradas no ADR de implementação.

## Impact

A change acrescenta repositório de eventos, composição por fábrica, porta e Adapter de log, geradores de relatório e uma operação HTTP pela fachada. Usuários e treinos existentes permanecem íntegros, inclusive em bancos SQLite anteriores. Os eventos só existem a partir da implantação e seguem o isolamento da aplicação e o armazenamento escolhido. Não há alteração de código neste PR.

As decisões de projeto, contratos propostos e alternativas estão em [design.md](design.md). As tarefas de implementação e encerramento estão em [tasks.md](tasks.md). Os deltas são propostas para revisão e não substituem as specs em vigor até o arquivamento.
