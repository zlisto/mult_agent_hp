"""Helpers to pull text chunks from harrypotter.db.

Build:
- list_books(), get_book_meta(book_number)
- retrieve_chunks(book_number, question) — keyword-scored chunks; cap evidence size
- format_evidence(chunks) — join chunks for the specialist prompt

Never load an entire novel into a model prompt.
"""
