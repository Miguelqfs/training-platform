# UC04 — Atualizar treino

**Objetivo:** substituir nome e descrição de um treino preservando seu vínculo.
**Ator principal previsto:** Aluno; Administrador também pode operar o protótipo.
**Gatilho:** `PUT /workouts/{id}`.
**Pré-condições de sucesso:** API iniciada e treino existente.
**Requisitos:** RF09, RF12, RF15, RF16; NF-SEG-03, NF-CON-04–06,
NF-MAN-02, NF-USA-02.
**Interface proposta:** [TL03](../06-interface/TL03-atualizar-treino.md).

## Fluxo principal

1. O ator consulta o treino pelo ID e edita nome e descrição.
2. Envia nome obrigatório e descrição opcional ao endereço do treino.
3. A fronteira valida ID positivo na URL e corpo; a fachada delega ao serviço.
4. O serviço normaliza os textos e valida os mesmos limites do cadastro.
5. O repositório substitui os dois campos mutáveis em uma transação.
6. A API retorna 200 com o treino atualizado; ID, vínculo e total permanecem.

## Alternativas e exceções

- **A1 — descrição omitida (2):** grava descrição vazia. PUT substitui ambos
  os campos; não é uma atualização parcial.
- **A2 — corpo inválido (3–4):** 422. Nome ausente, vazio, nulo ou grande,
  descrição nula/grande, campo desconhecido ou presença de `id`/`user_id`
  são recusados, mesmo repetindo valores existentes. Registro anterior intacto.
- **A3 — ID não inteiro positivo (3):** 422; não é ausência de registro.
- **A4 — treino ausente/excluído (5):** 404 `Treino não encontrado`; não recria.
- **E1 — persistência (5):** 503 `Armazenamento de treinos indisponível`;
  todos os campos e demais registros permanecem como antes.

**Pós-condição de sucesso:** nome e descrição substituídos; usuário e outros
planos intactos. **Garantia em falha:** treino completo e total preservados.

**Exemplo:** `PUT /workouts/1` com `{"name":" Costas ","description":" remada "}`
retorna `{"id":1,"user_id":1,"name":"Costas","description":"remada"}`.

[Contrato completo](../../openspec/changes/crud-treinos/specs/treinos/spec.md) · [Índice](README.md)
