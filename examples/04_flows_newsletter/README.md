# 04 — Flow: newsletter signup

A single-screen WhatsApp Flow asking for name + email, sent via a `FlowButton`. The submitted data arrives in `on_flow_completion`.

## Encryption setup (one-time)

Flows require an RSA key pair. The **public** key goes to Meta; the **private** key stays on your server and decrypts incoming Flow requests.

```bash
# Generate the keys (encrypted private key with a password)
openssl genrsa -aes256 -passout pass:CHANGE_ME -out private.pem 2048
openssl rsa -in private.pem -outform PEM -pubout -out public.pem

# Print the public key — paste into the Meta WhatsApp Manager
cat public.pem
```

Then in **Meta WhatsApp Manager → Account Tools → Phone numbers → ⋯ → Manage flows → Sign public key**, paste `public.pem` and submit. Meta will accept after a short delay.

Set in `.env`:

```dotenv
WA_FLOW_PRIVATE_KEY_PATH=./private.pem
WA_FLOW_PRIVATE_KEY_PASSWORD=CHANGE_ME
```

## Run

```bash
cp ../.env.example .env
pip install -r ../requirements.txt  # includes pywa[cryptography]
fastapi dev main.py
```

Send `subscribe` to the bot → tap the button → fill the form → submit. The handler runs and replies with a confirmation.

## Notes

- [`main.py:88`](main.py#L88) creates the flow **once** at startup. In real apps you typically keep the `FlowJSON` in a separate file or load it from a string and version it in git.
- The flow's screen is `terminal=True` so submission closes the chat overlay. For multi-screen flows with server-side branching, register an `on_flow_request` handler — see [the flows docs](https://pywa.readthedocs.io/en/latest/content/flows/overview.html).
- `flow.response` is a `dict` with the field names you defined (`name`, `email`).
- The `Ref` objects (`name.ref`, `email.ref`) are how flows reference the value of one component from another — they expand to `${form.name}` at runtime.
