# Diagramas da Sprint 3

| Fonte editável | Imagem correspondente |
| --- | --- |
| [Classes de projeto](classes-analise-usuarios.puml) | [PNG](diagrama-de-classes.png) |
| [Validação e exceções](excecoes-validacao.puml) | [PNG](excecoes-validacao.png) |
| [Casos de uso](casos-de-uso-usuarios.puml) | [PNG](diagrama-casos-de-uso.png) |

As fontes usam PlantUML 1.2026.2, UTF-8 e o motor Smetana embutido, sem exigir
Graphviz. Os nomes históricos dos arquivos foram mantidos. Com Java instalado
e `plantuml.jar` dessa versão disponível fora do repositório, gere novamente:

```bash
java -jar /caminho/plantuml.jar -charset UTF-8 -tpng -pipe < docs/diagramas/classes-analise-usuarios.puml > docs/diagramas/diagrama-de-classes.png
java -jar /caminho/plantuml.jar -charset UTF-8 -tpng -pipe < docs/diagramas/excecoes-validacao.puml > docs/diagramas/excecoes-validacao.png
java -jar /caminho/plantuml.jar -charset UTF-8 -tpng -pipe < docs/diagramas/casos-de-uso-usuarios.puml > docs/diagramas/diagrama-casos-de-uso.png
```

Execute na raiz do repositório e confira a imagem ao editar a fonte. A análise
conceitual em [docs/05-analise.md](../05-analise.md) é separada do diagrama das
classes reais, descrito em [docs/08-projeto.md](../08-projeto.md).
