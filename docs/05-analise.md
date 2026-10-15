# Classes de análise: gerenciamento de usuários

Na visão de análise, a fronteira recebe pedidos de cadastro e listagem; o controle aplica as regras; a entidade representa o usuário cadastrado. Os dois papéis previstos são Aluno e Administrador. O treinador IA será um componente futuro, sem papel de usuário nesta entrega.

```mermaid
classDiagram
    class APIUsuarios {
      <<boundary>>
      +cadastrar(dados)
      +listar()
    }
    class GerenciamentoUsuarios {
      <<control>>
      +cadastrarUsuario(dados)
      +listarUsuarios()
    }
    class Usuario {
      <<entity>>
      +id
      +login
      +email
      +papel
    }
    class Papel {
      <<enumeration>>
      ALUNO
      ADMINISTRADOR
    }
    APIUsuarios --> GerenciamentoUsuarios
    GerenciamentoUsuarios --> Usuario
    Usuario --> Papel
```

As classes de implementação, exceções e alternativas de persistência aparecem no [diagrama de projeto](08-projeto.md).
