# Design: relatório de acessos

## Contexto e limites

Esta é uma proposta para revisão, não uma descrição de implementação. A API não autentica nem autoriza; `user_id` é o dono associado ao treino, nunca uma alegação sobre o cliente. UC03 (criar), UC05 (consultar), UC04 (atualizar) e UC07 (excluir) originam eventos; UC06 e demais operações não. UC09 será o caso de uso proposto para gerar relatório.

## Eventos e consistência

Um evento contém `user_id` positivo existente no momento da operação, `operation` com um dos valores `create`, `get`, `update`, `delete` e `occurred_at` em UTC. Há exatamente um evento para cada operação elegível que retorne sucesso. O identificador do treino, senha, hash, e-mail e corpo HTTP não integram o evento nem o log do Adapter. A exclusão captura o proprietário antes de apagar o treino.

Operações inválidas, ausências, falhas e listagens não registram eventos. Para criação, atualização e exclusão, mudança do treino e evento são uma unidade atômica: se qualquer gravação falhar, ambas são revertidas e a API responde 503. Em SQLite, usar a mesma conexão e transação; em RAM, operação coordenada com trava e rollback antes de liberar a trava. Para consulta individual, só retornar 200 após registrar o evento; falha no registro retorna 503. Consultar relatório não gera eventos. Não fabricar eventos retroativos ao abrir banco legado.

O horário é obtido de relógio injetável para testes, normalizado em UTC; o intervalo é semiaberto `[start, end)`. Não há deduplicação por cliente ou sessão: duas requisições bem-sucedidas contam dois eventos.

## Contrato proposto

`GET /statistics/accesses?start=<instante>&end=<instante>&format=<html|pdf>` passa pela fachada e pelo contexto da aplicação. `start` e `end` são obrigatórios, em RFC 3339 com fuso explícito, normalizados a UTC; `start` deve ser anterior a `end`. O parâmetro `format` é obrigatório e aceita apenas `html` ou `pdf`. Entrada inválida retorna 422; falha de leitura ou geração retorna 503 com mensagem pública genérica, sem dados internos. Sucesso retorna 200 com `text/html; charset=utf-8` ou `application/pdf`, respectivamente.

O relatório mostra início e fim em UTC, total, contagens por usuário e contagens por operação. Ordenar usuários por ID crescente e operações na ordem `create`, `get`, `update`, `delete`; exibir zero para cada operação sem evento. Nenhum evento no período resulta em total zero, lista de usuários vazia e quatro contagens de operação iguais a zero. A soma das contagens por usuário e a soma das contagens por operação são iguais ao total. Os dois formatos usam o mesmo resultado agregado; nomes ou e-mails não são necessários.

## Padrões e limites entre camadas

- **Repository:** protocolos de usuários, treinos e eventos são dependências da camada business; RAM e SQLite são implementações de infra. O contrato de escrita coordenada deve permitir a atomicidade acima, sem espalhar SQL pelos serviços.
- **Factory Method ou Abstract Factory:** uma fábrica selecionada na inicialização cria o conjunto coerente de repositórios e a unidade de trabalho para o mesmo modo e arquivo; cada aplicação recebe seu contexto. A implementação escolherá uma das duas variantes aceitas, registrando participantes e justificativa no ADR Repository + Factory.
- **Adapter:** uma porta de log de eventos recebe somente `user_id`, operação e instante; um Adapter encapsula a biblioteca de log escolhida. O repositório de eventos é a fonte do relatório. Falha de log auxiliar não altera o resultado da operação nem cria, remove ou duplica eventos; o mecanismo de falha do log não deve gerar recursão ou expor dados sensíveis. Registrar escolha e dependência no ADR e PR.
- **Template Method:** na camada business, um fluxo-base valida período, obtém e agrega os eventos e delega a renderização a implementações HTML e PDF. A escolha da biblioteca PDF e sua justificativa acompanham o PR correspondente; a geração usa dados agregados, sem consultas distintas por formato.
- A fachada delega ao serviço do contexto e permanece Singleton sem guardar dados ou contexto global. O comportamento e a contagem de entidades anteriores permanecem inalterados; eventos não passam a compor essa contagem.

## Implantação, falhas e compatibilidade

Criar a estrutura SQLite de eventos de forma compatível com arquivos existentes, sem apagar tabelas ou reescrever dados. Reabrir o banco preserva eventos; RAM perde eventos ao reiniciar. Duas aplicações RAM permanecem isoladas; aplicações com o mesmo arquivo SQLite compartilham eventos confirmados. Erros de banco ou de renderização não divulgam exceções internas, caminhos ou entradas sensíveis. Nenhuma garantia nova de autorização é introduzida: a API permanece protótipo local.

Os ADRs devem acompanhar o primeiro PR que alterar contratos. O PR de integração atualiza diagramas, tabela de padrões, casos de uso e documentação para refletir o código real. O arquivamento ocorre somente após implementação e validação completas.
