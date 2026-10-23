# TL01 — Cadastrar usuário

[UC01](../04-casos-de-uso/UC01-cadastrar-usuario.md) · Interface proposta.

```text
+------------------------------------------------+
| Novo usuário                                   |
| Login*   [________________________]             |
| E-mail*  [________________________]             |
| Senha*   [••••••••________________]             |
| Papel    [Aluno v]                              |
|                                                |
| [Cancelar]                 [Cadastrar usuário]  |
| Mensagem de resultado / erros por campo         |
+------------------------------------------------+
```

Login: até 12 caracteres, sem números. Papel oferece Aluno (`student`, padrão)
e Administrador (`admin`). A senha é mascarada; sua política aparece como ajuda
antes do envio, conforme [contrato](../../openspec/specs/usuarios/spec.md).
Campos com asterisco são obrigatórios.

Cadastrar envia POST /users/. Em 201, mostrar ID/login/e-mail/papel e limpar a
senha. Em 422, associar erro ao campo ou regra; em 409, informar identidade já
cadastrada; em 503, informar indisponibilidade sem detalhes internos. Cancelar
abandona a tela sem requisição de cadastro. Não reproduzir a senha no resultado.
