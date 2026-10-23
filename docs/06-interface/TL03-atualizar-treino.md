# TL03 — Atualizar treino

[UC04](../04-casos-de-uso/UC04-atualizar-treino.md) · Interface proposta.

```text
+------------------------------------------------+
| Editar treino #1                               |
| Usuário: 1 - maria (somente leitura)            |
| Nome*      [Peito___________________] 5/100     |
| Descrição  [supino__________________]           |
|            [________________________] 6/1000    |
|                                                |
| [Cancelar]                  [Salvar alterações]|
| Mensagem de resultado / erros por campo         |
+------------------------------------------------+
```

Carregar com GET /workouts/1. ID e usuário são somente leitura e não entram no
corpo de PUT. Sempre enviar nome e descrição; texto vazio limpa a descrição.
Explicar antes de salvar que a atualização substitui ambos os campos.

Salvar envia PUT /workouts/1. Em 200, substituir o conteúdo exibido pelo retorno.
Em 422, mostrar a regra e manter a edição; em 404, informar treino ausente; em
503, informar indisponibilidade e permitir nova tentativa. Cancelar descarta
somente a edição local. A API não mantém histórico nem oferece desfazer.
