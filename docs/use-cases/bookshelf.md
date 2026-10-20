# Bookshelf: an EAR example

This case shows that the engine under CESDM knows nothing about energy. `add_entity`, `add_attribute` and `add_relation` do not mention a generator: the classes come from the schema that is loaded. CESDM loads `cesdm/schemas/base`. A schema that does not extend it describes another domain, and the same engine checks it. Read this page if you want to see what the engine does on its own, before any energy classes, or if you consider using it for data outside energy.

The bookshelf is the smallest such schema. `Author` has a `name`. `Book` has a `title`, a `year`, and a required `writtenBy` link to an `Author`. The schema is `docs/examples/bookshelf/schema/`. It does not extend `cesdm/schemas/base`, and the script loads it with `ear`, not with `cesdm_toolbox`.

```bash
python docs/examples/bookshelf/run.py
```

```python
from ear import build_model_from_yaml

model = build_model_from_yaml("docs/examples/bookshelf/schema")

model.add_entity("Author", "author.calvino")
model.add_attribute("author.calvino", "name", "Italo Calvino")

model.add_entity("Book", "book.invisible_cities")
model.add_attribute("book.invisible_cities", "title", "Invisible Cities")
model.add_attribute("book.invisible_cities", "year", 1972)
model.add_relation("book.invisible_cities", "writtenBy", "author.calvino")

model.validate()                          # [] — the book has an author
model.export_yaml("bookshelf.yaml")       # flat file; import_yaml reads it back
```

A second book is another instance, not a new class. `validate()` reports a book with no author, because the schema says `writtenBy` is required. The book is written; the check finds the gap afterwards. The script prints:

```text
validate(): ok
book with no author: [Book:book.untitled] Missing required relation 'writtenBy'
wrote output/bookshelf/bookshelf.yaml
Invisible Cities (1972) — Italo Calvino
```

Everything CESDM adds — the energy classes, the shared libraries, the analysis profiles shipped with the toolbox — sits on top of these same calls. How the two layers fit together is [The EAR engine and CESDM](../concepts/engine.md).
