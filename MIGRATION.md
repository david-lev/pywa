🔀 **Migration**
----------------

- [Migration](#migration)
  - [Migration from 2.x to 3.x](#migration-from-2x-to-3x)
    - [New features](#new-features)
    - [Breaking changes](#breaking-changes)
    - [Migration steps](#migration-steps)
  - [Migration from 1.x to 2.x](#migration-from-1x-to-2x)
    - [New features](#new-features)
    - [Breaking changes](#breaking-changes)
    - [Migration steps](#migration-steps)

## Migration from 2.x to 3.x


### New features

- [templates] Refactored and improved templates support. The templates are now flexible, reusable, extensible, easier to use and more powerful.
- [calls] Added full support for calls. You can now make and receive calls, manage calls, handle call events, configure call settings, and more.
- [user_preferences] Added full support for user preferences. You can now listen to user marketing preferences - if the user has opted in or out of marketing messages, and act accordingly.
- [server] Continued handling if listener is not using the update. If a listener does not use the update (not filtered or not cancelled), the server will continue to handle the update and pass it to the handlers.
- [system] Moved `system` messages to `PhoneNumberChange` and `IdentityChange` updates. The `system` messages are now handled as separate updates, allowing you to focus on real user messages and events.
- [client] Forced keyword-only for context args in `send_message`, `send_image`, and other `send_...` methods. This change improves readability and consistency of the API.
- [types] Returned `SuccessResult` instead of `bool` to allow future extension with other attributes. The `SuccessResult` object acts as boolean, but can also contain additional information about the success of the operation.
- [client] `upload_media` returns `Media` object. The `Media` object contains the media ID so you can use it later to send the media or perform other operations.
- [client] Added `update_display_name` method to update the WhatsApp display name. This method allows you to change the display name of your WhatsApp account.
- [handlers] Added `on_completion` decorator to flow request callback wrapper. This decorator allows you to register a callback that will be called when the flow request is completed.
- [errors] Show more descriptive error messages. The error messages now provide more context and information about the error, making it easier to debug and fix issues.
- [base_update] Added `waba_id` for all user updates. The `waba_id` is the WhatsApp Business Account ID that received the update, allowing you to identify the account that the update belongs to.
- [message] Added `referral` field. When a customer clicks an ad that redirects to WhatsApp and starts a chat, the `referral` field contains information about the ad that was clicked.
- [client] Added `delete_media` method. This method allows you to delete media files from WhatsApp servers.


### Breaking changes

- [templates] The templates system has been completely redesigned. The old templates are no longer supported, and you need to update your code to use the new templates system (create and send)
- [listeners] Listeners can now be used to handle any update, not just user updates. This means that you can now use listeners to wait for template to be approved and to other account related upadtes. If you are using `wa.listen` directly (and not using one of the shortcuts like `wait_for_reply`, `wait_for_click` etc.), you will need to update your code to use the new listeners system.
- [server] The server now continues to handle updates even if the listener does not use the update. This means that if a listener does not filter or cancel the update, the server will pass it to the handlers (unless you call `update.stop_handling()` inside the listener filters/cancelers).
- [client] The `upload_media` method now returns a `Media` object instead of a string (media ID). The `Media` object contains the media ID and allows you to perform actions on the media, such as downloading or deleting it. If you using the media ID directly to send media - you don't need to change anything, just use the `Media` object instead of the string. if you stored the media ID in a database or somewhere else, you will need to update your code to use the `Media.id` attribute instead of the string media ID.
- [client] The `send_message`, `send_image`, and other `send_...` methods now require keyword-only arguments for context. This change improves readability and consistency of the API. This context arguments are `reply_to_message_id`, `sender` etc. Most of users don't need to change anything, but if you are using positional arguments for these context args (they are located at the end of the method signature, so the chance for breaking is low), you will need to update your code to use keyword arguments.
- [types] The `SuccessResult` object is now returned instead of a boolean value. This change allows for future extension of the `SuccessResult` object with additional attributes, such as error messages or additional information about the success of the operation. If you are using the return value of methods like `mark_as_read`, `indicate_typing`, etc., if you just checking if the operation was successful, you can continue to use it as a boolean. but if you storing the result in a database or forcing the result to be a boolean, you will need to update your code to use the `SuccessResult.success` attribute instead of the boolean value.
- [system] The `system` messages are now handled as separate updates, and the `PhoneNumberChange` and `IdentityChange` updates are used instead. This change allows you to focus on real user messages and events, and handle system messages separately. If you were accessing the `system` attribute of the `Message` object, you will need to update your code to start listening to the `PhoneNumberChange` and `IdentityChange` updates instead.
- [utils] The `FlowRequestDecryptedMedia` object is now returned instead of a tuple `(media_id, filename, data)`. This change allows you to access the media ID, filename, and data in a more structured way. If you were using the tuple to access the media ID, filename, and data, you will need to update your code to use the `FlowRequestDecryptedMedia` object instead.

### Migration steps

1. If you are using the templates system, you need to update your code to use the new templates system. You can find the documentation for the new templates system [here](https://pywa.readthedocs.io/en/latest/content/templates/overview.html).

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

2. If you are using the listeners system, you need to update your code to use the new listeners system. You can find the documentation for the new listeners system [here](https://pywa.readthedocs.io/en/latest/content/listeners/overview.html).

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types, filters

wa = WhatsApp(...)

@wa.on_message(filters.text)
def on_first_message(_: WhatsApp, msg: types.Message):
    age = msg.reply(f"Hi {msg.from_user.name}! What's your age?").wait_for_reply(
        # In the old code, if the update is not filtered, it will NOT be passed to the handlers (another_text_handler)
        filters=filters.text & filters.new(lambda _, m: m.text.isdigit())
    )
    msg.reply(f"You are {age.text} years old!")


@wa.on_message(filters.text)
def another_text_handler(_: WhatsApp, msg: types.Message):
    update = wa.listen(to="123456789", ...) # listen for updates from the user
    ...

########################## NEW CODE ##########################

from pywa import WhatsApp, types, filters, listeners

wa = WhatsApp(...)

def filter_age(_: WhatsApp, msg: types.Message) -> bool:
    if msg.text.isdigit():
      return True # the update is filtered
    msg.reply("Please enter a valid age (number).")
    msg.stop_handling() # stop handling this update (will not be passed to the handlers)


@wa.on_message(filters.text)
def on_first_message(_: WhatsApp, msg: types.Message):
    age = msg.reply(f"Hi {msg.from_user.name}! What's your age?").wait_for_reply(
        # In the new code, if the update is not filtered, it will be passed to the handlers (another_text_handler), so we need to stop handling it if the age is not valid
        filters=filters.text & filters.new(filter_age)
    )
    msg.reply(f"You are {age.text} years old!")

@wa.on_message(filters.text)
def another_text_handler(_: WhatsApp, msg: types.Message):
    update = wa.listen(to=listeners.UserUpdateListenerIdentifier(sender="123456789", recipient="your_phone_id"), ...)  # listen for updates from the user
    ...
```

3. If you are using the `upload_media` method, you need to update your code to use the `Media` object instead of a string (media ID):

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

media_id = wa.upload_media(file="path/to/file.jpg")

# running sql query to store media_id
cursor.execute("CREATE TABLE IF NOT EXISTS media (id INTEGER PRIMARY KEY AUTOINCREMENT, media_id VARCHAR UNIQUE NOT NULL)")
cursor.execute("INSERT INTO media (media_id) VALUES (?)", (media_id,))


########################## NEW CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

media = wa.upload_media(file="path/to/file.jpg")

# running sql query to store media.id
cursor.execute("CREATE TABLE IF NOT EXISTS media (id INTEGER PRIMARY KEY AUTOINCREMENT, media_id VARCHAR UNIQUE NOT NULL)")
cursor.execute("INSERT INTO media (media_id) VALUES (?)", (media.id,))
```

4. If you are using the `send_message`, `send_image`, or other `send_...` methods, you need to update your code to use keyword-only arguments for context:

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

wa.send_message(
    "97234567890",
    "Hello, World!",
    "header text",
    "footer text",
    [types.Button(title="x", callback_data="y")],
    True, # preview_url
    "message_id", # reply_to_message_id
    "phone_id", # sender
)

########################## NEW CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

wa.send_message(
    "97234567890",
    "Hello, World!",
    "header text",
    "footer text",
    [types.Button(title="x", callback_data="y")],
    preview_url=True,  # kw only argument
    reply_to_message_id="message_id",  # kw only argument
    sender="phone_id",  # kw only argument
)
```

5. If you are using the `SuccessResult` object, you need to update your code to use the `SuccessResult.success` attribute instead of a boolean value:

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

result = wa.mark_as_read("97234567890", "message_id")

# running sql query to store result
cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, message_id VARCHAR UNIQUE NOT NULL, is_read BOOLEAN NOT NULL)")
cursor.execute("INSERT INTO messages (message_id, is_read) VALUES (?, ?)", ("msg_id", result))

########################## NEW CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

result = wa.mark_as_read("97234567890", "message_id")

# running sql query to store result.success
cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, message_id VARCHAR UNIQUE NOT NULL, is_read BOOLEAN NOT NULL)")
cursor.execute("INSERT INTO messages (message_id, is_read) VALUES (?, ?)", ("msg_id", result.success))
```

6. If you are using the `system` messages, you need to update your code to start listening to the `PhoneNumberChange` and `IdentityChange` updates instead:

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types, filters

wa = WhatsApp(...)

@wa.on_message(filters=filters.new(lambda _, m: m.system and m.system.type == "customer_changed_number"))
def on_phone_number_change(_: WhatsApp, msg: types.Message):
    repository.update_phone_number(old=msg.system.wa_id, new=msg.system.new_wa_id)

@wa.on_message(filters=filters.new(lambda _, m: m.system and m.system.type == "customer_changed_identity"))
def on_identity_change(_: WhatsApp, msg: types.Message):
    repository.log_out_user(wa_id=msg.sender) # secure the user account


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

7. If you are using the `FlowRequestDecryptedMedia` object, you need to update your code to use the `FlowRequestDecryptedMedia` object instead of a tuple:

```python
########################## OLD CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

@wa.on_flow_request("/my-flow-endpoint")
def my_flow_endpoint(_: WhatsApp, req: types.FlowRequest):
    media_id, filename, decrypted_data = req.decrypt_media(key="driver_license", index=0)
    with open(filename, "wb") as file:
        file.write(decrypted_data)
    return req.respond(...)

########################## NEW CODE ##########################

from pywa import WhatsApp, types

wa = WhatsApp(...)

@wa.on_flow_request("/my-flow-endpoint")
def my_flow_endpoint(_: WhatsApp, req: types.FlowRequest):
    decrypted_media = req.decrypt_media(key="driver_license", index=0)
    with open(decrypted_media.filename, "wb") as file:
        file.write(decrypted_media.data)
    return req.respond(...)
```


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
