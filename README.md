# Training Platform

Projeto da disciplina de Métodos de Projetos de Software. A primeira sprint entrega uma API para cadastrar e listar usuários em memória. Os tipos de usuário são aluno (`student`) e administrador (`admin`). O treinador será um agente de IA em uma etapa futura.

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
{"username": "maria", "email": "maria@example.com", "role": "student"}
```

O campo `role` é opcional e assume `student`. Os usuários são perdidos quando a API reinicia. Ainda não há autenticação ou autorização; a API deve ser usada somente como protótipo local.

## Testar

```bash
python -m unittest discover -s tests
```

As regras da sprint estão em [docs/specs/usuarios.md](docs/specs/usuarios.md), os diagramas em [docs/diagramas/](docs/diagramas/) e a decisão arquitetural em [docs/adr/0001-usuarios-em-memoria.md](docs/adr/0001-usuarios-em-memoria.md).
