# ADR 0008: Contratos públicos do relatório e Template Method

## Status

Aceito na implementação; sujeito à revisão do PR. Cobre **tasks.md 1.1** e **3.1–3.3**.

## Contexto

RF21–RF22 exigem relatório por período em HTML e PDF com agregação única.
O repositório de eventos é a fonte de leitura; a geração fica na camada de negócio.
O registro de operações e sua consistência estão nos [ADRs 0006](0006-repository-factory.md)
e [0007](0007-adapter-log-eventos.md). Não há autenticação: os IDs representam
proprietários dos treinos, não a identidade de quem chamou a API.

## Decisão

### Template Method e agregação

`AccessReportTemplate.generate(start, end)` define o algoritmo na camada de
negócio: validar e normalizar período, consultar `AccessEventRepository` uma vez,
agregar os eventos e chamar o método abstrato `render(report)`.
`HtmlAccessReport` e `PdfAccessReport` herdam esse fluxo e implementam somente
a renderização. A biblioteca de PDF fica em `renderers.py`; o método-base e o
serviço não dependem dela, de SQL ou de HTTP.

`aggregate` produz `AccessReport`, dataclass imutável com início/fim UTC, total e
tuplas de contagens: usuários por ID crescente e operações na ordem `create`,
`get`, `update`, `delete`, incluindo zeros. Período sem eventos tem total zero,
nenhum usuário e quatro operações com zero. As duas somas coincidem com o total.
O repositório aplica o intervalo semiaberto `[start, end)`. Não há relógio novo no
relatório: seu período é explícito; os testes controlam o relógio da captura de eventos.

### Contratos Python e composição

- `AccessReportRequest(start, end, format)` representa a solicitação.
- `GeneratedReport(content: bytes, media_type: str)` representa a saída binária.
- `AccessReportService.generate(request)` escolhe o template pelo formato.
- `ApplicationContext.reports` recebe esse serviço em `create_app`, com os dois
  templates usando o repositório de eventos selecionado pela fábrica da aplicação.
- `FacadeSingletonController.generate_access_report(context, request)` delega ao
  serviço do contexto. A fachada continua Singleton sem guardar estado de negócio.

Chamadores Python que constroem `ApplicationContext` diretamente passam também
o serviço de relatórios. A composição normal via `create_app` permanece compatível.
Consulta de relatório não escreve eventos nem altera a contagem de entidades.

### Biblioteca PDF

Usamos `reportlab>=4.4,<5` como dependência de execução. O
[PLATYPUS do ReportLab](https://docs.reportlab.com/reportlab/userguide/ch5_platypus/)
gera o documento em memória, com parágrafos e tabelas paginadas, sem navegador,
serviço externo ou binário de conversão. `LongTable` repete o cabeçalho nas páginas;
as quatro operações permanecem juntas. Fontes Vera distribuídas pelo próprio
ReportLab são incorporadas para preservar acentos e aparência entre ambientes.
Não são necessários arquivos de fonte do sistema nem fontes novas no repositório.
O documento inclui numeração de páginas e não grava um arquivo no servidor.

`pypdf>=6,<7` é dependência apenas de desenvolvimento, usada para ler os PDFs e
comparar seu conteúdo aos relatórios HTML. Não exigimos igualdade binária entre
PDFs: metadados internos podem variar; o período e as estatísticas são determinísticos.

### HTTP e falhas

`GET /statistics/accesses?start=<RFC3339>&end=<RFC3339>&format=<html|pdf>`:

| Resultado | Contrato |
| --- | --- |
| 200 HTML | `text/html; charset=utf-8`, documento HTML em português. |
| 200 PDF | `application/pdf`, bytes de PDF válido. |
| 422 | Parâmetro ausente/inválido, formato desconhecido, instante sem fuso ou início não anterior ao fim. |
| 503 | `{"detail":"Não foi possível gerar o relatório de acessos"}` para falha de leitura, agregação ou renderização. |

`start` e `end` são obrigatórios, com data, hora com segundos e fuso explícito
(`Z` ou deslocamento `±HH:MM`); aceitam frações de segundo. A fronteira exige
RFC 3339 antes da conversão Pydantic, rejeitando timestamps numéricos e datas
sem hora. O método-base valida também chamadas diretas de negócio e normaliza UTC.
O formato é obrigatório e aceita somente `html` e `pdf` em minúsculas.

`InvalidReportError` sinaliza entrada inválida. `ReportGenerationError` preserva a
causa interna de leitura/geração; seu handler sempre usa a mensagem pública fixa,
sem divulgar SQL, caminhos, dados recebidos ou detalhes da biblioteca. Erros de
validação seguem o contrato existente, sem `input` ou `ctx`. A resposta de sucesso
mostra apenas o período, as contagens e a ressalva sobre o proprietário; não
consulta usuários nem inclui nomes, e-mails, senha, hash ou conteúdo de treino.

## Consequências

Os formatos compartilham validação, consulta e agregação; cada requisição observa
os eventos retornados por sua única leitura. Duas requisições terão os mesmos
dados se não houver alterações no intervalo entre elas. Novos formatos podem
implementar `render` sem duplicar o algoritmo-base.

`tests/test_access_reports.py` verifica equivalência dos dois formatos, limites
do intervalo, UTC, período vazio, validação, erros de leitura/renderização,
paginação, fachada, OpenAPI e fluxo real de eventos em RAM e SQLite. A inspeção
visual inclui PDFs com eventos, vazios e com vários usuários/páginas.

## Alternativas consideradas

- Gerar formatos em camadas distintas com consultas/agregações diferentes: duplica regras e permite divergência.
- Converter HTML por navegador ou motor nativo externo: aumenta os requisitos de implantação para um relatório tabular simples.
- Escrever PDF manualmente: exige manter fontes, tabelas e paginação sem necessidade.
