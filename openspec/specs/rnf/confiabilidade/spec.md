# Confiabilidade do armazenamento

## Purpose

Comunicar indisponibilidade e garantir atomicidade e durabilidade no SQLite.

## Requirements

### Requirement: NF-CON-01 — Tratar falhas de persistência

Nas requisições afetadas por `sqlite3.Error` de leitura ou escrita, o sistema DEVE retornar HTTP 503 com exatamente `{"detail":"Armazenamento de usuários indisponível"}`, sem SQL ou caminhos internos. Conflitos de unicidade são erros de negócio (HTTP 409), não indisponibilidade.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Banco indisponível

- **GIVEN** o banco iniciado e a tabela `users` removida para simular falha
- **WHEN** o cadastro ou a listagem é solicitado
- **THEN** ambas as operações retornam HTTP 503 com a mensagem especificada

### Requirement: NF-CON-02 — Garantir atomicidade do cadastro

Uma gravação SQLite malsucedida DEVE deixar 0 usuários novos e preservar os usuários anteriores.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Falha após a inserção

- **GIVEN** 1 usuário no banco e um gatilho `AFTER INSERT` que aborta a gravação
- **WHEN** um segundo cadastro válido é enviado
- **THEN** retorna HTTP 503 e continuam exatamente 1 usuário na API e 1 linha no banco

### Requirement: NF-CON-03 — Preservar dados após reinicialização

Ao reiniciar a aplicação em modo SQLite usando o mesmo arquivo, 100% dos usuários confirmados DEVEM manter seus IDs e dados e continuar sujeitos às mesmas restrições de unicidade. O próximo cadastro DEVE receber um novo ID. Este requisito não se aplica ao modo RAM.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Nova instância com o mesmo banco

- **GIVEN** 1 usuário confirmado no arquivo SQLite
- **WHEN** a aplicação é recriada com esse arquivo
- **THEN** lista o mesmo usuário com o mesmo ID, rejeita seu recadastro com HTTP 409 e atribui ID 2 a um novo usuário

A verificação recria a aplicação e suas conexões; não simula queda de energia nem corrupção de disco.
