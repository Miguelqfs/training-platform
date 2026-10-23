# TL02 — Cadastrar treino

[UC03](../04-casos-de-uso/UC03-cadastrar-treino.md) · Interface proposta.

```text
+------------------------------------------------+
| Novo treino                                    |
| Usuário*   [1 - maria v]                        |
| Nome*      [________________________] 0/100     |
| Descrição  [________________________]           |
|            [________________________] 0/1000    |
|                                                |
| [Cancelar]                    [Salvar treino]   |
| Mensagem de resultado / erros por campo         |
+------------------------------------------------+
```

A seleção apresenta usuários existentes de GET /users/ e envia seu ID como
inteiro. Sem usuários, orientar cadastro anterior. Nome obrigatório; descrição
opcional. Limites consideram caracteres após remover espaços externos.

Salvar envia POST /workouts/. Em 201, mostrar ID e plano salvo. Em 422,
identificar campo; em 404, atualizar a seleção de usuários; em 503, indicar
indisponibilidade. Nomes repetidos não geram conflito. Cancelar não grava.
Não há campos de exercício, carga, histórico ou senha nesta tela.
