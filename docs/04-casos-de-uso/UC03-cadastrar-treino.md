# UC03 — Cadastrar treino

**Objetivo:** guardar um plano de treino vinculado a um usuário.
**Ator principal previsto:** Aluno; Administrador também pode operar o protótipo.
**Gatilho:** `POST /workouts/`.
**Pré-condições de sucesso:** API iniciada e usuário já cadastrado no contexto.
**Requisitos:** RF08, RF09, RF14, RF15, RF16; Sprint 4: RF19, RF20, RF23.
NF-SEG-03, NF-CON-04–06, NF-MAN-02, NF-USA-02.
**Registro de evento:** [Luigi — guia Sprint 4](../sprint4/luigi-registro-acessos.md).
**Interface proposta:** [TL02](../06-interface/TL02-cadastrar-treino.md).

## Fluxo principal

1. O ator informa `user_id`, `name` e, opcionalmente, `description`.
2. A fronteira exige ID inteiro JSON positivo e recusa campos desconhecidos.
3. A fachada delega ao serviço do contexto. Nome e descrição perdem espaços
   externos; nome tem 1–100 caracteres e descrição tem até 1.000.
4. O serviço verifica se o usuário existe no mesmo repositório de usuários.
5. Em transação compartilhada, o repositório confirma o treino e registra evento `create` para o proprietário.
6. A API retorna 201 com os quatro campos e a contagem aumenta em um.

## Alternativas e exceções

- **A1 — descrição omitida (1):** grava `""`; espaços apenas também viram vazio.
- **A2 — nome repetido (5):** cadastro continua permitido, com novo ID.
- **A3 — tipo/campo/limite inválido (2–3):** 422 identificando o campo, sem
  escrita. `null` não é descrição válida; `true`, `1.0` e `"1"` não são IDs JSON
  inteiros estritos. O cliente não pode enviar `id`.
- **A4 — vínculo ausente (4–5):** 404 `Usuário não encontrado`; não há treino.
- **E1 — falha de persistência, inclusive busca do vínculo:** 503
  `Armazenamento de treinos indisponível`, preservando causa internamente.

**Pós-condição de sucesso (Sprint 4):** treino adicional e evento `create` consultável,
sem modificar o usuário. **Garantia em falha:** treino e eventos anteriores
preservados; falha na transação responde 503 (RF23).

**Exemplo:** `{"user_id":1,"name":" Peito ","description":" supino "}`
retorna `{"id":1,"user_id":1,"name":"Peito","description":"supino"}`.

[Contrato completo](../../openspec/specs/treinos/spec.md) · [Índice](README.md)
