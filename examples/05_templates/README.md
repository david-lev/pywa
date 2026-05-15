# 05 — Templates: create + send

No webhook needed. Two-step script:

```bash
cp ../.env.example .env  # set WA_BUSINESS_ACCOUNT_ID and WA_TEST_RECIPIENT too
python main.py create    # submit the template — Meta will review it
# ...wait for status: APPROVED (you can poll with wa.get_template_by_name(...) or check the dashboard)
python main.py send      # sends to WA_TEST_RECIPIENT
```

## Notes

- The same component objects (`HeaderText`, `BodyText`, `URLButton`, …) are used **both** at create-time (to declare the template) **and** at send-time (to fill in values). At send-time you call `.params(...)` on each to supply the live values for that send.
- `ParamFormat.NAMED` lets you write `{{iphone_num}}` instead of `{{1}}`. Highly recommended — positional params are easy to mis-order.
- Marketing templates are gated by Meta's review. For OTPs use `TemplateCategory.AUTHENTICATION` — different rules, different latency.
- Quick-reply button taps from templates arrive as `on_callback_button` events with the `callback_data` you set in `.params(...)`.

## Common pitfalls

- **`(#100) Param mismatch`** → the parameters you pass at send-time don't match the ones declared at create-time. Re-check names and order.
- **Template stuck in PENDING** → Meta's review queue. Usually <1h, can be longer.
- **`(#132001) Template does not exist`** → you're sending to a number on a different WhatsApp Business Account than the one that owns the template.
