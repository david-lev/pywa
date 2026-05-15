# 02 — Menu with buttons and section lists

Three things:
1. **Quick-reply buttons** with `types.Button` (max 3).
2. **Section list** with `types.SectionList` (max 10 rows total).
3. **Typed callback data** via a `@dataclass` subclass of `types.CallbackData` — your handler gets back a real Python object, not a string.

## Run

```bash
cp ../.env.example .env
fastapi dev main.py
```

Send `menu` to the bot. Tap a button → handler fires with a typed `Action` payload.

## Notes

- The `factory=Action` parameter at [`main.py:62`](main.py#L62) is what makes `btn.data.name` typed.
- Quick-reply buttons and section-list rows trigger **different** events: `on_callback_button` vs `on_callback_selection`.
- WhatsApp limits: button title ≤ 20 chars, section row title ≤ 24 chars, description ≤ 72 chars, 10 rows total across all sections.
