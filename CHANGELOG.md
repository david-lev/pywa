📝 **Changelog**
---------------

> NOTE: pywa follows the [semver](https://semver.org/) versioning standard.


### 2.3.0 (2024-11-30) **Latest**

- [client] allowing to specify the callback url scope
- [client] expose methods to override callback url in waba and phone scopes
- [flows] typing `DataSource` to accept `Ref`s

### 2.2.0 (2024-11-29)

- [flows] adding `ScreenDataUpdate` to use in `UpdateDataAction`
- [flows] using math operators between math objs
- [flows] renaming `ActionNext` to `Next` and `ActionNextType` to `NextType`

### 2.1.0 (2024-11-24)

- [flows] adding `CalendarPicker` component
- [flows] allow string concatenation with refs
- [flows] adding support for math expressions
- [flows] allowing to use condition in `visible`
- [flows] new action: open url
- [flows] new action: update data
- [flows] `init_value` available outside form
- [flows] allow to use `screen/ref` as shortcut for `.ref_in(screen)`
- [flows] separating `Action` and adding `on_unselect_action`


### 2.0.5 (2024-11-10)

- [client] fix `send_template` return type `SentMessage`

### 2.0.4 (2024-11-08)

- [client] fix `reply_to_message`

### 2.0.3 (2024-11-02)

- [client] override `_flow_req_cls`
- [handlers] descriptive repr for `Handler`


### 2.0.2 (2024-10-30)

- [server] rely on update hash instead of update id to avid duplicate updates


### 2.0.1 (2024-10-30)

- [server] fix skip update in process (async)


### 2.0.0 (2024-10-30)

BREAKING CHANGES!! READ THE [MIGRATION GUIDE](https://github.com/david-lev/pywa/blob/v2/MIGRATION.md)

- [listeners]: Listeners are a new way to handle incoming user updates (messages, callbacks, etc.). They are more flexible, faster, and easier to use than handlers.
- [sent_message]: The `SentMessage` object returned by `send_message`, `send_image`, etc., contains the message ID and allows to act on the sent message with methods like `reply_x`, `wait_for_x` etc.
- [filters]: Filters are now objects that can be combined using logical operators. They are more powerful and flexible than the previous filter system.
- [handlers] allow to register callbacks without WhatsApp instance
- [flows] allow pythonic conditionals in `If` component
- [flows]: A new method `FlowCompletion.get_media(types.Image, key="img")` allows you to construct a media object and perform actions like `.download()` on it.
- [flows]: Decrypt media directly from FlowRequest using `.decrypt_media(key, index)`.
- [flows] rename `.data_key` and `.from_ref` to `.ref`
- [client]: The client can run without a token but won’t allow API operations (only webhook listening).
- [callback] allow to override callback data id
- [utils] bump graph-api version to `21.0`


#### 1.26.0 (2024-09-22)

- [flows] adding support of `RichText`
- [flows] adding support of `markdown` in `TextBody` and `TextCaption`
- [flows] adding `sensitive` attr to Screen, allowing to hide specific fields from the response summary
- [client] adding `reply_to_message` arg to `send_location`, `request_location`, `send_sticker`, and `send_audio`
- [message] adding `reply_location_request`


#### 1.25.0 (2024-08-15)

- [handlers] adding priority
- [client] adding QR methods (create update get and delete)
- [client] adding `get_flow_metrics` method
- [flows] adding to `DataSource` support for images/colors
- [flows] support `datetime` objs in `DatePicker`
- [flows] support `Screen` when using `.data_key_of(...)` and `.form_ref_of(...)`
- [flows] update flow json with indent and without ensuring ascii
- [flows] adding `health_status` to `FlowDetails`


#### 1.24.0 (2024-07-26)

- [server] validating `X-Hub-Signature-256` header
- [requirements] removing `requests`
- [server] default callback url registration delay to 3 sec


#### 1.23.0 (2024-07-14)

- [client] allowing to manage multiple numbers from the same client (Partner solutions)
- [flows] adding `.respond()` shortcut for `FlowRequest`
- [flows] allowing body in `FlowResponseError` subclasses


#### 1.22.0 (2024-06-16)

- [handlers] introducing `FlowRequestCallbackWrapper` to help split flow endpoint logic to multiple handlers
- [client] adding `add_flow_request_handler` method to register `FlowRequestHandler`s
- [flows] pop `flow_token` from `FlowCompletion`.response
- [docs] update examples


#### 1.21.0 (2024-06-14)

- [flows] added new components `PhotoPicker`, `DocumentPicker`, `If` and `Switch`
- [flows] added `.data_key_of` and `.form_ref_of` to refer from other screens
- [flows] added `description` to `CheckboxGroup` and to `RadioButtonsGroup`
- [utils] adding `flow_request_media_decryptor` function to decrypt medias from flow requests
- [client] allow updating flow application id with `update_flow_metadata`
- [server] remove event loop
- [docs] update examples
- [version] bump `FLOW_JSON` version to `4.0`


#### 1.20.2 (2024-06-02)

- [server] improve continue/stop handling

#### 1.20.1 (2024-06-02)


- [api] fix downloading media content-type

#### 1.20.0 (2024-06-02)

- [client] adding official support for async (limited support for now)


#### 1.19.0-rc.3 (2024-05-23)

- [api] fix uploads
- [server] expose `webhook_challenge_handler`, `webhook_update_handler` and `flow_request_handler`


#### 1.19.0-rc.2 (2024-05-17)

- [client] adding `skip_duplicate_updates` when callbacks take too long to return (~25s), defaults to True
- [client,handlers] allow to override `continue_handling`
- [message] fix async constructors
- [api] remove `requests_toolbelt` from deps
- [handlers] fix dynamic field name when `factory_before_filters`


#### 1.19.0-rc.1 (2024-05-08)

- [async] adding beta support for async!


#### 1.18.1 (2024-05-05)

- [client] fix document filename


#### 1.18.0 (2024-05-02)

- [client] allow to modify token and remove handlers/callbacks
- [tests] test client methods


#### 1.17.0 (2024-04-30)

- [client,message_status] Added param `tracker` to all send-message-methods in order to track the message status, allowing to pass `CallbackData` subclasses to`tracker` param
- [client,api] adding `update_conversational_automation` and `get_business_phone_number` to add and get `commands`, `ice_breakers` and enable `ChatOpened` events
- [filters] adding `send_to_me` filters shortcut and `replays_to` filters. mark as deprecated all match-specific-type filters and create generic `matches`, `regex` filters for all text containing updates
- [flows] adding `updated_at` to `FlowDetails`
- [message] fix `from_user` in system messages
- [errors] adding optionals `error_subcode` and `type` to all errors
- [logging] improve loggers performance
- [utils] bump graph api version to 19.0 and expose `Version` in the package level
- [docs] switch readme to markdown


#### 1.16.2 (2024-02-15)

- [client] fix sending single contact
- [filters] prioritize `/` over `!` in `filters.command(...)` and `filters.is_command`


#### 1.16.0 (2024-01-22)

- [chat_opened] adding a new type: `ChatOpened`
- [server] improve handlers and logs
- [types] warning on missing enum constant
- [flows] handle cases where there is no `flow_token` in `FlowCompletion` (When the flow completion sent from iOS)
- [tests] adding more tests

#### 1.15.0 (2024-01-14)

- [client] Added `register_phone_number` method
- [client] mark the `body` arg in send image/video/doc as deprecated. use `caption` instead
- [utils] bump `FLOW_JSON` version to 3.1
- [flows] allow `DataSource` in `FlowResponse` data
- [flows] `Image` .src can be dynamic
- [flows] default `ActionNext` to SCREEN
- [flows] adding `.success` for screen and adding in-docs examples



#### 1.14.0 (2024-01-01)

- [flows] define `Form` `init_values` from children `init_value`
- [flows] adding a new `ScreenData` type to be used in screen `.data`
- [flows] adding `.form_ref` and `.form_ref_of(form_name)` to form components
- [docs] adding s real-world example for a complex flow

#### 1.13.0 (2023-12-22)

- [flows] adding full support for [WhatsApp Flows](https://business.whatsapp.com/products/whatsapp-flows)!
- [client] adding `request_location` method to `WhatsApp` client
- [base_update] adding `.raw` attr to hold the original update
- [utils] adding `Version` to provide the latest versions to the api & flows, and to perform min checks

#### 1.13.0-rc.6 (2023-12-20)

- [utils] adding `Version` to provide the latest versions to the api & flows, and to perform min checks

#### 1.13.0-rc.5 (2023-12-18)

- [flows] add supported types for Layout and Form `.children` and fix FlowPreview.expires_at
- [webhook] validate `cryptography` is installed when using the default flows decryptor/encryptor

#### 1.13.0-rc.4 (2023-12-16)

- [client] expose `set_business_public_key`
- [flows] adding `DataKey` and `FormRef` to use when building a `FlowJSON`
- [template] adding support to create and send template with `FlowButton`
- [errors] remove `FlowInvalidError` (Too broad error code)

#### 1.13.0-rc.3 (2023-12-15)

- [errors] adding flows specific errors
- [flows] allow to `@on_flow_request` callbacks to return or raise `FlowResponseError` subclasses

#### 1.13.0-rc.2 (2023-12-14)

- [base_update] adding `.raw` attr to hold the original update
- [requirements] set `cryptography` as extra dependency

#### 1.13.0-rc.1 (2023-12-14)

- [flows] Adding beta support for [WhatsApp Flows](https://business.whatsapp.com/products/whatsapp-flows)!

#### 1.12.1 (2023-11-29)

- [filters] adding new filter called `sent_to` to filter updates even if `WhatsApp(..., filter_updates=False)`
- [webhook] renaming route callbacks names to allow multiple `WhatsApp` instances to use the same server
- [message_type] default missing to `UNKNOWN`
- [bugs] fix bug on interactive message without data


#### 1.12.0 (2023-11-20)

- [reply_to_msg] adding `ReferredProduct` to message context
- [filters] adding filter for messages that has `referred_product` in their context
- [types] unfrozen editable types
- [base_update] hash updates by their update ID
- [client] adding `dl_session` param of type `requests.Session` to `.upload_media` when uploading locally from URL
- [errors] adding more `template` and `flow` exceptions; fix typo in `TooManyMessages`

#### 1.11.1 (2023-11-07)

- [reaction] hot-fix for reaction when "unreacting" to a message
- [filters] adding `.extensions(...)` filter for all media filters

#### 1.11.0 (2023-11-01)

- [callback] adding support for `Optional[x]` annotation in `CallbackData` subclasses
- [media] allowing to pass `pathlib.Path` as a media file path
- [system] make all fields nullable in system update

#### 1.10.0 (2023-10-29)

- [template] adding support for `OtpType.ZERO_TAP` in new authentication template
- [callback] adding support for optional fields in `CallbackData`
- [tests] update `CallbackData` tests

#### 1.9.0 (2023-10-25)

- [handlers] add `StopHandling` to raise if you want to stop handling the update
- [errors] include `requests.Response` with all api errors
- [client] mark `keyboard` argument in `.send_message` as deprecated. use `buttons` instead

#### 1.8.0 (2023-10-20)

- [webhook] allow to register callback url by @david-lev in #18

#### 1.7.3 (2023-10-18)

- [callback] Treat the Template's `QuickReplyButtonData` as an incoming `CallbackButton` (Reported by @bcombes in #17)
- [handlers] adding `@functools.wraps` to all on_x decorators to preserve callbacks metadata


#### 1.7.2 (2023-10-12)

- [reply] reply to `CallbackButton`.id instead of to `.reply_to_message` by @yehuda-lev in #16
- [callback] change default `CallbackData` separators to unused characters (`¶` for clb sep, `~` for data sep and `§` for True boolean


#### 1.7.1 (2023-10-12)

- [callback] hot-fix for last booleans fields on `CallbackData` (WhatsApp Cloud API consider "1: " and "1:" as duplicate datas)


#### 1.7.0 (2023-10-12)

- [types] new `ButtonUrl` type
- [client] allowing to provide `mime_type` when sending media as bytes, open file or file path without extensions


#### 1.6.0 (2023-10-11)

- [handlers] apply callback data factory before filters by setting `factory_before_filters` to True when registering the handler


#### 1.5.4 (2023-10-08)

- [template] fix media key


#### 1.5.3 (2023-10-03)

- [webhook] faster field-to-handler matching
- [message-status] make `.pricing_model` optional


#### 1.5.2 (2023-10-03)

- [callback] better typing for `callback_data` and `factory`

#### 1.5.1 (2023-10-02)

- [build] Fix package imports


#### 1.5.0 (2023-10-02)

- [callback] allowing to override separators in `CallbackData` subclasses
- [tests] starting to adding tests
- [message] reaction messages are also replays (.is_reply)
- [api] bump api version to 18.0
- [template] new update type - `TemplateStatus`; remove deprecated headers
- [build] move to `pyproject.toml`
- [docs] tips and improvements


#### 1.4.1 (2023-09-12)

- [reaction] Fix ReactionFilter and TextFilter by @yehuda-lev in #12


#### 1.4.0 (2023-09-10)

- [callback] allowing to provide `factory` to construct callback data (`Button` and `Selection`) into custom object.
- [callback] adding type-safe `CallbackData` interface in order to send and receive typed callback data.
- [webhook] add protocols for supported web frameworks.


#### 1.3.0 (2023-09-06)

- [template] adding support for `CopyCodeButton` and add `Language` enum for better typing
- [filters] adding `from_countries` filter
- [typing] fix typos by @nallon in #10


#### 1.2.0 (2023-08-21)

- [template] adding support for `MPMButton` and `CatalogButton`.
- [template] rename and mark as deprecated template headers.


#### 1.1.0 (2023-08-20)

- [template] adding support for sending and creating template messages
- [errors] adding more errors


#### 1.0.0 (2023-08-16)

- FIRST STABLE RELEASE - VERSION 1.0.0
