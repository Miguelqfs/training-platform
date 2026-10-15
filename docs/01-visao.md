# Visão do sistema — Training Plataform

## 1. Introdução

### 1.1 Propósito

Este repositório registra a visão, os requisitos e a implementação inicial do Training Plataform para a equipe, os avaliadores da disciplina e futuros participantes do projeto. O produto pretende facilitar o acompanhamento de treinos por alunos com apoio de um treinador baseado em IA.

### 1.2 Organização

O [glossário](02-glossario.md) define os termos do produto; a [elicitação](03-elicitacao.md) registra a origem dos problemas e decisões; `openspec/specs/` contém os requisitos em vigor. Os diagramas e decisões arquiteturais ficam em `docs/`.

### 1.3 Documentos relacionados

- [Especificação atual de usuários](specs/usuarios.md).
- [Arquitetura proposta](arquitetura.md).
- [Decisão de validação e persistência](adr/0003-validacao-persistencia.md).
- [Modelo de documentação da disciplina](https://github.com/rkulesza/mps-modelo).

## 2. Descrição geral

### 2.1 Motivação

Segundo o relato de um dos idealizadores, pessoas que treinam podem guardar suas rotinas em planilhas, blocos de notas ou plataformas diferentes. Isso dispersa o histórico e dificulta acompanhar e adaptar o plano ao longo do tempo. Uma pessoa entrevistada pela equipe relatou que guarda o treino no bloco de notas do celular, precisa procurar a nota certa e receia mudar uma rotina que permanece igual. Ela gostaria de conversar sobre o próprio treino para entender como adequá-lo à rotina. O grupo propõe concentrar esse acompanhamento em um aplicativo simples e oferecer apoio de um agente de IA para adaptar treinos à rotina. A entrevista traz uma experiência individual, sem medir a frequência desses problemas entre alunos.

### 2.2 Problemas identificados

| ID | Problema relatado pelo idealizador | Impacto esperado | Fonte |
| --- | --- | --- | --- |
| P1 | Informações de treino ficam dispersas entre planilhas, notas e plataformas. | Dificuldade para consultar o treino e acompanhar sua evolução. | Questionário escrito com Artur e entrevista relatada pela equipe. |
| P2 | Uma rotina registrada de modo estático pode permanecer igual semana após semana. | Receio de mudar o treino sem orientação. | Questionário escrito com Artur e entrevista relatada pela equipe. |
| P3 | O bloco de notas não permite dialogar sobre o treino para compreender possíveis adaptações. | Falta de explicação e apoio ao ajustar a rotina. | Entrevista remota de 12/10/2026 com praticante anônimo. |

Esses problemas foram relatados pelo idealizador e por uma pessoa entrevistada pela equipe. A amostra é insuficiente para estimar quantas pessoas enfrentam as mesmas dificuldades.

### 2.3 Visão geral e escopo

O produto planejado deverá permitir que alunos acompanhem seus treinos em um lugar e recebam auxílio de um agente de IA para adaptar a rotina conforme dias disponíveis para treinar e limitações físicas informadas pelo aluno. A entrevista também apontou interesse em conversar sobre o treino e entender as adaptações; o comportamento exato do agente será detalhado em sprints futuras. Administradores operarão a plataforma e, segundo a intenção atual do grupo, realizarão o cadastro e a listagem de usuários. O cadastro e a listagem são o núcleo implementado nas Sprints 1 e 2, mas a API ainda não controla quem pode executá-los. Funcionalidades de treino, aplicativo mobile e agente de IA ainda não funcionam nesta versão.

**Fora do escopo inicial:** coleta de dados pessoais sem relação com o treino e funcionalidades de treino ou IA nesta versão da API. Nenhuma outra integração externa foi definida para o ciclo inicial; novas integrações serão decididas nas próximas sprints.

### 2.4 Usuários e papéis

| Papel | Necessidade | Situação atual |
| --- | --- | --- |
| Aluno | Consultar e acompanhar seus treinos; futuramente interagir com o treinador IA. | Pode ser cadastrado com papel `student`; acompanhamento de treinos ainda não foi implementado. |
| Administrador | Operar a plataforma e, na proposta atual, cadastrar e listar usuários. | Pode ser cadastrado com papel `admin`; autorização por papel ainda não foi implementada. |
| Treinador IA | Auxiliar o trabalho com treinos. | Componente futuro do sistema, não é um tipo de usuário cadastrado. |

### 2.5 Dados, suposições e restrições

- O cadastro atual contém login, e-mail, senha e papel. A senha é armazenada apenas como hash e nunca aparece nas respostas da API.
- O grupo planeja guardar futuramente apenas dados pertinentes ao treino, como altura, idade, peso e preferências de treino. O agente poderá considerar limitações físicas informadas pelo aluno; a necessidade de guardar essa informação ainda não foi definida. Esses campos ainda não existem no código.
- A integração mais importante prevista é com o agente de IA. Seu comportamento e seus limites serão definidos nas próximas sprints.
- A versão atual é um protótipo local sem autenticação nem autorização; o papel informado no cadastro não restringe as operações da API.
- A persistência atual é escolhida na inicialização entre RAM e SQLite. O armazenamento em RAM não sobrevive ao reinício; SQLite sobrevive.
