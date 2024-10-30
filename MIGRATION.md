🔀 **Migration**
----------------

- [Migration](#migration)
  - [Migration from 1.x to 2.x](#migration-from-1x-to-2x)
    - [New features](#new-features)
    - [Breaking changes](#breaking-changes)
    - [Migration steps](#migration-steps)

## Migration from 1.x to 2.x


### New features
- Listeners: Listeners are a new way to handle incoming user updates (messages, callbacks, etc.). They are more flexible, faster, and easier to use than handlers.
- Filters: Filters are now objects that can be combined using logical operators. They are more powerful and flexible than the previous filter system.
- Handlers: Now you can register handlers with decorators without the need to use the `add_handler` method.
- FlowCompletion: A new method `.get_media(types.Image, key="img")` allows you to construct a media object and perform actions like `.download()` on it.
- FlowRequest: Decrypt media directly from FlowRequest using `.decrypt_media(key, index)`.
- Client: The client can run without a token but won’t allow API operations (only webhook listening).
- SentMessage: The `SentMessage` object returned by `send_message`, `send_image`, etc., contains the message ID and allows to act on the sent message with methods like `reply_x`, `wait_for_x` etc.
- Flows: Create conditionals for `If` by using python's operators like `==`, `!=`, `>`, `<`, `>=`, `<=` etc.

### Breaking changes

- Async Separation: In the sync version of pywa, no async callbacks or filters are allowed.
- Returning `SentMessage` Object: Functions like `send_message`, `send_image`, etc., no longer return a string (message ID). Instead, they return a `SentMessage` object, which contains the ID and allows further actions.
- Filter System Redesign: Filters are now objects rather than simple callables. You can combine filters using logical operators like `&`, `|`, and `~`.
- Reordered Init Parameters: The order of the parameters in the `WhatsApp` class has been changed and some parameters have been removed.
- Handler Factory Changes: Factories in handlers are now limited to `CallbackData` subclasses (not any callable). Only one class is allowed, not multiple.
- Removal of Deprecated Arguments: Deprecated arguments like `keyboard` (use `buttons` instead) and `body` (use `caption`) have been removed from `send_message`, `send_image`, `send_video`, and `send_document`.
- Server: The function signature `webhook_update_handler` that used to pass updates manually to the server has been changed.
- Deprecated Argument Removal: Deprecated arguments such as `keyboard` and `body` have been removed.
- Client: The `continue_handling` param is now set to `False` by default. so if update is handled, it will not be passed to the next handler unless you set it to `True` or call `update.continue_handling()` in the handler.
- Flows: The `.data_key` and `.from_ref` of the flowjson components renamed to `.ref`.

### Migration steps

1. If you are using the sync version of pywa, and you have async callbacks or filters, you need to remove them or switch to the async version:

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

2. If you use the message ID returned by functions like `send_message`, `send_image`, etc (e.g to store it in a database), you need to update your code to use the `.id` attribute of the `SentMessage` object:

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

5. If You are writing the handlers in separate modules and then using `add_handler` to register the callback wrapped with handler objects, you can now use decorators to register handlers:

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

6. If you want to keep the continuation of the update to the next handler, you need to set the `continue_handling` attribute of the update object to `True`:

```python

from pywa import WhatsApp
wa = WhatsApp(..., continue_handling=True)
```

7. If you are using the `webhook_update_handler` function to pass updates manually to the server, you need to update the function signature:

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

8. If you are using the `.data_key` and `.from_ref` of the flowjson components, you need to update your code to use the `.ref` attribute:

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
