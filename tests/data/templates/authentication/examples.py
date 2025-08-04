from pywa.types.templates import *  # noqa: F403

authentication_code_autofill_button = Template(
    name="authentication_code_autofill_button",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.AUTHENTICATION,
    message_send_ttl_seconds=60,
    components=[
        AuthenticationBody(add_security_recommendation=True),
        AuthenticationFooter(code_expiration_minutes=10),
        Buttons(
            buttons=[
                OneTapOTPButton(
                    text="Copy Code",
                    autofill_text="Autofill",
                    supported_apps=[
                        OTPSupportedApp(
                            package_name="com.example.luckyshrub",
                            signature_hash="K8a/AINcGX7",
                        ),
                        OTPSupportedApp(
                            package_name="com.example.luckyshrub",
                            signature_hash="K8a/AINcGX7",
                        ),
                    ],
                )
            ]
        ),
    ],
)

authentication_code_copy_code_button = Template(
    name="authentication_code_copy_code_button",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.AUTHENTICATION,
    message_send_ttl_seconds=60,
    components=[
        AuthenticationBody(add_security_recommendation=True),
        AuthenticationFooter(code_expiration_minutes=5),
        Buttons(
            buttons=[
                CopyCodeOTPButton(
                    text="Copy Code",
                )
            ]
        ),
    ],
)

zero_tap_auth_template = Template(
    name="zero_tap_auth_template",
    language=TemplateLanguage.ENGLISH_US,
    category=TemplateCategory.AUTHENTICATION,
    message_send_ttl_seconds=60,
    components=[
        AuthenticationBody(add_security_recommendation=True),
        AuthenticationFooter(code_expiration_minutes=5),
        Buttons(
            buttons=[
                ZeroTapOTPButton(
                    text="Copy Code",
                    autofill_text="Autofill",
                    zero_tap_terms_accepted=True,
                    supported_apps=[
                        OTPSupportedApp(
                            package_name="com.example.luckyshrub",
                            signature_hash="K8a/AINcGX7",
                        ),
                    ],
                )
            ]
        ),
    ],
)
