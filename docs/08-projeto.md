# Projeto: gerenciamento de usuários

## 1. Pacotes e responsabilidades

`app/routers/` e `app/schemas.py` compõem a fronteira HTTP.
`app/error_handlers.py` registra a tradução das exceções em respostas HTTP.
`app/users/service.py` coordena validação, hash, cadastro e listagem;
`app/users/domain.py` contém a entidade, os objetos de cadastro e as exceções;
`app/users/repository.py` oferece o contrato de persistência e as implementações
RAM e SQLite. `app/users/factory.py` escolhe o repositório na inicialização e
`app/users/policy.py` centraliza os limites das credenciais.
A estrutura atual está detalhada em [arquitetura](arquitetura.md).

## 2. Diagrama de classes de projeto

O diagrama mostra o tratamento de erros e os dois mecanismos de persistência pedidos na Sprint 2.

![Diagrama de classes de projeto](diagramas/diagrama-de-classes.png)

Fonte editável: [PlantUML](diagramas/classes-analise-usuarios.puml). A escolha de persistência e o tratamento das falhas estão registrados no [ADR 0003](adr/0003-validacao-persistencia.md).

O [ADR 0004](adr/0004-revisao-entrega-1.md) registra a revisão: o serviço recebe
o repositório obrigatoriamente, `UserRegistration` agrupa a entrada do cadastro e
`NewUser` leva ao repositório somente dados com a senha já convertida em hash.
`InvalidLoginError` e `InvalidPasswordError` especializam a exceção de
credenciais; cada mensagem identifica a regra violada.

## 3. Padrões e evolução

| Elemento atual | Papel no projeto | Situação |
| --- | --- | --- |
| `UserRepository` | Contrato para armazenamento de usuários. | Implementado com RAM e SQLite. |
| `UserService` | Coordena regras de negócio de usuários. | Implementado para o núcleo da Entrega 1. |

A introdução de padrões pedidos nas sprints seguintes será documentada quando cada mudança for proposta e implementada.
