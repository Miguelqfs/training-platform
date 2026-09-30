# Users API

API em Rust com Axum. Os usuários ficam em memória, em ordem de criação, e são
perdidos ao reiniciar o processo. Execute uma única instância para manter uma lista
compartilhada entre todas as requisições.

## Executar

Instale Rust estável com suporte à edição 2024 e execute:

```sh
cargo run --locked
```

O endereço padrão é `127.0.0.1:8000`. Para escolher outro:

```sh
BIND_ADDRESS=0.0.0.0:8000 cargo run --locked
```

Ctrl+C encerra o servidor aguardando requisições em andamento. Em sistemas Unix,
`SIGTERM` também inicia esse encerramento.

## API

- `GET /users/`: lista os usuários (200).
- `POST /users/`: recebe `username`, `email` e `role` opcional; retorna o usuário com `id` e `role` (201).
- Os papéis aceitos são `student` e `admin`; `student` é usado quando `role` é omitido.
- Nomes têm entre 1 e 50 caracteres Unicode depois de remover espaços externos.
- Nome ou e-mail repetido retorna 409, sem distinguir maiúsculas de minúsculas.
- JSON inválido, campos ausentes ou valores inválidos retornam 422.
- `/users` redireciona para `/users/` com 307.

```sh
curl -X POST http://127.0.0.1:8000/users/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"davi","email":"davi@example.com"}'
curl http://127.0.0.1:8000/users/
```

Para cadastrar um administrador, inclua `"role":"admin"` no JSON. O papel
classifica o usuário; autenticação e autorização ainda não foram implementadas.

Os erros usam `{"detail":"mensagem"}`. Nomes e e-mails têm espaços externos
removidos; e-mails são convertidos integralmente para minúsculas.
As regras estão na [especificação](docs/specs/usuarios.md), a organização do
código na [arquitetura](docs/arquitetura.md) e as diferenças em relação ao
FastAPI no [ADR](docs/adr/0003-rust-api.md).

## Verificar

```sh
cargo fmt --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
```
