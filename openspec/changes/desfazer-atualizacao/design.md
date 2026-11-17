# Design: desfazer atualização de treino

## Escopo e regras

Cada treino possui no máximo um Memento com `name` e `description` imediatamente anteriores ao último `PUT` bem-sucedido, mesmo quando os valores recebidos forem iguais aos atuais. Atualizações sucessivas substituem o Memento anterior. Uma atualização inválida ou malsucedida não modifica o Memento. Criar um treino não cria histórico; excluir o treino apaga seu Memento. Bancos anteriores à mudança iniciam sem Mementos, sem fabricar histórico.

Desfazer restaura ambos os campos, preservando `id` e `user_id`, e consome o Memento. Uma segunda tentativa não pode percorrer edições mais antigas; novo `PUT` bem-sucedido cria um novo Memento. Treinos diferentes têm históricos independentes. Não há refazer, restauração de exclusão ou identidade autenticada.

## Contrato proposto

`POST /workouts/{id}/undo` não exige corpo; usa ID inteiro positivo e passa pela fachada. Sucesso retorna 200 com o treino restaurado nos mesmos quatro campos de uma consulta de treino. ID inválido retorna 422; treino ausente retorna 404; treino existente sem Memento retorna 409 com mensagem pública `Nenhuma atualização disponível para desfazer`; falha de armazenamento retorna 503 com mensagem pública de treinos. Uma requisição malsucedida não muda treino, Memento ou eventos. Sem autorização por papel, continua sendo protótipo local.

## Persistência e concorrência

No `PUT`, leitura do estado anterior, substituição do Memento, atualização e evento `update` pertencem à mesma unidade de trabalho. No desfazer, leitura e consumo do Memento, restauração do treino e evento `undo` pertencem à mesma unidade; falha de qualquer passo ou do commit reverte tudo. O log auxiliar é chamado somente após commit e sua falha não reverte a operação, como no ADR 0007. A restauração não deve chamar o método público de atualização, evitando sobrescrever o Memento ou criar evento `update` adicional.

RAM usa a mesma trava e rollback coordenado da aplicação; o Memento é volátil. SQLite persiste o Memento no mesmo arquivo, mantém dados e eventos existentes e usa a mesma conexão e transação dos treinos e eventos. Aplicações RAM são isoladas; aplicações com o mesmo SQLite compartilham dados confirmados. Atualizações, exclusões e desfazer concorrentes do mesmo treino devem ser serializáveis: nenhuma tentativa pode consumir um Memento duas vezes nem restaurar dados obsoletos após uma atualização confirmada. Conflitos de armazenamento são tratados como falha, sem sucesso parcial.

## Relatórios e dependência da sprint 4

Um desfazer bem-sucedido registra um único evento `undo`, contendo proprietário, operação e instante UTC. Tentativas recusadas não registram eventos. A operação aparece em HTML e PDF, inclusive com contagem zero; os totais e somas continuam coerentes. Eventos anteriores permanecem inalterados. O proprietário associado ao treino não autentica o cliente.

A change `relatorio-de-acessos` ainda está aberta e contém RF19–RF23, incluindo cenário de quatro operações. A equipe deve concluir e arquivar essa change antes de incorporar o delta correspondente à sprint 5; então atualizar integralmente os requisitos afetados e os cenários de período vazio para cinco operações. Enquanto isso, RF24–RF27 desta change descrevem a extensão proposta sem editar a change anterior nem fingir que ela já foi arquivada.

## Command e Memento

A fachada Singleton permanece sem dados nem contexto global. Seus métodos mantêm as assinaturas e resultados existentes e criam/delegam a comandos que recebem o contexto da aplicação; os comandos encaminham operações aos serviços. A nova operação de desfazer também passa por comando. O Memento é uma representação imutável dos campos restauráveis; o serviço de treinos coordena captura e restauração, e o armazenamento conserva o único estado anterior por treino. O ADR da fachada descreve participantes reais, alternativas e contratos junto ao primeiro PR de implementação. Repositórios e unidades de trabalho continuam intercambiáveis e sem SQL na camada de negócio.

As classes concretas, contratos de repositório e migração devem ser documentados no ADR junto à implementação correspondente. Nenhuma dependência externa é exigida pela proposta.
