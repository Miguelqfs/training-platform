# Diagramas

| Fonte editável | Imagem correspondente |
| --- | --- |
| [Classes de projeto](classes-analise-usuarios.puml) | [PNG](diagrama-de-classes.png) |
| [Command e Memento](command-memento.puml) | [PNG](command-memento.png) |
| [Validação e exceções](excecoes-validacao.puml) | [PNG](excecoes-validacao.png) |
| [Casos de uso](casos-de-uso-usuarios.puml) | [PNG](diagrama-casos-de-uso.png) |

O diagrama de classes e o de casos de uso descrevem a Sprint 5, com Command,
Memento e o desfazer da última atualização. O diagrama de exceções inclui
`WorkoutUndoUnavailableError` (409). As fontes usam PlantUML 1.2026.2, UTF-8 e
o motor Smetana embutido, sem exigir Graphviz. Os nomes históricos dos arquivos
foram mantidos. O mapa completo de camadas pode ficar largo; a vista
[Command e Memento](command-memento.png) mostra os participantes da Sprint 5.
Com Java instalado e `plantuml.jar` dessa versão disponível fora do
repositório, gere novamente:

```bash
java -DPLANTUML_LIMIT_SIZE=16384 -jar /caminho/plantuml.jar -charset UTF-8 -tpng -pipe < docs/diagramas/classes-analise-usuarios.puml > docs/diagramas/diagrama-de-classes.png
java -jar /caminho/plantuml.jar -charset UTF-8 -tpng -pipe < docs/diagramas/command-memento.puml > docs/diagramas/command-memento.png
java -jar /caminho/plantuml.jar -charset UTF-8 -tpng -pipe < docs/diagramas/excecoes-validacao.puml > docs/diagramas/excecoes-validacao.png
java -jar /caminho/plantuml.jar -charset UTF-8 -tpng -pipe < docs/diagramas/casos-de-uso-usuarios.puml > docs/diagramas/diagrama-casos-de-uso.png
```

Execute na raiz do repositório e confira a imagem ao editar a fonte. A análise
conceitual em [docs/05-analise.md](../05-analise.md) é separada do diagrama das
classes reais, descrito em [docs/08-projeto.md](../08-projeto.md).
