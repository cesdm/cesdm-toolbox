#!/usr/bin/env python3
"""A bookshelf: EAR with a schema that does not extend CESDM.

    python docs/examples/bookshelf/run.py

Two classes, one link, and the flat YAML pair. The schema is this
folder's schema/. An ear model loads it; a CesdmModel is not involved.
"""

from __future__ import annotations

from pathlib import Path

from ear import build_model_from_yaml, get_attr_value

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "schema"
OUT = Path.cwd() / "output" / "bookshelf" / "bookshelf.yaml"


def new_model():
    return build_model_from_yaml(str(SCHEMA))


def build():
    model = new_model()

    model.add_entity("Author", "author.calvino")
    model.add_attribute("author.calvino", "name", "Italo Calvino")
    model.add_entity("Author", "author.borges")
    model.add_attribute("author.borges", "name", "Jorge Luis Borges")

    model.add_entity("Book", "book.invisible_cities")
    model.add_attribute("book.invisible_cities", "title", "Invisible Cities")
    model.add_attribute("book.invisible_cities", "year", 1972)
    model.add_relation("book.invisible_cities", "writtenBy", "author.calvino")

    model.add_entity("Book", "book.ficciones")
    model.add_attribute("book.ficciones", "title", "Ficciones")
    model.add_attribute("book.ficciones", "year", 1944)
    model.add_relation("book.ficciones", "writtenBy", "author.borges")
    return model


def main() -> None:
    model = build()
    errors = model.validate()
    print(f"validate(): {errors or 'ok'}")

    bare = new_model()
    bare.add_entity("Book", "book.untitled")
    bare.add_attribute("book.untitled", "title", "Untitled")
    bare.add_attribute("book.untitled", "year", 2020)
    missing = bare.validate()
    print(f"book with no author: {missing[0]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    model.export_yaml(OUT)
    print(f"wrote {OUT.relative_to(Path.cwd())}")

    again = new_model()
    again.import_yaml(OUT)
    book = again.get_entities("Book")["book.invisible_cities"]
    author = again.get_entities("Author")[book.get_relation("writtenBy")]
    print(
        f"{get_attr_value(book, 'title')} ({get_attr_value(book, 'year')})"
        f" — {get_attr_value(author, 'name')}"
    )


if __name__ == "__main__":
    main()
