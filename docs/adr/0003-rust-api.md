# 0003: Reescrever a API em Rust

## Contexto e decisão

A reescrita foi solicitada para substituir o serviço Python/FastAPI por Rust
idiomático. A especificação e os testes de `develop` no commit `163abd6` são a
referência do contrato. Os papéis `student` e `admin` são mantidos. Esta decisão
substitui a stack e a organização Python dos ADRs 0001 e 0002. O escopo continua
sendo criar e listar usuários em memória, sem autenticação ou autorização.

Axum fornece roteamento e extração tipada de JSON; Tokio fornece o runtime,
servidor e sincronização assíncrona; Serde serializa os dados; validator valida
e-mails sem uma expressão regular própria. Tower e serde_json são usados somente
nos testes HTTP, sem precisar abrir uma porta. unicase compara nomes e e-mails
com case folding Unicode, incluindo equivalências como `Straße` e `STRASSE`,
em vez de comparar apenas letras ASCII ou usar uma tabela própria.

Um `Arc<UserService>` compartilha o serviço entre handlers; o serviço possui
`RwLock<Vec<User>>`. A verificação de duplicatas e a inserção acontecem sob o
mesmo lock de escrita, evitando que duas
requisições concorrentes cadastrem o mesmo usuário. Cada construção do router
possui seu próprio estado. Não há lock mantido durante operações de rede.

## Compatibilidade e diferenças públicas

Rotas, campos, IDs sequenciais, ordem de listagem, status 200/201/409 e mensagem
de conflito são preservados. O redirecionamento 307 de `/users` é mantido,
incluindo a query string.
O campo `role` aceita `student` e `admin`, com `student` como padrão quando
omitido. Outros valores são rejeitados com 422. Um enum Rust garante essa
restrição na desserialização. Os dois papéis compartilham as regras de unicidade.
Os nomes têm espaços externos removidos antes da validação de comprimento.
E-mails são armazenados em minúsculas e ambos os campos são comparados sem
distinguir caixa. A fronteira HTTP fica em `src/lib.rs` e os modelos e regras
de cadastro em `src/users.rs`.

Erros de entrada retornam 422 com `detail` textual, em vez da lista estruturada
de erros do Pydantic. JSON sem Content-Type também retorna 422. O limite padrão
do extrator JSON do Axum é 2 MiB; corpos maiores retornam 422 neste serviço.

A validação de e-mail segue o validator (HTML5), não o email-validator do Python.
Espaços externos e caixa do e-mail são normalizados, mas não há equivalência
completa para endereços internacionais, nomes de exibição ou domínios especiais.

As páginas automáticas `/docs`, `/redoc` e `/openapi.json` do FastAPI não são
fornecidas. O README passa a documentar os dois endpoints.

O armazenamento continua volátil e restrito a um processo. Buscas de duplicatas
são lineares; para a API atual, índices adicionais e camadas de repositório não
se justificam.
