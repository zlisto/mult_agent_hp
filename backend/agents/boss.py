"""Boss agent — owns the chat and delegates to book specialists.

Build:
- PydanticAI Agent with async tool ask_book_specialist(book_number, question)
- BossDeps with asyncio.Queue + emit() for live SSE events
- run_boss_chat_stream(message) and run_boss_chat(message)
- Event types: boss_thinking, specialist_started, specialist_done, final, error

main.py imports run_boss_chat and run_boss_chat_stream from here.
"""
