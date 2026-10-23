# UC01 — Cadastrar usuário

**Objetivo:** registrar um aluno ou administrador com identidade única.
**Ator principal previsto:** Administrador. A API ainda não exige autenticação.
**Gatilho:** envio do cadastro por `POST /users/`.
**Pré-condições:** API iniciada; repositório disponível para o fluxo de sucesso.
**Requisitos:** RF01, RF02, RF03, RF05, RF06, RF07, RF16; NF-SEG-01,
NF-SEG-02, NF-CON-01–03, NF-MAN-01, NF-USA-01.
**Interface proposta:** [TL01](../06-interface/TL01-cadastrar-usuario.md).

## Fluxo principal

1. O ator informa login, e-mail, senha e papel (padrão `student`).
2. A fronteira valida obrigatoriedade, tipos, e-mail e papel.
3. A fachada delega ao serviço do contexto; o serviço remove espaços externos
   do login, normaliza e-mail e valida as regras de credenciais.
4. O serviço gera hash com salt e solicita cadastro ao repositório.
5. O repositório confirma identidade única, gera o ID e grava o usuário.
6. A API retorna 201 com `id`, `username`, `email` e `role`.

## Alternativas e exceções

- **A1 — entrada inválida (2–3):** 422. Login: 1–12 caracteres sem números
  Unicode; senha: 8–128, três das quatro categorias IAM documentadas,
  diferente do login/e-mail normalizados. A resposta informa a regra ou campo,
  sem reproduzir a senha. Nenhum usuário é gravado.
- **A2 — duplicidade (5):** login ou e-mail já existente sem distinguir caixa
  resulta em 409. Coleção e contagem permanecem.
- **E1 — persistência (4–5):** 503 com mensagem de usuários; transação SQLite
  revertida. Falha na inicialização impede atender antes deste caso de uso.

**Pós-condição de sucesso:** exatamente um usuário a mais; senha original não
é persistida nem publicada. **Garantia em falha:** nenhum cadastro parcial.

**Exemplo:** `{"username":"maria","email":"maria@example.com","password":"Abcdef12"}`
retorna `{"id":1,"username":"maria","email":"maria@example.com","role":"student"}`.

[Contrato completo](../../openspec/specs/usuarios/spec.md) · [Índice](README.md)
