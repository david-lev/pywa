🔀 **Migration**
----------------

- [Migration](#migration)
    - [Migration from 3.x to 4.x](#migration-from-3x-to-4x)
        - [New features](#new-features)
        - [Breaking changes](#breaking-changes)
        - [Migration steps](#migration-steps)
    - [Migration from 2.x to 3.x](#migration-from-2x-to-3x)
        - [New features](#new-features)
        - [Breaking changes](#breaking-changes)
        - [Migration steps](#migration-steps)
    - [Migration from 1.x to 2.x](#migration-from-1x-to-2x)
        - [New features](#new-features)
        - [Breaking changes](#breaking-changes)
        - [Migration steps](#migration-steps)

## Migration from 3.x to 4.x

### New features

Pywa 4.x is mostly about making the library ready for Meta's new identity model, improving webhook development, and
adding the APIs needed for groups, usernames, richer templates, and business management.

#### User identity and BSUID readiness

- Full support for
  [BSUIDs (Business-Scoped User IDs)](https://developers.facebook.com/documentation/business-messaging/whatsapp/business-scoped-user-ids),
  parent BSUIDs, usernames, and `country_code`.
- `types.User.wa_id` is now optional. Users who enable usernames may no longer expose a phone-number-based WhatsApp ID.
- `types.User.preferred_id` can resolve IDs using `WhatsApp(user_identifier_priority=...)`, so you can decide whether
  your app prefers `wa_id`, `bsuid`, or `parent_bsuid` when more than one identifier is available.
- `filters.from_users(...)` now accepts BSUIDs, parent BSUIDs, WA IDs, and formatted phone numbers.
- Phone number change updates now expose BSUID-related fields (`new_user_id`, `new_parent_id`) when Meta sends them.

#### Groups and chat-aware updates

- Full group management support: create, update, delete, fetch groups, manage invite links, handle join requests, and
  add or remove participants.
- Incoming messages now expose `msg.chat`, a `Chat` object with `id` and `type`, so handlers can distinguish private
  chats from groups.
- Added `filters.private`, `filters.group`, and `filters.from_groups(...)`.
- Added `GroupMessageStatusesHandler` and `wa.on_group_message_statuses(...)` for group delivery/read status updates.
- Sent messages now expose `sent.chat` instead of storing the recipient as a plain string field.
- Sent messages can be pinned and unpinned when the target chat supports it.

#### Webhooks, CLI, and local development

- Added the built-in server workflow:
    - `pywa dev` for development with auto-reload.
    - `pywa run` for production-style serving.
    - `WhatsApp.run()` for small scripts and quick prototypes.
- Added `utils.start_ngrok_tunnel(...)` to make local webhook testing easier.
- `webhook_fields` now accepts `utils.WebhookFields`, so you can add or remove fields from pywa's default subscription
  set.
- Webhook validation and endpoint registration were refactored to work consistently across the built-in Starlette app,
  FastAPI, Flask, and manual integrations.
- Listeners now warn when no timeout is provided and prevent usage with multiple Uvicorn workers.

#### Messages, media, callbacks, and account updates

- Added `EditedMessage`, `DeletedMessage`, `OutgoingEditedMessage`, and `OutgoingDeletedMessage` updates for
  Coexistence support.
- Added `AccountUpdate` and related enums for `account_update` webhooks.
- Media objects now store their `caption`.
- Media upload internals now support async pending uploads with `PendingMedia`.
- Added `ContactInfoRequestButton` for requesting a user's contact information.
- Added `send_carousel(...)` and `reply_carousel(...)` for interactive media carousel messages.
- Added `ContactList` for shared contact handling.

#### Business management and templates

- Added methods to retrieve shared and owned WABAs.
- Added methods to create and verify phone numbers on a WhatsApp Business Account.
- Added username management methods: `set_username`, `get_current_username`, `get_reserved_usernames`, and
  `delete_username`.
- Added WABA settings updates, including `degrees_of_freedom_spec`.
- Template components now have better validation, easier component lookup, `param_names`, stricter URL variable checks,
  and improved errors for positional/named examples.
- `Template.duplicate(...)` now supports `target_waba_id`.
- Added `CreativeFeaturesSpec.all_enabled()` and `CreativeFeaturesSpec.all_disabled()`.
- Pywa-specific deprecation warnings now use `PywaDeprecationWarning`.

### Breaking changes

#### 1. Treat `User.wa_id` as optional

`User.wa_id` may be `None` when a user enables WhatsApp usernames. Store `User.bsuid` now, and only use `wa_id` when
you specifically need a phone-number-based identifier and have checked that it exists.

`User` now includes:

- `bsuid`
- `wa_id`
- `username`
- `parent_bsuid`
- `country_code`

If you use `user.preferred_id`, review `WhatsApp(user_identifier_priority=...)` and choose the order that matches your
app. The current default remains phone-number-compatible, but your code should be ready for BSUID-first behavior as
Meta expands BSUID-based endpoints.

#### 2. Remove `ChatOpened` usage

`ChatOpened` support was removed:

- `types.ChatOpened`
- `handlers.ChatOpenedHandler`
- `wa.on_chat_opened(...)`
- `filters.chat_opened`
- `chat_opened_enabled` in `types.ConversationalAutomation`

Use message, callback, listener, or template entry points instead.

#### 3. Update direct `wa.listen(...)` calls

`wa.listen(to="...")` no longer accepts a raw phone number or WA ID. Use a listener identifier explicitly:

- `listeners.UserUpdateListenerIdentifier(...)` for user updates.
- `listeners.TemplateStatusUpdateListenerIdentifier(...)` for template status updates.

The shortcut methods such as `msg.reply(...).wait_for_reply(...)`, `sent.wait_for_click(...)`, and
`created_template.wait_until_approved(...)` remain the preferred API for most code.

#### 4. Replace `Message.system`

`Message.system` was removed. System events are separate updates now:

- `wa.on_phone_number_change(...)`
- `wa.on_identity_change(...)`

#### 5. Replace removed aliases

Deprecated aliases were removed:

- `types.ButtonUrl` -> `types.URLButton`
- `types.flows.OpenUrlAction` -> `types.flows.OpenURLAction`

#### 6. Replace in-memory media downloads

`Message.download_media(..., in_memory=True)` was removed:

- Use `msg.get_media_bytes()` when you need all bytes in memory.
- Use `msg.stream_media()` when you want to stream large files.
- Use `msg.download_media(...)` when you want to save the file to disk.

#### 7. Update sent-message recipient access

Sent updates now expose the destination as `sent.chat`.

- Use `sent.chat.id` for the destination ID.
- Use `sent.chat.type` to distinguish private and group chats.
- Use `sent.to` when you only need the destination ID compatibility shortcut.
- Stop using `sent.to_user`.

---

### Migration steps

#### Step 1: Update user identity storage

Old code often used `wa_id` as the only stable user key. In 4.x, store `bsuid` and treat `wa_id` as optional.

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)


def save_user_to_db(user: types.User):
    db.save_user(
        user_id=user.wa_id,
        name=user.name,
    )


@wa.on_message
def on_message(_: WhatsApp, msg: types.Message):
    save_user_to_db(msg.from_user)
    msg.reply(f"Hello {msg.from_user.name or 'there'}!")


########################## NEW CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)


def save_user_to_db(user: types.User):
    db.save_user(
        bsuid=user.bsuid,
        wa_id=user.wa_id,
        username=user.username,
        parent_bsuid=user.parent_bsuid,
        country_code=user.country_code,
        name=user.name,
    )


@wa.on_message
def on_message(_: WhatsApp, msg: types.Message):
    save_user_to_db(msg.from_user)
    msg.reply(f"Hello {msg.from_user.name or 'there'}!")
```

If you need to choose which identifier pywa uses for user actions, configure `user_identifier_priority`:

```python
from pywa import WhatsApp, utils

wa = WhatsApp(
    ...,
    user_identifier_priority=(
        utils.UserIdentifier.BSUID,
        utils.UserIdentifier.WA_ID,
        utils.UserIdentifier.PARENT_BSUID,
    ),
)
```

#### Step 7: Run webhooks with the new built-in server

If you previously created a FastAPI or Flask app only to host pywa webhooks, you can usually remove that framework and
run pywa directly.

```python
from pywa import WhatsApp, filters, types, utils

callback_url = utils.start_ngrok_tunnel(
    auth_token="NGROK_AUTH_TOKEN",
    domain="your-domain.ngrok-free.app",
)

wa = WhatsApp(
    phone_id="1234567890",
    token="EAA...",
    app_id="1234567890",
    app_secret="********",
    callback_url=callback_url,
    verify_token="my-verify-token",
)


@wa.on_message(filters.text)
def echo(_: WhatsApp, msg: types.Message):
    msg.reply(msg.text)
```

```bash
pywa dev
pywa run
```

#### Step 3: Update filters that identify users

`filters.from_users(...)` now accepts several identifier formats. Prefer BSUIDs where you have them, but existing
phone-number filters can often keep working.

```python
from pywa import WhatsApp, filters, types

wa = WhatsApp(...)


@wa.on_message(filters.from_users("US.13491208655302741918", "+1 (631) 555-1234"))
def trusted_user(_: WhatsApp, msg: types.Message):
    msg.reply("You are on the allowlist.")
```

#### Step 4: Replace in-memory media downloads

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)


@wa.on_message
def on_message(_: WhatsApp, msg: types.Message):
    media_bytes = msg.download_media(in_memory=True)
    store(media_bytes)


########################## NEW CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)


@wa.on_message
def on_message(_: WhatsApp, msg: types.Message):
    media_bytes = msg.get_media_bytes()
    store(media_bytes)


@wa.on_message
def upload_large_file(_: WhatsApp, msg: types.Message):
    upload_stream(msg.stream_media())
```

#### Step 5: Update sent-message recipient access

```python
########################## OLD CODE ##########################

sent = wa.send_message(to="1234567890", text="Hello")

audit_log.write(
    message_id=sent.id,
    to_user=sent.to_user,
)

########################## NEW CODE ##########################

sent = wa.send_message(to="1234567890", text="Hello")

audit_log.write(
    message_id=sent.id,
    chat_id=sent.chat.id,
    chat_type=sent.chat.type,
)

# If you only need the destination ID:
destination = sent.to
```

#### Step 6: Replace `ChatOpened` entry points

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)


@wa.on_chat_opened
def opened_chat(_: WhatsApp, update: types.ChatOpened):
    wa.send_message(to=update.from_user.wa_id, text="Welcome!")


########################## NEW CODE ##########################

from pywa import WhatsApp, filters, types

wa = WhatsApp(...)


@wa.on_message(filters.command("start"))
def start(_: WhatsApp, msg: types.Message):
    msg.reply("Welcome!")


@wa.on_callback_button(filters.matches("start"))
def start_clicked(_: WhatsApp, clb: types.CallbackButton):
    clb.reply_text("Welcome!")
```

#### Step 7: Use chat-aware group/private handling

```python
from pywa import WhatsApp, filters, types

wa = WhatsApp(...)


@wa.on_message(filters.group)
def on_group_message(_: WhatsApp, msg: types.Message):
    msg.reply(f"Public reply in group {msg.chat.id}")
    msg.reply("Private reply to the sender", private=True)


@wa.on_message(filters.private)
def on_private_message(_: WhatsApp, msg: types.Message):
    msg.reply("Hello from a private chat!")
```

## Migration from 2.x to 3.x

### New features

- [templates] Fully redesigned template system — now more flexible, reusable, and powerful.
- [calls] Full support for calls: make/receive calls, manage call state, handle events, and configure settings.
- [user_preferences] Full support for user marketing preferences (opt-in/out).
- [listeners] Listeners can now wait for non-user updates (e.g., template approval, account events).
- [system] System messages are now separate updates (`PhoneNumberChange`, `IdentityChange`).
- [client]
    - All `send_...` methods enforce keyword-only context args for clarity and consistency.
    - `upload_media` now returns a `Media` object (with media ID).
    - Added `delete_media` and `update_display_name` methods.
- [handlers] Added `on_completion` decorator for flow request callbacks.
- [types] `SuccessResult` replaces `bool`, extendable with extra attributes.
- [base_update] All user updates now include `waba_id` (WhatsApp Business Account ID).
- [message] New `referral` field (e.g., when users click ads leading to WhatsApp).
- [errors] More descriptive error messages.

### Breaking changes

- [templates] Old template system removed. Update code to the new template APIs.
- [listeners]
    - Listeners apply to **all update types**, not just user messages.
    - Legacy `to` parameter type updated.
    - If using `wa.listen` directly, update to the new listener API (shortcuts like `wait_for_reply`, `wait_for_click`
      are unchanged).
- [server] Updates now continue through the pipeline unless a listener explicitly cancels with `update.stop_handling()`.
- [client]
    - `upload_media` returns a `Media` object instead of a raw media ID string.
        - If you only pass the `upload_media` result to `send_*` methods, no changes needed.
        - If you store media IDs, update code to use `Media.id`.
    - `send_message`, `send_image`, and other `send_...` methods now require keyword-only context args (
      `reply_to_message_id`, `sender`, etc.).
        - Most users unaffected, but if you used positional args for these fields, switch to keywords.
- [types] Methods like `mark_as_read`, `indicate_typing`, etc. now return `SuccessResult` instead of `bool`.
    - Still usable in boolean checks (`if result:`).
    - If you persist results or explicitly cast to `bool`, switch to `result.success`.
- [system] `system` messages removed from `Message`. Listen to `PhoneNumberChange` and `IdentityChange` updates instead.
- [utils] `FlowRequestDecryptedMedia` replaces raw `(media_id, filename, data)` tuple. Update code to use object
  attributes.

---

### Migration steps

1. Update all template usage to the new
   system ([docs here](https://pywa.readthedocs.io/en/latest/content/templates/overview.html)).

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

# Create a WhatsApp client
wa = WhatsApp(..., business_account_id=123456)

# Create a template
created = wa.create_template(
    template=types.NewTemplate(
        name="buy_new_iphone_x",
        category=types.NewTemplate.Category.MARKETING,
        language=types.NewTemplate.Language.ENGLISH_US,
        header=types.NewTemplate.Text(text="The New iPhone {15} is here!"),
        body=types.NewTemplate.Body(text="Buy now and use the code {WA_IPHONE_15} to get {15%} off!"),
        footer=types.NewTemplate.Footer(text="Powered by PyWa"),
        buttons=[
            types.NewTemplate.UrlButton(title="Buy Now", url="https://example.com/shop/{iphone15}"),
            types.NewTemplate.PhoneNumberButton(title="Call Us", phone_number='1234567890'),
            types.NewTemplate.QuickReplyButton(text="Unsubscribe from marketing messages"),
            types.NewTemplate.QuickReplyButton(text="Unsubscribe from all messages"),
        ],
    ),
)

# Send the template message
wa.send_template(
    to="9876543210",
    template=types.Template(
        name="buy_new_iphone_x",
        language=types.Template.Language.ENGLISH_US,
        header=types.Template.TextValue(value="15"),
        body=[
            types.Template.TextValue(value="John Doe"),
            types.Template.TextValue(value="WA_IPHONE_15"),
            types.Template.TextValue(value="15%"),
        ],
        buttons=[
            types.Template.UrlButtonValue(value="iphone15"),
            types.Template.QuickReplyButtonData(data="unsubscribe_from_marketing_messages"),
            types.Template.QuickReplyButtonData(data="unsubscribe_from_all_messages"),
        ],
    ),
)

########################## NEW CODE ##########################

from pywa import WhatsApp
from pywa.types.templates import *

# Create a WhatsApp client
wa = WhatsApp(..., business_account_id=123456)

wa.create_template(
    template=Template(
        name="buy_new_iphone_x",
        category=TemplateCategory.MARKETING,
        language=TemplateLanguage.ENGLISH_US,
        parameter_format=ParamFormat.NAMED,
        components=[
            ht := HeaderText("The New iPhone {{iphone_num}} is here!", iphone_num=15),
            bt := BodyText("Buy now and use the code {{code}} to get {{per}}% off!", code="WA_IPHONE_15", per=15),
            FooterText(text="Powered by PyWa"),
            Buttons(
                buttons=[
                    url := URLButton(text="Buy Now", url="https://example.com/shop/{{1}}", example="iphone15"),
                    PhoneNumberButton(text="Call Us", phone_number="1234567890"),
                    qrb1 := QuickReplyButton(text="Unsubscribe from marketing messages"),
                    qrb2 := QuickReplyButton(text="Unsubscribe from all messages"),
                ]
            ),

        ]
    ),
)

# Send the template message
wa.send_template(
    to="9876543210",
    name="buy_new_iphone_x",
    language=TemplateLanguage.ENGLISH_US,
    params=[
        ht.params(iphone_num=30),
        bt.params(code="WA_IPHONE_30", per=30),
        url.params(url_variable="iphone30", index=0),
        qrb1.params(callback_data="unsubscribe_from_marketing_messages", index=1),
        qrb2.params(callback_data="unsubscribe_from_all_messages", index=2),
    ]
)
```

2. If you are using the `upload_media` method, you need to update your code to use the `Media` object instead of a
   string (media ID):

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

media_id = wa.upload_media(file="path/to/file.jpg")

# running sql query to store media_id
cursor.execute(
    "CREATE TABLE IF NOT EXISTS media (id INTEGER PRIMARY KEY AUTOINCREMENT, media_id VARCHAR UNIQUE NOT NULL)")
cursor.execute("INSERT INTO media (media_id) VALUES (?)", (media_id,))

########################## NEW CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

media = wa.upload_media(file="path/to/file.jpg")

# running sql query to store media.id
cursor.execute(
    "CREATE TABLE IF NOT EXISTS media (id INTEGER PRIMARY KEY AUTOINCREMENT, media_id VARCHAR UNIQUE NOT NULL)")
cursor.execute("INSERT INTO media (media_id) VALUES (?)", (media.id,))
```

3. If you are using the `system` messages, you need to update your code to start listening to the `PhoneNumberChange`
   and `IdentityChange` updates instead:

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types, filters

wa = WhatsApp(...)


@wa.on_message(filters=filters.new(lambda _, m: m.system and m.system.type == "customer_changed_number"))
def on_phone_number_change(_: WhatsApp, msg: types.Message):
    repository.update_phone_number(old=msg.system.wa_id, new=msg.system.new_wa_id)


@wa.on_message(filters=filters.new(lambda _, m: m.system and m.system.type == "customer_changed_identity"))
def on_identity_change(_: WhatsApp, msg: types.Message):
    repository.log_out_user(wa_id=msg.sender)  # secure the user account


########################## NEW CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)


@wa.on_phone_number_change
def on_phone_number_change(_: WhatsApp, update: types.PhoneNumberChange):
    repository.update_phone_number(old=update.old_wa_id, new=update.new_wa_id)


@wa.on_identity_change
def on_identity_change(_: WhatsApp, update: types.IdentityChange):
    repository.log_out_user(wa_id=update.sender)  # secure the user
```

## Migration from 1.x to 2.x

### New features

- Listeners: Listeners are a new way to handle incoming user updates (messages, callbacks, etc.). They are more
  flexible, faster, and easier to use than handlers.
- Filters: Filters are now objects that can be combined using logical operators. They are more powerful and flexible
  than the previous filter system.
- Handlers: Now you can register handlers with decorators without the need to use the `add_handler` method.
- FlowCompletion: A new method `.get_media(types.Image, key="img")` allows you to construct a media object and perform
  actions like `.download()` on it.
- FlowRequest: Decrypt media directly from FlowRequest using `.decrypt_media(key, index)`.
- Client: The client can run without a token but won’t allow API operations (only webhook listening).
- SentMessage: The `SentMessage` object returned by `send_message`, `send_image`, etc., contains the message ID and
  allows to act on the sent message with methods like `reply_x`, `wait_for_x` etc.
- Flows: Create conditionals for `If` by using python's operators like `==`, `!=`, `>`, `<`, `>=`, `<=` etc.

### Breaking changes

- Async Separation: In the sync version of pywa, no async callbacks or filters are allowed.
- Returning `SentMessage` Object: Functions like `send_message`, `send_image`, etc., no longer return a string (message
  ID). Instead, they return a `SentMessage` object, which contains the ID and allows further actions.
- Filter System Redesign: Filters are now objects rather than simple callables. You can combine filters using logical
  operators like `&`, `|`, and `~`.
- Reordered Init Parameters: The order of the parameters in the `WhatsApp` class has been changed and some parameters
  have been removed.
- Handler Factory Changes: Factories in handlers are now limited to `CallbackData` subclasses (not any callable). Only
  one class is allowed, not multiple.
- Removal of Deprecated Arguments: Deprecated arguments like `keyboard` (use `buttons` instead) and `body` (use
  `caption`) have been removed from `send_message`, `send_image`, `send_video`, and `send_document`.
- Server: The function signature `webhook_update_handler` that used to pass updates manually to the server has been
  changed.
- Deprecated Argument Removal: Deprecated arguments such as `keyboard` and `body` have been removed.
- Client: The `continue_handling` param is now set to `False` by default. so if update is handled, it will not be passed
  to the next handler unless you set it to `True` or call `update.continue_handling()` in the handler.
- Flows: The `.data_key` and `.from_ref` of the flowjson components renamed to `.ref`.

### Migration steps

1. If you are using the sync version of pywa, and you have async callbacks or filters, you need to remove them or switch
   to the async version:

```python
# Old code
from pywa import WhatsApp, types

wa = WhatsApp(...)


@wa.on_message
async def on_message(_: WhatsApp, msg: types.Message):
    msg.reply("Hello, World!")


# New code
from pywa_async import WhatsApp, types

wa = WhatsApp(...)


@wa.on_message
async def on_message(_: WhatsApp, msg: types.Message):
    await msg.reply("Hello, World!")
```

2. If you use the message ID returned by functions like `send_message`, `send_image`, etc (e.g to store it in a
   database), you need to update your code to use the `.id` attribute of the `SentMessage` object:

```python
# Old code
message_id = wa.send_message("Hello, World!")
db.store_message_id(message_id)

# New code
sent_message = wa.send_message("Hello, World!")
db.store_message_id(sent_message.id)
```

3. If you are using filters, you need to update your code to use the new filter system:

```python
# Old code
from pywa import WhatsApp, filters, types

wa = WhatsApp(...)


@wa.on_message(filters.text, lambda _, m: m.text.isdigit())
def on_message(_: WhatsApp, msg: types.Message):
    msg.reply("Hello, World!")


@wa.on_message(filters.any_(filters.text.is_command, filters.text.command("start")))
def on_command(_, __): ...


# New code
from pywa import WhatsApp, filters, types

wa = WhatsApp(...)


@wa.on_message(filters.text & filters.new(lambda _, m: m.text.isdigit()))
def on_message(_: WhatsApp, msg: types.Message):
    msg.reply("Hello, World!")


@wa.on_message(filters.is_command | filters.command("start"))
def on_command(_, __): ...
```

4. If you are using lots of handlers, you may want to switch to listeners:

```python
# Old code
from pywa import WhatsApp, types, filters


@wa.on_message(filters.command("start"))
def on_start(_: WhatsApp, m: types.Message):
    m.reply("How old are you?")


@wa.on_message(filters.text & filters.new(lambda _, m: m.text.isdigit()))
def on_age(_: WhatsApp, m: types.Message):
    m.reply(f"You are {m.text} years old")
    m.reply("What is your name?")


@wa.on_message(filters.text & filters.new(lambda _, m: m.text.isalpha()))
def on_name(_: WhatsApp, m: types.Message):
    m.reply(f"Hello {m.text}")


# New code
from pywa import WhatsApp, types, filters

wa = WhatsApp(...)


@wa.on_message(filters.command("start"))
def on_start(_: WhatsApp, m: types.Message):
    age = m.reply("How old are you?").wait_for_reply(
        filters=filters.text & filters.new(lambda _, m: m.text.isdigit()),
    )
    m.reply(f"You are {age.text} years old")
    name = m.reply("What is your name?").wait_for_reply(
        filters=filters.text & filters.new(lambda _, m: m.text.isalpha()),
    )
    m.reply(f"Hello {name.text}")

```

5. If You are writing the handlers in separate modules and then using `add_handler` to register the callback wrapped
   with handler objects, you can now use decorators to register handlers:

```python
# Old code

# module1.py

from pywa import WhatsApp, types


def on_start(_: WhatsApp, m: types.Message):
    m.reply("How old are you?")


def on_age(_: WhatsApp, m: types.Message):
    m.reply(f"You are {m.text} years old")
    m.reply("What is your name?")


# module2.py

from pywa import WhatsApp, handlers, filters

wa = WhatsApp(...)

wa.add_handlers(handlers.MessageHandler(on_start, filters.command("start")))
wa.add_handlers(handlers.MessageHandler(on_age, filters.text & filters.new(lambda _, m: m.text.isdigit())))

# New code

# module1.py

from pywa import WhatsApp, types, filters


@WhatsApp.on_message(filters.command("start"))  # we using the class here, not the instance!
def on_start(_: WhatsApp, m: types.Message):
    m.reply("How old are you?")


@WhatsApp.on_message(filters.text & filters.new(lambda _, m: m.text.isdigit()))
def on_age(_: WhatsApp, m: types.Message):
    m.reply(f"You are {m.text} years old")
    m.reply("What is your name?")


# module2.py

from pywa import WhatsApp
from . import module1

wa = WhatsApp(..., handlers_modules=[module1])
```

6. If you want to keep the continuation of the update to the next handler, you need to set the `continue_handling`
   attribute of the update object to `True`:

```python

from pywa import WhatsApp

wa = WhatsApp(..., continue_handling=True)
```

7. If you are using the `webhook_update_handler` function to pass updates manually to the server, you need to update the
   function signature:

```python

# Old code
from pywa import WhatsApp, utils

wa = WhatsApp(..., server=None)


def some_web_framework_handler(req):
    res, status = wa.webhook_update_handler(
        update=req.json(),
        raw_body=req.read(),
        hmac_header=req.headers.get(utils.HUB_SIG)
    )
    return res, status


# New code

from pywa import WhatsApp, utils

wa = WhatsApp(..., server=None)


def some_web_framework_handler(req):
    res, status = wa.webhook_update_handler(
        update=req.read(),
        hmac_header=req.headers.get(utils.HUB_SIG),
    )
    return res, status
```

8. If you are using the `.data_key` and `.from_ref` of the flowjson components, you need to update your code to use the
   `.ref` attribute:

```python

# Old code

from pywa.types.flows import *

FlowJSON(
    screens=[
        Screen(
            data=[
                name := ScreenData(key="name", example="David")
            ],
            layout=Layout(
                children=[
                    date := DatePicker(
                        on_select_action=Action(
                            payload={"date": FormRef("date"), "name": DataKey("name")},
                        ),
                    ),
                    Footer(
                        ...,
                        on_click_action=Action(
                            payload={
                                "date": date.form_ref,
                                "name": name.data_key
                            },
                        ),
                    ),
                ],
            ),
        )
    ],
)

# New code

FlowJSON(
    screens=[
        Screen(
            data=[
                name := ScreenData(key="name", example="David")
            ],
            layout=Layout(
                children=[
                    date := DatePicker(
                        on_select_action=Action(
                            payload={"date": ComponentRef("date"), "name": ScreenDataRef("name")},
                        ),
                    ),
                    Footer(
                        ...,
                        on_click_action=Action(
                            payload={
                                "date": date.ref,
                                "name": name.ref
                            },
                        ),
                    ),
                ],
            ),
        )
    ],
)

```
