## MODIFIED Requirements

### Requirement: RF19 — Registrar uso de treinos
O sistema DEVE registrar um evento para cada criação, consulta individual, atualização, exclusão ou desfazer atualização de treino bem-sucedida, associado ao usuário proprietário do treino.

**Prioridade:** Essencial
**Casos de uso:** UC03, UC04, UC05, UC07, UC10

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


#### Scenario: Desfazer atualização
- **GIVEN** um treino de proprietário 7 tem uma atualização disponível para desfazer
- **WHEN** desfazer é concluído
- **THEN** exatamente um evento undo é associado ao proprietário 7, sem evento update adicional

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
- **THEN** o total é zero, não há usuários listados e as cinco operações têm contagem zero

#### Scenario: Período inválido
- **GIVEN** o início não é anterior ao fim ou um instante não possui fuso explícito
- **WHEN** o relatório é solicitado
- **THEN** a API rejeita a solicitação com 422


#### Scenario: Contagem separada de desfazer
- **GIVEN** um período contém eventos update e undo
- **WHEN** o relatório do período é solicitado
- **THEN** as contagens de atualização e de desfazer são apresentadas separadamente e incluídas no total

### Requirement: RF23 — Tratar falhas no registro e no relatório
O sistema DEVE impedir sucesso de operação elegível quando o evento obrigatório não puder ser registrado e DEVE informar falhas de armazenamento ou geração de relatório sem expor detalhes internos.

**Prioridade:** Essencial
**Casos de uso:** UC03, UC04, UC05, UC07, UC09, UC10

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

#### Scenario: Falha de registro ao desfazer
- **GIVEN** a gravação do evento undo falha durante a restauração
- **WHEN** desfazer é solicitado
- **THEN** treino, estado anterior e eventos permanecem inalterados e a API responde 503
