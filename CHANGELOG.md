Changelog
=========

NOTE: pywa follows the [semver](https://semver.org/) versioning standard.

### 1.16.1 (2024-02-15)

- [client] fix sending single contact
- [filters] prioritize `/` over `!` in `filters.command(...)` and `filters.is_command`


### 1.16.0 (2024-01-22)

- [chat_opened] adding a new type: `ChatOpened`
- [server] improve handlers and logs
- [types] warning on missing enum constant
- [flows] handle cases where there is no `flow_token` in `FlowCompletion` (When the flow completion sent from iOS)
- [tests] adding more tests

### 1.15.0 (2024-01-14)

- [client] Added `register_phone_number` method
- [client] mark the `body` arg in send image/video/doc as deprecated. use `caption` instead
- [utils] bump `FLOW_JSON` version to 3.1
- [flows] allow `DataSource` in `FlowResponse` data
- [flows] `Image` .src can be dynamic
- [flows] default `ActionNext` to SCREEN
- [flows] adding `.success` for screen and adding in-docs examples



### 1.14.0 (2024-01-01)

- [flows] define `Form` `init_values` from children `init_value`
- [flows] adding a new `ScreenData` type to be used in screen `.data`
- [flows] adding `.form_ref` and `.form_ref_of(form_name)` to form components
- [docs] adding s real-world example for a complex flow

### 1.13.0 (2023-12-22)

- [flows] adding full support for [WhatsApp Flows](https://business.whatsapp.com/products/whatsapp-flows)!
- [client] adding `request_location` method to `WhatsApp` client
- [base_update] adding `.raw` attr to hold the original update
- [utils] adding `Version` to provide the latest versions to the api & flows, and to perform min checks

### 1.13.0-rc.6 (2023-12-20)

- [utils] adding `Version` to provide the latest versions to the api & flows, and to perform min checks

### 1.13.0-rc.5 (2023-12-18)

- [flows] add supported types for Layout and Form `.children` and fix FlowPreview.expires_at
- [webhook] validate `cryptography` is installed when using the default flows decryptor/encryptor

### 1.13.0-rc.4 (2023-12-16)

- [client] expose `set_business_public_key`
- [flows] adding `DataKey` and `FormRef` to use when building a `FlowJSON`
- [template] adding support to create and send template with `FlowButton`
- [errors] remove `FlowInvalidError` (Too broad error code)

### 1.13.0-rc.3 (2023-12-15)

- [errors] adding flows specific errors
- [flows] allow to `@on_flow_request` callbacks to return or raise `FlowResponseError` subclasses

### 1.13.0-rc.2 (2023-12-14)

- [base_update] adding `.raw` attr to hold the original update
- [requirements] set `cryptography` as extra dependency

### 1.13.0-rc.1 (2023-12-14)

- [flows] Adding beta support for [WhatsApp Flows](https://business.whatsapp.com/products/whatsapp-flows)!

### 1.12.1 (2023-11-29)

- [filters] adding new filter called `sent_to` to filter updates even if `WhatsApp(..., filter_updates=False)`
- [webhook] renaming route callbacks names to allow multiple `WhatsApp` instances to use the same server
- [message_type] default missing to `UNKNOWN`
- [bugs] fix bug on interactive message without data


### 1.12.0 (2023-11-20)

- [reply_to_msg] adding `ReferredProduct` to message context
- [filters] adding filter for messages that has `referred_product` in their context
- [types] unfrozen editable types
- [base_update] hash updates by their update ID
- [client] adding `dl_session` param of type `requests.Session` to `.upload_media` when uploading locally from URL
- [errors] adding more `template` and `flow` exceptions; fix typo in `TooManyMessages`

### 1.11.1 (2023-11-07)

- [reaction] hot-fix for reaction when "unreacting" to a message
- [filters] adding `.extensions(...)` filter for all media filters

### 1.11.0 (2023-11-01)

- [callback] adding support for `Optional[x]` annotation in `CallbackData` subclasses
- [media] allowing to pass `pathlib.Path` as a media file path
- [system] make all fields nullable in system update

### 1.10.0 (2023-10-29)

- [template] adding support for `OtpType.ZERO_TAP` in new authentication template
- [callback] adding support for optional fields in `CallbackData`
- [tests] update `CallbackData` tests

### 1.9.0 (2023-10-25)

- [handlers] add `StopHandling` to raise if you want to stop handling the update
- [errors] include `requests.Response` with all api errors
- [client] mark `keyboard` argument in `.send_message` as deprecated. use `buttons` instead

### 1.8.0 (2023-10-20)

- [webhook] allow to register callback url by @david-lev in #18

### 1.7.3 (2023-10-18)

- [callback] Treat the Template's `QuickReplyButtonData` as an incoming `CallbackButton` (Reported by @bcombes in #17)
- [handlers] adding `@functools.wraps` to all on_x decorators to preserve callbacks metadata


### 1.7.2 (2023-10-12)

- [reply] reply to `CallbackButton`.id instead of to `.reply_to_message` by @yehuda-lev in #16
- [callback] change default `CallbackData` separators to unused characters (`¶` for clb sep, `~` for data sep and `§` for True boolean


### 1.7.1 (2023-10-12)

- [callback] hot-fix for last booleans fields on `CallbackData` (WhatsApp Cloud API consider "1: " and "1:" as duplicate datas)


### 1.7.0 (2023-10-12)

- [types] new `ButtonUrl` type
- [client] allowing to provide `mime_type` when sending media as bytes, open file or file path without extensions


### 1.6.0 (2023-10-11)

- [handlers] apply callback data factory before filters by setting `factory_before_filters` to True when registering the handler


### 1.5.4 (2023-10-08)

- [template] fix media key


### 1.5.3 (2023-10-03)

- [webhook] faster field-to-handler matching
- [message-status] make `.pricing_model` optional


### 1.5.2 (2023-10-03)

- [callback] better typing for `callback_data` and `factory`

### 1.5.1 (2023-10-02)

- [build] Fix package imports


### 1.5.0 (2023-10-02)

- [callback] allowing to override separators in `CallbackData` subclasses
- [tests] starting to adding tests
- [message] reaction messages are also replays (.is_reply)
- [api] bump api version to 18.0
- [template] new update type - `TemplateStatus`; remove deprecated headers
- [build] move to `pyproject.toml`
- [docs] tips and improvements


### 1.4.1 (2023-09-12)

- [reaction] Fix ReactionFilter and TextFilter by @yehuda-lev in #12


### 1.4.0 (2023-09-10)

- [callback] allowing to provide `factory` to construct callback data (`Button` and `Selection`) into custom object.
- [callback] adding type-safe `CallbackData` interface in order to send and receive typed callback data.
- [webhook] add protocols for supported web frameworks.


### 1.3.0 (2023-09-06)

- [template] adding support for `CopyCodeButton` and add `Language` enum for better typing
- [filters] adding `from_countries` filter
- [typing] fix typos by @nallon in #10


### 1.2.0 (2023-08-21)

- [template] adding support for `MPMButton` and `CatalogButton`.
- [template] rename and mark as deprecated template headers.


### 1.1.0 (2023-08-20)

- [template] adding support for sending and creating template messages
- [errors] adding more errors


### 1.0.0 (2023-08-16)

- FIRST STABLE RELEASE - VERSION 1.0.0
