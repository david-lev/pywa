from pywa import errors


def test_error_codes_uniqueness():
    all_error_codes = [
        tuple(e.__error_codes__) for e in errors.WhatsAppError._all_exceptions()
    ]
    assert len(all_error_codes) == len(set(all_error_codes))
