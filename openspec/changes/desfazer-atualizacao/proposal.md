# Proposta: desfazer atualização de treino

**Estado: proposta para revisão; a funcionalidade ainda não foi implementada.**

## Why

Na API atual, a atualização substitui o nome e a descrição do treino, sem oferecer uma operação para recuperar o conteúdo anterior. O [checklist da Sprint 5](https://github.com/rkulesza/mps-modelo/blob/main/docs/00-entregas.md) solicita desfazer a última atualização da entidade principal, uma fachada de negócio baseada em Command e o padrão Memento.

## What Changes

- Propor a capacidade de restaurar o estado anterior à atualização de um treino.
- Guardar somente a última edição de cada treino e consumi-la ao desfazer; uma nova edição cria nova possibilidade de desfazer.
- Registrar `undo` como operação própria no relatório de acessos, associado ao dono do treino, sem identificar o cliente.
- Propor o uso de Memento para guardar e restaurar o estado e de Command nas operações da fachada, preservando o isolamento do contexto por aplicação.
- Especificar cenários, falhas, contratos e responsabilidades na change antes de implementar; registrar o ADR da fachada baseada em Command junto ao primeiro PR que alterar contratos.
- Atualizar o diagrama de projeto e a tabela de padrões quando as implementações forem integradas.

**Fora do escopo:** implementar a funcionalidade neste PR de proposta, múltiplos níveis de histórico, refazer, desfazer exclusões ou cadastros, autenticação e autorização, exercícios, execução de treinos e agente de IA.

## Capabilities

### New Capabilities

- `desfazer-atualizacao`: restauração do estado anterior à atualização de um treino.

### Modified Capabilities

- `relatorio-de-acessos`: propõe modificar RF19, RF21 e RF23 para incluir desfazer como quinta operação. Os demais contratos de treinos e fachada são estendidos pelos novos requisitos, preservando seus IDs.

## Origem das decisões

| Decisão | Origem |
| --- | --- |
| Desfazer a última atualização, Command, Memento e ADR | Checklist da disciplina |
| Um nível de desfazer por treino e operação `undo` no relatório | Escolhas do usuário para esta proposta |
| API, semântica de falha, persistência e atomicidade | Propostas desta change para revisão pela equipe |

## Impact

Alterações futuras atingirão a fachada, o serviço de treinos, a unidade de trabalho, os modos de armazenamento RAM/SQLite, testes e documentação. Não há implementação nem alteração de contrato em vigor neste rascunho.
