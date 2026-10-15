# Elicitação de requisitos

Elicitação é a coleta sistemática de necessidades e regras com pessoas e fontes relacionadas ao produto. Esta primeira iteração registra uma entrevista remota conduzida por Artur em 12/10/2026, um questionário escrito com Artur e uma análise documental em 14/10/2026. A entrevista descreve uma experiência individual; não representa uma amostra estatística de alunos.

## 1. Entrevista remota com praticante

| Campo | Registro |
| --- | --- |
| Data | 12/10/2026; horário não registrado |
| Meio/local | Remoto; plataforma não registrada |
| Participantes | Artur Coelho Batista Guedes Pereira, entrevistador; uma pessoa que guarda treinos no bloco de notas do celular, mantida anônima |
| Registro | [Síntese do relato informado à equipe de documentação](03-elicitacao/anexos/entrevista-praticante.md) |

**Por que esta técnica:** ouvir diretamente uma pessoa que registra treinos permite compreender dificuldades concretas do método atual e expectativas de melhoria.

**Principais achados:**

- É necessário abrir e procurar a nota específica do treino no celular → P1.
- O treino tende a permanecer igual, e a pessoa receia modificá-lo sem orientação → P2.
- A pessoa gostaria de “conversar” com o treino para entender como adequá-lo à própria rotina; o bloco de notas não oferece isso → P3 e orientação para detalhar a IA em sprint futura.

**Limite do registro:** o roteiro original, o horário e a plataforma da entrevista não foram preservados. O registro contém a síntese comunicada por Artur, sem atribuir à pessoa respostas adicionais.

## 2. Questionário escrito com um idealizador

| Campo | Registro |
| --- | --- |
| Data | 14/10/2026 |
| Meio/local | Conversa escrita no Codex, de forma remota |
| Participante | Artur Coelho Batista Guedes Pereira, integrante e idealizador do projeto |
| Condução e registro | Assistente Codex, com respostas fornecidas por Artur |
| Instrumento | [Perguntas e síntese das respostas](03-elicitacao/anexos/questionario-idealizador.md) |

**Por que esta técnica:** consultar diretamente um idealizador permite registrar o problema pretendido, o público, o recorte de dados e a integração prioritária com a IA antes de escrever a visão do produto. As perguntas foram enviadas por escrito e respondidas por Artur nesta conversa.

**Principais achados:**

- O público planejado inclui alunos que acompanham treinos e administradores que operam a plataforma.
- O grupo considera que planilhas, blocos de notas e plataformas separadas podem dispersar o acompanhamento do treino (P1).
- O grupo considera que uma rotina estática repetida semanalmente pode dificultar ajustes (P2).
- O agente de IA é a integração principal planejada, com definição detalhada adiada para sprints futuras.
- A coleta futura de dados pessoais deve se limitar aos pertinentes ao treino, como altura, idade, peso e preferências; esses campos ainda não estão implementados.

**Limite da evidência:** trata-se da visão de um idealizador, sem entrevistas com alunos ou resultados quantitativos. Não se afirma que a frequência ou gravidade de P1 e P2 já tenha sido medida.

## 3. Análise documental do repositório do projeto

| Campo | Registro |
| --- | --- |
| Data | 14/10/2026 |
| Meio/local | Leitura do clone local do repositório `training-platform` |
| Responsável pela análise | Assistente Codex, a partir dos documentos e do código da equipe |
| Material | `README.md`, `docs/specs/usuarios.md`, `docs/arquitetura.md`, ADRs 0001 e 0003, diagramas de usuários e implementação em `app/` |

**Por que esta técnica:** o repositório já contém decisões e comportamento executável para o gerenciamento de usuários. A leitura desses registros permite transformar regras implementadas nas Sprints 1 e 2 em requisitos rastreáveis, sem depender de memória ou criar funcionalidades não previstas.

**Principais achados:**

- A API já cadastra e lista usuários com papéis `student` e `admin` → RF01 e RF04.
- O login tem limite de 12 caracteres, rejeita vazio e números; a senha segue a política IAM padrão → RF02 e RF03.
- Há armazenamento em RAM e SQLite, selecionado no início da execução → RF05 e NF-MAN-01.
- Senha não é retornada em respostas e é armazenada como hash → NF-SEG-01.
- Falhas SQLite durante requisições são traduzidas em HTTP 503 → NF-CON-01.
- Autenticação, autorização, treinos e agente de IA ainda não estão implementados; são limites da versão atual.

## 4. Síntese e rastreabilidade

| Origem | Resultado | Destino na documentação |
| --- | --- | --- |
| Entrevista com praticante | P1: dificuldade de localizar a nota | Visão §2.2; acompanhamento de treino futuro |
| Entrevista com praticante | P2: receio de mudar treino repetido | Visão §2.2; adaptação futura do treino |
| Entrevista com praticante | P3: desejo de conversar sobre o treino | Visão §2.2–2.3; detalhamento futuro do agente de IA |
| Questionário com idealizador | P1: acompanhamento disperso | Visão §2.2; funcionalidade futura de treino |
| Questionário com idealizador | P2: dificuldade de adaptar rotina estática | Visão §2.2; definição futura do agente de IA |
| Questionário com idealizador | Público, dados mínimos e integração prioritária | Visão §2.3–2.5 e glossário |
| Análise documental | Regras de cadastro e listagem | RF01–RF05 |
| Análise documental | Restrições de segurança, falha e substituição de armazenamento | NF-SEG-01, NF-CON-01, NF-MAN-01 |

**Próxima validação:** consultar mais alunos para verificar a frequência de P1, P2 e P3 e detalhar o comportamento do agente de IA. Uma entrevista individual não permite generalizar seus resultados.
