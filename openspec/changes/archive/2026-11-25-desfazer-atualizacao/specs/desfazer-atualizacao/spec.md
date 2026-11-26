## ADDED Requirements

### Requirement: RF24 — Desfazer a última atualização de treino
O sistema DEVE permitir desfazer uma única vez a última atualização bem-sucedida de cada treino, restaurando nome e descrição anteriores e preservando identificador e proprietário.

**Prioridade:** Essencial
**Casos de uso:** UC04, UC10

#### Scenario: Restaurar a atualização mais recente
- **GIVEN** um treino passou de nome Peito e descrição supino para Costas e remada, e depois para Pernas e agachamento
- **WHEN** o cliente desfaz a última atualização do treino
- **THEN** o treino volta a Costas e remada, preservando seu ID e proprietário

#### Scenario: Histórico consumido
- **GIVEN** a última atualização de um treino já foi desfeita
- **WHEN** uma segunda tentativa de desfazer ocorre sem nova atualização
- **THEN** a API retorna 409 e o treino permanece inalterado

#### Scenario: Nova atualização após desfazer
- **GIVEN** uma atualização de treino foi desfeita
- **WHEN** o treino recebe uma nova atualização válida e essa atualização é desfeita
- **THEN** os campos retornam ao estado que tinham imediatamente antes da nova atualização

#### Scenario: Treinos independentes
- **GIVEN** dois treinos têm atualizações pendentes de desfazer
- **WHEN** apenas o primeiro é restaurado
- **THEN** o segundo treino e sua possibilidade de desfazer permanecem inalterados

### Requirement: RF25 — Controlar o estado anterior do treino
O sistema DEVE manter no máximo um estado anterior por treino e atualizá-lo somente junto a uma atualização bem-sucedida; criar ou excluir treino NÃO DEVE gerar estado disponível para desfazer.

**Prioridade:** Essencial
**Casos de uso:** UC03, UC04, UC07, UC10

#### Scenario: Treino recém-criado
- **GIVEN** um treino foi criado e nunca atualizado
- **WHEN** desfazer é solicitado
- **THEN** a API retorna 409 sem alterar o treino

#### Scenario: Atualização inválida
- **GIVEN** um treino possui estado anterior disponível
- **WHEN** uma atualização inválida é recusada
- **THEN** o estado anterior permanece disponível e inalterado

#### Scenario: Atualização com mesmos valores
- **GIVEN** um treino existente
- **WHEN** uma atualização válida repete seus campos atuais
- **THEN** o estado anterior armazenado corresponde aos campos que o treino tinha antes dessa atualização

#### Scenario: Treino excluído ou inexistente
- **GIVEN** um treino foi excluído ou nunca existiu
- **WHEN** desfazer é solicitado para seu ID
- **THEN** a API retorna 404 e não recria o treino

### Requirement: RF26 — Persistir e restaurar atomicamente
O sistema DEVE manter o estado anterior no armazenamento configurado e tratar alteração de treino, estado anterior e evento de acesso como uma unidade atômica.

**Prioridade:** Essencial
**Casos de uso:** UC04, UC07, UC10

#### Scenario: Reinício SQLite
- **GIVEN** um treino foi atualizado com sucesso em SQLite e ainda não foi desfeito
- **WHEN** a aplicação reinicia com o mesmo arquivo
- **THEN** a última atualização ainda pode ser desfeita

#### Scenario: Reinício RAM
- **GIVEN** um treino foi atualizado em uma aplicação RAM
- **WHEN** uma nova aplicação RAM é criada
- **THEN** ela não contém o treino nem seu estado anterior

#### Scenario: Falha durante atualização ou restauração
- **GIVEN** uma falha ocorre na gravação do treino, estado anterior, evento ou commit
- **WHEN** atualização ou desfazer é solicitado
- **THEN** a API retorna 503 e treino, estado anterior e eventos permanecem como antes da requisição

#### Scenario: Tentativas concorrentes
- **GIVEN** um treino possui um único estado anterior disponível
- **WHEN** duas solicitações de desfazer são executadas concorrentemente
- **THEN** no máximo uma conclui a restauração e nenhum estado anterior é consumido duas vezes

### Requirement: RF27 — Registrar desfazer nas estatísticas
O sistema DEVE registrar um evento `undo` por desfazer bem-sucedido e incluí-lo separadamente nas contagens de operação dos relatórios HTML e PDF.

**Prioridade:** Essencial
**Casos de uso:** UC09, UC10

#### Scenario: Desfazer concluído
- **GIVEN** um treino possui uma atualização disponível para desfazer
- **WHEN** a restauração é concluída
- **THEN** um único evento `undo` é associado ao proprietário e não é criado evento `update` adicional

#### Scenario: Relatório sem desfazer
- **GIVEN** um período contém eventos anteriores à introdução de `undo` e nenhum desfazer
- **WHEN** o relatório do período é gerado em HTML e PDF
- **THEN** ambos preservam as contagens dos eventos anteriores e mostram zero para `undo`

#### Scenario: Tentativa recusada
- **GIVEN** um treino não possui atualização disponível para desfazer
- **WHEN** desfazer é solicitado
- **THEN** nenhum evento de acesso é acrescentado
