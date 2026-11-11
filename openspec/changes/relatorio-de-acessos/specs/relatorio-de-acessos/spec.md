## ADDED Requirements

### Requirement: RF19 — Registrar uso de treinos
O sistema DEVE registrar um evento para cada criação, consulta individual, atualização ou exclusão de treino bem-sucedida, associado ao usuário proprietário do treino.

**Prioridade:** Essencial
**Casos de uso:** UC03, UC04, UC05, UC07

#### Scenario: Operações elegíveis
- **GIVEN** um treino pertence ao usuário 7
- **WHEN** cada uma das quatro operações elegíveis termina com sucesso
- **THEN** são registrados quatro eventos, um por operação, associados ao usuário 7

#### Scenario: Operações excluídas
- **GIVEN** existem treinos cadastrados
- **WHEN** ocorre uma listagem, consulta de relatório ou operação inválida, inexistente ou com falha
- **THEN** nenhum evento de acesso é registrado para essa requisição

#### Scenario: Exclusão preserva a associação
- **GIVEN** um treino pertence ao usuário 7
- **WHEN** o treino é excluído com sucesso
- **THEN** o evento de exclusão permanece associado ao usuário 7

### Requirement: RF20 — Preservar dados e persistência dos eventos
O sistema DEVE registrar identificador do proprietário, operação e instante em UTC, sem senha, hash, e-mail ou corpo da requisição, no armazenamento configurado para a aplicação.

**Prioridade:** Essencial
**Casos de uso:** UC03, UC04, UC05, UC07, UC09

#### Scenario: Campos do evento
- **GIVEN** uma operação elegível é concluída
- **WHEN** o evento é armazenado
- **THEN** ele contém o identificador do proprietário, a operação e o instante UTC, sem senha, hash, e-mail ou corpo da requisição

#### Scenario: Reinício com SQLite
- **GIVEN** existe um evento confirmado em SQLite
- **WHEN** a aplicação reinicia com o mesmo arquivo
- **THEN** o evento continua disponível para relatório e os dados anteriores permanecem intactos

#### Scenario: Reinício em RAM
- **GIVEN** existe um evento em RAM
- **WHEN** a aplicação reinicia
- **THEN** o evento não está disponível na nova aplicação

### Requirement: RF21 — Gerar relatório de acessos por período
O sistema DEVE gerar relatório de eventos em um intervalo informado, incluindo início e excluindo fim, com total e contagens por usuário proprietário e por operação.

**Prioridade:** Essencial
**Casos de uso:** UC09

#### Scenario: Filtrar intervalo
- **GIVEN** há eventos antes, no início, dentro e no fim de um período
- **WHEN** o relatório é solicitado para esse período
- **THEN** ele inclui os eventos no início e dentro do período e exclui os anteriores e os do fim

#### Scenario: Período sem eventos
- **GIVEN** nenhum evento ocorreu no período solicitado
- **WHEN** o relatório é gerado
- **THEN** o total é zero, não há usuários listados e as quatro operações têm contagem zero

#### Scenario: Período inválido
- **GIVEN** o início não é anterior ao fim ou um instante não possui fuso explícito
- **WHEN** o relatório é solicitado
- **THEN** a API rejeita a solicitação com 422

### Requirement: RF22 — Disponibilizar formatos de relatório
O sistema DEVE disponibilizar o relatório em HTML e PDF com os mesmos dados agregados e identificação do período em UTC.

**Prioridade:** Essencial
**Casos de uso:** UC09

#### Scenario: Mesmos dados nos formatos
- **GIVEN** há eventos de usuários e operações diferentes no período
- **WHEN** são solicitados relatórios HTML e PDF para o mesmo período sem alteração dos eventos
- **THEN** ambos apresentam o mesmo período, total e contagens por usuário e operação

#### Scenario: Formato inválido
- **GIVEN** o formato solicitado não é HTML nem PDF
- **WHEN** a API recebe a solicitação
- **THEN** ela responde 422 sem gerar relatório

### Requirement: RF23 — Tratar falhas no registro e no relatório
O sistema DEVE impedir sucesso de operação elegível quando o evento obrigatório não puder ser registrado e DEVE informar falhas de armazenamento ou geração de relatório sem expor detalhes internos.

**Prioridade:** Essencial
**Casos de uso:** UC03, UC04, UC05, UC07, UC09

#### Scenario: Falha de registro em mutação
- **GIVEN** a gravação do evento falha durante criação, atualização ou exclusão de treino
- **WHEN** a operação é concluída
- **THEN** treino e eventos permanecem como antes da requisição e a API responde 503

#### Scenario: Falha de registro em consulta
- **GIVEN** um treino existe e a gravação do evento falha
- **WHEN** sua consulta individual é solicitada
- **THEN** a API responde 503 e nenhum evento é confirmado

#### Scenario: Falha de relatório
- **GIVEN** a leitura dos eventos ou a renderização falha
- **WHEN** o relatório é solicitado
- **THEN** a API responde 503 com mensagem genérica sem detalhes internos
