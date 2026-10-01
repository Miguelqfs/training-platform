# ADR 0003: Validação de credenciais e persistência selecionável

## Estado

Aceito para o Sprint 2. Substitui a restrição de RAM do ADR 0001.

## Decisão

Manter Python 3.12/FastAPI da develop. `username` continua representando login,
com limite reduzido de 50 para 12 caracteres e proibição de números Unicode.
Exigir `password` no POST, sem incluí-lo no esquema de resposta. Essa é uma
alteração incompatível para clientes anteriores, que devem enviar senha válida.

Como a atividade não define uma política IAM personalizada, adotar a política
padrão documentada pela AWS: 8 a 128 caracteres, três de quatro categorias e
sem expiração. Adaptar a restrição de nome/e-mail da conta AWS para login/e-mail
do usuário local, pois o projeto não tem contas AWS. Não implementar políticas
opcionais de histórico, expiração ou redefinição administrativa nesta etapa.

Validar credenciais no serviço com exceções de domínio e traduzir erros para
HTTP 422; duplicidades continuam em 409. Usar `SecretStr` na entrada e hash
PBKDF2-HMAC-SHA256 com 600.000 iterações e salt aleatório de 16 bytes, via biblioteca
padrão, nos dois mecanismos. Não implementar autenticação nesta etapa.

Extrair `UserRepository` como protocolo, com implementações RAM e SQLite.
Escolher com `USER_STORAGE` na inicialização, usando `USER_DATABASE` para o
arquivo SQLite. SQLite atende à opção de BD da atividade, sem dependências
externas. Transações evitam cadastro parcial; índices únicos com chaves casefold
mantêm a mesma unicidade Unicode da RAM, inclusive com processos concorrentes.
Conexões são abertas por operação e sempre fechadas.

Converter `sqlite3.Error` em `PersistenceError` preservando a causa. Inicialização
malsucedida impede servir requisições; falhas em execução retornam 503 sem expor
SQL ou caminhos internos. Configuração desconhecida falha explicitamente.

## Consequências

RAM continua volátil. SQLite persiste dados sensíveis derivados da senha; seu
arquivo exige proteção operacional. Não há migração de dados de RAM nem
alteração de bancos preexistentes de outro formato. O protótipo continua local,
sem autenticação ou autorização. Treinos e a stack futura permanecem fora do escopo.
