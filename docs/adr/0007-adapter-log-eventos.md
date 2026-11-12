# ADR 0007: Adapter para log auxiliar de eventos

## Status

Aceito na implementação de registro de acessos; sujeito à revisão do PR.

## Contexto

A change [relatorio-de-acessos](../../openspec/changes/relatorio-de-acessos/design.md)
exige um evento por criação, consulta individual, atualização e exclusão de treino
bem-sucedida. Os repositórios e a unidade de trabalho do
[ADR 0006](0006-repository-factory.md) fornecem persistência RAM/SQLite e atomicidade.
O log auxiliar precisa de interface própria, sem acoplar o negócio à biblioteca.

## Decisão

Participantes do Adapter:

| Papel | Participante e responsabilidade |
| --- | --- |
| Cliente | `WorkoutService`: registra o evento obrigatório e solicita log após o commit. |
| Target (porta) | `AccessLogPort.record(event: AccessEvent) -> None`, em `app/accesses/ports.py`. |
| Adapter | `LoggingAccessLogAdapter`, em `app/accesses/logging_adapter.py`: traduz o evento em chamada `Logger.info`. |
| Adaptee | `logging.Logger`, da biblioteca padrão Python; logger padrão `app.accesses`. |

`AccessEvent` contém somente `user_id`, `operation` e `occurred_at` em UTC.
O identificador representa o proprietário do treino, sem autenticar o cliente.
O Adapter formata somente esses três campos, sem ID/nome/descrição de treino,
senha, hash, e-mail, corpo HTTP ou exceção. Não recebe objetos de usuário ou requisição.
Usamos `logging` para evitar uma dependência externa; handlers, destinos e nível
ficam a cargo da configuração da aplicação. O Adapter não altera a configuração
global. Em nível INFO habilitado, emite uma mensagem por chamada bem-sucedida.

### Registro obrigatório e contratos de composição

`WorkoutService` passa a exigir `UnitOfWork` e `access_log: AccessLogPort`, além dos
repositórios de treinos e usuários. Recebe também `clock: Callable[[], datetime]`,
cujo padrão `utc_now` usa o relógio UTC real. `create_app` compõe esses contratos
com a fábrica existente e permite injetar `clock` e `access_log` por aplicação.
Os contratos HTTP e da fachada permanecem; o registro acrescenta a obrigação RF23.

Nas mutações, serviço grava treino e evento dentro de `unit_of_work.transaction()`.
Na consulta individual, lê o treino e grava o evento no mesmo bloco: isso também
reverte um evento cuja gravação lance exceção após a escrita. A resposta só é
produzida após sair do bloco com sucesso. A exclusão lê o proprietário dentro
da transação antes de apagar; não chama a consulta pública nem produz evento `get`.
Listagem, contagem, entradas inválidas e registros ausentes não produzem eventos.

`PersistenceError` durante a transação, inclusive no commit, propaga com a causa
preservada e mensagem pública `Armazenamento de treinos indisponível` (HTTP 503).
O erro sai do bloco transacional para garantir rollback em RAM e SQLite.
O relógio injetado deve fornecer um instante com fuso explícito; `AccessEvent`
normaliza o valor em UTC. Não há eventos retroativos ou deduplicação por sessão.

### Falhas do log auxiliar

Após confirmar a transação, o serviço chama `AccessLogPort.record` uma vez.
Uma exceção desse log é contida pelo serviço, inclusive com um substituto do
Adapter: não altera a resposta, não reverte dados, não repete gravações e não
registra a própria exceção. O repositório de eventos é a fonte dos relatórios.
Não existe garantia de entrega do log auxiliar se a aplicação encerrar após o commit.

## Consequências e validação

Não há novas dependências de execução. Testes podem trocar relógio e porta sem
herança ou infraestrutura de log. Chamadores Python diretos de `WorkoutService`
precisam fornecer a unidade de trabalho e a porta; não há caminho silencioso que
desabilite o registro obrigatório. A consulta individual passa a exigir escrita.

`tests/test_access_recording.py` cobre operações HTTP reais, associação ao dono,
UTC, consultas repetidas, exclusão, operações sem evento, rollback em RAM/SQLite,
falhas reais de SQLite na escrita e no commit, recuperação, reinício e falha do
substituto de log. Também exercita o Adapter real e inspeciona os campos emitidos
com conteúdo sensível proposital nos treinos. A geração dos relatórios e seus
contratos Python permanecem com Miguel no [ADR 0008](0008-relatorio-template-method.md).

## Alternativas consideradas

- Chamar `logging` diretamente no serviço: acopla negócio à biblioteca e não fornece a porta exigida.
- Adicionar biblioteca externa de log: não há necessidade que justifique nova dependência.
- Usar somente log como fonte do relatório: não oferece a persistência e a atomicidade especificadas.
- Logar antes do commit: pode emitir operações que depois serão revertidas.
