# Classes de análise: usuários e treinos

A análise representa conceitos do problema e responsabilidades de fronteira,
controle e entidade. Não descreve classes concretas de persistência nem os
mecanismos do Singleton; estes ficam no [projeto](08-projeto.md).

```mermaid
classDiagram
    class APIPlataforma {
      <<boundary>>
      +cadastrarUsuario(dados)
      +listarUsuarios()
      +gerenciarTreino(operacao, dados)
      +consultarQuantidade()
    }
    class GerenciamentoUsuarios {
      <<control>>
      +cadastrar(dados)
      +listar()
    }
    class GerenciamentoTreinos {
      <<control>>
      +cadastrar(dados)
      +consultar(id)
      +listar()
      +atualizar(id, dados)
      +excluir(id)
    }
    class ConsultaQuantidade {
      <<control>>
      +contarUsuariosETreinos()
    }
    class Usuario {
      <<entity>>
      +id
      +login
      +email
      +papel
    }
    class Treino {
      <<entity>>
      +id
      +nome
      +descricao
    }
    class Papel {
      <<enumeration>>
      ALUNO
      ADMINISTRADOR
    }
    APIPlataforma --> GerenciamentoUsuarios
    APIPlataforma --> GerenciamentoTreinos
    APIPlataforma --> ConsultaQuantidade
    GerenciamentoUsuarios --> Usuario
    GerenciamentoTreinos --> Treino
    GerenciamentoTreinos --> Usuario : verifica vínculo
    ConsultaQuantidade --> Usuario
    ConsultaQuantidade --> Treino
    Usuario "1" -- "0..*" Treino : possui
    Usuario --> Papel
```

Treino é um plano, ainda sem exercícios ou execução. Cada treino pertence a
exatamente um usuário existente; um usuário pode não ter treinos. O papel não
impõe autorização no protótipo. Aplicativo e treinador IA permanecem futuros.
