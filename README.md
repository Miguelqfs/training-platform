# Training Plataform

Projeto da disciplina de Métodos de Projetos de Software. O produto pretende reunir o acompanhamento de treinos e, em etapas futuras, usar um agente de IA para ajudar o aluno a ajustar seus treinos. A Sprint 3 entrega CRUD de planos de treino vinculados a usuários, fachada única com Singleton/Facade e contagem de entidades, preservando cadastro de usuários e armazenamento em RAM ou SQLite. Os tipos de usuário são aluno (`student`) e administrador (`admin`). O treinador será um agente de IA em uma etapa futura.

## Equipe

| Integrante | Matrícula | GitHub |
| --- | --- | --- |
| Artur Coelho Batista Guedes Pereira | 20240007863 | [@arturpereira12](https://github.com/arturpereira12) |
| Davi de Oliveira Gurgel | 20240007881 | [@Davi-Gurgel](https://github.com/Davi-Gurgel) |
| Luigi Emanuel Martins Schmitt | 20240008047 | [@luigischmitt](https://github.com/luigischmitt) |
| Miguel de Queiroz Fernandes Soares | 20240008109 | [@Miguelqfs](https://github.com/Miguelqfs) |
| Rafael Torres Nobrega Gomes | 20240097646 | [@rafaeltorresng](https://github.com/rafaeltorresng) |

## Documentação de requisitos

- [Visão e descrição geral](docs/01-visao.md)
- [Glossário](docs/02-glossario.md)
- [Elicitação e evidências](docs/03-elicitacao.md)
- [Requisitos funcionais de usuários](openspec/specs/usuarios/spec.md)
- [Requisitos de treinos](openspec/specs/treinos/spec.md) e [fachada](openspec/specs/fachada/spec.md)
- [Interface proposta](docs/06-interface/README.md) e [arquitetura](docs/07-arquitetura/README.md)
- [Requisitos não funcionais](openspec/specs/rnf/)
- [Casos de uso](docs/04-casos-de-uso/README.md), [análise](docs/05-analise.md) e [projeto](docs/08-projeto.md)

## Executar a API

O projeto requer Python 3.12 e usa `pip` para instalar as dependências.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

A documentação interativa fica em `http://127.0.0.1:8000/docs`. Use `POST /users/` para cadastrar e `GET /users/` para listar. Exemplo de cadastro:

```json
{"username": "maria", "email": "maria@example.com", "role": "student", "password": "Abcdef12"}
```

O campo `role` é opcional e assume `student`. Em RAM, os usuários e treinos são perdidos quando a API reinicia. Ainda não há autenticação ou autorização; a API deve ser usada somente como protótipo local.

## Verificar

Instale as ferramentas de desenvolvimento para executar os mesmos checks do CI:

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

O [Ruff](https://docs.astral.sh/ruff/configuration/) verifica erros comuns,
imports, práticas de Python e compatibilidade com Python 3.12. A configuração
fica em `ruff.toml`. Para formatar e aplicar correções automáticas:

```bash
python -m ruff check --fix .
python -m ruff format .
```

As regras da sprint estão em [docs/specs/usuarios.md](docs/specs/usuarios.md), os diagramas em [docs/diagramas/](docs/diagramas/), a estrutura planejada em [docs/arquitetura.md](docs/arquitetura.md) e a decisão da primeira sprint em [docs/adr/0001-usuarios-em-memoria.md](docs/adr/0001-usuarios-em-memoria.md).

## Regras de usuários preservadas da Sprint 2

`username` representa o login: de 1 a 12 caracteres após remover espaços externos,
sem números (incluindo números Unicode). A senha é obrigatória e segue a
[política padrão do AWS IAM](https://docs.aws.amazon.com/pt_br/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html):
8 a 128 caracteres, pelo menos três categorias entre `A-Z`, `a-z`, `0-9` e os
símbolos `!@#$%^&*()_+-=[]{}|'`. Não pode ser igual ao login ou e-mail normalizados.
A senha não é aparada, não expira e nunca aparece nas respostas. Somente um hash
PBKDF2-HMAC-SHA256 com salt aleatório e 600.000 iterações é armazenado.

A escolha de persistência acontece ao iniciar o processo. O padrão é `memory`.
Para manter os dados após reiniciar, use SQLite (biblioteca padrão, sem servidor):

```bash
USER_STORAGE=sqlite USER_DATABASE=users.sqlite3 python -m uvicorn app.main:app
```

O diretório do banco deve existir. SQLite mantém IDs e unicidade também entre
processos. `USER_STORAGE` inválido ou banco inacessível/corrompido interrompem a
inicialização; falhas de leitura ou escrita durante requisições retornam `503`
com mensagem genérica. Uma gravação malsucedida é revertida pela transação.
Entradas inválidas retornam `422` e duplicidades retornam `409`.

O cadastro agora exige `password`, alterando o contrato anterior. A decisão e
as suposições estão no [ADR 0003](docs/adr/0003-validacao-persistencia.md).


## Sprint 3

Treino é um plano com nome e descrição ligado a um usuário existente. Não há
exercícios, execução ou histórico. Nome: 1–100 caracteres; descrição: até 1.000;
espaços externos são removidos. Nomes repetidos são permitidos. O ID do usuário
é inteiro JSON positivo; campos desconhecidos são recusados.

Depois de cadastrar o usuário, envie:

```json
{"user_id": 1, "name": "Peito", "description": "supino"}
```

| Operação | Endpoint | Sucesso | Erros |
| --- | --- | --- | --- |
| Cadastrar treino | POST /workouts/ | 201 | 422, 404 usuário, 503 |
| Listar treinos | GET /workouts/ | 200, lista em ordem de ID | 503 |
| Consultar treino | GET /workouts/{id} | 200 | 422, 404, 503 |
| Atualizar treino | PUT /workouts/{id} | 200 | 422, 404, 503 |
| Excluir treino | DELETE /workouts/{id} | 204 sem corpo | 422, 404, 503 |
| Contar entidades | GET /statistics/entities | 200, `{"total": N}` | 503 |

PUT aceita somente `name` e `description`; omitir descrição grava `""`.
`id` e `user_id` no corpo são recusados mesmo sem mudança de valor. Exclusão
repetida retorna 404. IDs confirmados de treinos não são reutilizados depois de
exclusão. SQLite preserva usuários e treinos no mesmo arquivo já configurado,
inclusive ao iniciar com um banco da Sprint 2.

`FacadeSingletonController.get_instance().count_entities(context)` retorna um
inteiro: usuários dos dois papéis + treinos. A fachada é única por processo e
não guarda dados. Cada aplicação tem seu contexto; RAM e arquivos diferentes
são independentes, enquanto o mesmo SQLite compartilha registros confirmados.
Decisões: [ADR 0005](docs/adr/0005-treinos-fachada.md).

### Verificar a documentação

Com Node.js 20.19 ou superior, instale as versões usadas pelo CI em um diretório
temporário (sem dependências novas para executar a API):

```bash
npm install --prefix /tmp/training-platform-docs --no-save @fission-ai/openspec@1.14.3 yaml@2.8.2
DOCS_TOOLS_DIR=/tmp/training-platform-docs/node_modules node scripts/check-docs.mjs
```

A verificação faz parsing e valida o conteúdo da configuração YAML, confere
links locais e executa `openspec validate --all`. Também exige IDs únicos,
prioridades e referências a casos de uso no formato da disciplina nas specs em
vigor. Os testes desse verificador rodam no CI e podem ser executados com
`node --test scripts/check-specs.test.mjs`. As especificações usam DEVE
em português: o OpenSpec emite avisos por esperar SHALL/MUST. Dois avisos de
texto longo já existem em RF03/NF-USA-01. Esses avisos são relatados; não se usa
`--strict` para confundi-los com falhas nem se dispensa validação por causa deles.
O script funciona também após o arquivamento da change.
