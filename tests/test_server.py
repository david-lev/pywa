import pytest
from unittest.mock import Mock

from pywa import utils as pywa_utils
from pywa.server import Server, StopHandling, ContinueHandling


def test_webhook_updates_validator():
    assert pywa_utils.webhook_updates_validator(
        app_secret="1222e786b144d0e85b9f365372d93676",  # This secret key is already reset
        request_body=b'{"object":"whatsapp_business_account","entry":[{"id":"264937493375603","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"15550953877","phone_number_id":"277321005464405"},"contacts":[{"profile":{"name":"PyWa Tests"},"wa_id":"972544401243"}],"messages":[{"from":"972544401243","id":"wamid.HBgMOTcyNTQ0NDAxMjQzFQIAEhggM0RFQTNCMEEwRTY3QzUwODYzMDc4NjQ4QzM4ODAxM0YA","timestamp":"1730231903","text":{"body":"Hey there! I am using PyWa."},"type":"text"}]},"field":"messages"}]}]}',
        x_hub_signature="sha256=54edfa1d7259e0eb13c677cc7d73d1b5c86cfa12433d19156e058ab9251bc441",
    )


# This private key is already reset
private_key = """
-----BEGIN ENCRYPTED PRIVATE KEY-----
MIIFJDBWBgkqhkiG9w0BBQ0wSTAxBgkqhkiG9w0BBQwwJAQQkgClH0obPRRd3cmr
s0LvRAICCAAwDAYIKoZIhvcNAgkFADAUBggqhkiG9w0DBwQIWxsUnYjosHEEggTI
tIwws0TcJNJ+IoMfNfalxb8FpV8JzIXNPKoS2vBNhni3F6tk6tYSsBW7p5Wl/1jv
0fmf6iZhGgidFT5KvxRI7Z9FyD4FAKKxMsIsrxdqblupaB/2L1dHM2foBmKZTKVP
pMkiGYCRM+uPQWao/etBvTf1IKQw5phFJ6J/NVhlU6hSh3SjMp9CN4Xy6rA7wcfu
yYfrSUBHoCZZMvdWkCxo9sQ0N/nvU1FpBO0ZZQ+WDRKKg3g8BD8jWKRVM+uzZdVx
oWLoqkIWlNuCbObYsWvK07q9qryG0WeeZtPRti6Tp/TW2NMSqIN5Zx1jHLAYPU0V
3fgt3TmHPphy8etyXEg7PBJToCgTw6snnDqQDJm4nfJPg9UxxUvkkN8Tk+5P3o/0
E2Hf3RhYIqraKhuZAToA5Isniez/L/O5Fyjye0ShOFF9auhsmLDKbdG6wL+2CX1+
cQAash4HE2Xlj9v2iVC5mlnU9e7F1EyhJNAkmbr+i2z+93Wp/XytAx9xGV6lt7J8
gv454dCSQ5brByM/D12yyB5mcKX73MkaECa2iu/qH30H10S91IgiLUOQsS9A8ABi
S32U9SlYGfwlyV7izOXiS5vnk2XiihYFKPIdoNgcq3FPDXZoJr9u/ipZl/viTzWP
2V9DTODpTWuERIUCi8Lrg82HA62yNLO6Z5ib7+oHgpsTrhxWbqvxa8T4EL7V2Hx+
AqD2/M9easd2Atl6mI8uekjndL8sKNJ2kNlG54PMddgZzoIMYPnYp0ZPCtds+KIj
pwHK0nGL+kih0R9FLHLm0YKIYgD/i13N0vD+qSd0/PC66Bcnm5CqDlOYMyweBzvv
TrnUgTCUyMVGbKJ4mpBMHQOSoVfGuE18zkfvoUmqXNEUiOj3v61ODs50zrz9GzeL
r8mehVuSY82CDqPM7vbJS+UIgrPi9cqhxv1APcV+FW+nDux3hyvyG6mHxSOoaTz/
tmAXqxZ7IJKRJW+p2Qw9FjSrQOjjfCDWRKNd3m7WhHlceKWuh6fargYbs3A7jIf7
+BaGTOfx/EcbgWrrvQ6FgdNqiijUfxmk0nTtFAaAACs/V9wOiqZLCBP+Uqv5GL7T
X2+yrJtpe2A/Jc/0VC7utOK7HPHO9y+mqkFm2SzCUnN4PDCIm6L4yDdzdjsAxj6n
YcG2AYnZhPGstAXYeQThbbgnOa76hpr4FDFb7y5OMQvbb7uDAs6goHd8yrlGdMub
KqalC3IWh9RbnDbXQLFkTG9ijaswbKu0Q4DRIjVtN/RRlYrLqKE/P/uy99GQ+zxC
vUSUci1YVbkGaTC7OMeLWf2gPptcEOXRqZhluEFIxIeMD2ykv50nfZWl6wBQRyas
+MsEoHCZYtb8ZgA8adAh0bFo/zsh9nu/HeXN6Rk0DIzBv31t6bIubsZ8VAybVetG
vkivZ9yrc5R/lNYCmIIk0YqYr4IU8GMru7l11Ojui08RTESwZ5KcsH1s9CFWuUG4
D8SsbEVopM4IbnZi0X5WWyHreEjfBrcP6+/o+3vzi+sq76v17PXlalypi4kuUjAD
78w/o5vWmS+DWkrr0DqmQZ3nFX3fcrBbP1blr1Nlb5iv3Rwy7tVMF87tpgrnk/4Y
337xpCvNLXW0EwL6KdWqJ7Y6KLjLDmeT
-----END ENCRYPTED PRIVATE KEY-----
"""


def test_default_flow_request_decryptor_encryptor():
    payload = {
        "encrypted_flow_data": "sCTmBCqjs0GkkX6n/nyZDuyjpaijuelY3I/8rlr1ZIEymEzCMnDGQdxQ9OGaKw0CEaWSgc/GLhuixa8NTQNYXAyVfTaU9H2FWEabWUb8nbZYRdYy81XHUkDCodl4SvBhhufEag==",
        "encrypted_aes_key": "gSTeWDqfKqo1eL73VstmrMm5k5lymwUwXCfuxauPFPoW7Ji9dgcG74Y6YRtoYOAch6Z/AgrR7EAlsRi/s8xT/Gx2WWz6zfcXPUQVpoIlp7EgC+HmmA2ZK64g/107yL+vKoUdL0mWJHQf1ml12HszBxOtNlW+7GAMPESNDqGpgy1R3Zgz/luStp2INtigps9w2j9+Ktp0smqxHqpUkBWp8xxoWVvzPK4H0jcFm7sjFMpiJ1e1EjApo7iDqldys0tMRC+KoOjJVD6aq1gY5s2yYL7iCXXgEAKJItTk/4/mbWWNkRtd9NoEGnMHilcjYOzlUCHehAO9fos+WCLE87JAXw==",
        "initial_vector": "5eCmDjs+VAJwdo5caZtgbw==",
    }
    decrypted_data, aes_key, iv = pywa_utils.default_flow_request_decryptor(
        encrypted_flow_data_b64=payload["encrypted_flow_data"],
        encrypted_aes_key_b64=payload["encrypted_aes_key"],
        initial_vector_b64=payload["initial_vector"],
        private_key=private_key,
        password="pywa",
    )
    assert decrypted_data == {
        "data": {},
        "flow_token": "my_flow_token",
        "screen": "",
        "action": "INIT",
        "version": "3.0",
    }

    assert (
        pywa_utils.default_flow_response_encryptor(
            response={"version": "3.0", "screen": "SUCCESS", "data": {"key": "value"}},
            aes_key=aes_key,
            iv=iv,
        )
        == "FBEoV73B8mnSt+nzfurVK704zkwHsr1uu/m953h5vNdri5G4Pe/BoDTh6SgzgjrrZ4iP12GO3kti8YW7Tn1KibKaRf8LE/gps2ATJq3nWSCI"
    )


def test_flow_request_media_decryptor():
    assert (
        pywa_utils._flow_request_media_decryptor(
            cdn_file=b"\x84a\xd2~\xd7\xe5f\xf0T$Yv\xa3\xa3\xb0\xc3\xa9>+\xca7\xd5\x81\x0cw\xe7/a\x92Q\xce\xfe\xa8>\xeaP\x915\x0b[/\x83\xd23gB\xd4\xf0\xd4c\x95w\xc6\xa2>\xb38\x7f[\xef\x87\x8d,Y\xce\xe9\xe3\xaf\x88\x04\x91e\xfc\xf9dK\\\xd0\x8e^\xa4\x88\xd7\x101JI2T\x13\xe1\xf5BR\r\x1et\xdeO@K\xbd\x95DQ\xb1(\x00\x84\xe5\xed\xe90\xf0\xd3k\xb0\xf2\x01\x88(7%\xd0\xc63<\x91\x96\x9c\xd4*\xbb.\xed\xa1D\x01D\xdd\xfa\x96eK\xd9\xe44H\x16\x0e\xb8eC\xfe\x1a\xfb\x14/\x1b\x81\x93\xef\xc5\xc2}\xe1\xd2\x9d\xca\xdf\x96\xb0V\xe96\xfcL9\x82KE\xfe\x11\xea\x8a\x9e\x13{\x19\xaba\x05\xcaW\x11\xa3#B\xa2\x93\x95&\x925~\xec\xc5Qt\x16\xed\x88\r\x16\xeb\x06$\xd8\x1c\x9d\xcc\xbec\x9f\x9e\x0bkz/\xffK\x18\x8ag(wO9t\xd7\xcc\xd7za\x94\xe3\x85a<\x8f<\xb6\x19]\xfev\x92\xa7T\xb6\x0cE\x86\x04\xfb\xdb\xb8\xb2\x93\x1d\x12\xa3>\xb1\x01vR\xde\xcb\xdf\xb2\xb3E\xdaHv\xcbg\x1bZ\xd0\x82)\xda\x14\xadL\x9b\x99\x03\n\xa9p\xda8\x11`\xc8\xfe\xeaAe\x85\xd7\x9c\r\x7f\x88\xd9 \xaf\xc8\x93\x98\xe7\xe1 Y\xc2\xc6\xc8\x9b9\x9bf\xa2\x84DL\xb7\xfc\xab\x1c\xd3yH\xb5\xedE\xc9\xddi\xd1f\xff\x18\x84\xcd\xbc\x80\x91\xa4\x04gZ\x85\x9ae\xd8\xc1Pf+\xaa=\x08\x9b~0\x16\x96\x9b\xd3\x13]\xb1Z\xca\xd4\xf8(\xf4\x14\x02\xb5\x13R\x06wY\xc4\xf3\xe6;\x10T\xca\t\xf5C\xe6)5\xf7\xef\xd1DW+\xf5\x94\xc0y\x9d\xdd\x90\x81\x1c)r}NE\x981m@\xed\x9fq\xfb^\xe0\xfaR;\xdf\x16\xce\x081\x95i={\xfeK]",
            encryption_metadata={
                "encryption_key": "202pQMDtZoAMwJwZJFVPqQOgdJRBahBmGywwSXz5tAY=",
                "hmac_key": "A/72TYylRAHTg/CdXpBtC6T6qcJ2C7Cf2qzZ/hqVASM=",
                "iv": "t1MOy02KXLbsH+NYkqkRXQ==",
                "plaintext_hash": "ZvSgxwXg5fWL7v7ggGHXtMCZYTf/nVFasOdX0p6kiP4=",
                "encrypted_hash": "pDhRHkyevzgkdg5ObY+MfzW5J6/ObZj/OrmAvyUeYA8=",
            },
        )
        == b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00\x84\x00\x06\x06\x06\x06\x07\x06\x07\x08\x08\x07\n\x0b\n\x0b\n\x0f\x0e\x0c\x0c\x0e\x0f\x16\x10\x11\x10\x11\x10\x16"\x15\x19\x15\x15\x19\x15"\x1e$\x1e\x1c\x1e$\x1e6*&&*6>424>LDDL_Z_||\xa7\x01\x06\x06\x06\x06\x07\x06\x07\x08\x08\x07\n\x0b\n\x0b\n\x0f\x0e\x0c\x0c\x0e\x0f\x16\x10\x11\x10\x11\x10\x16"\x15\x19\x15\x15\x19\x15"\x1e$\x1e\x1c\x1e$\x1e6*&&*6>424>LDDL_Z_||\xa7\xff\xc2\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\'\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x02\xaa\x07\xff\xc4\x00\x02\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00!\x03\xff\xc4\x00\x02\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10\xf3\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x02\x01\x01?\x00\x7f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x03\x01\x01?\x00\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01?\x02\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01?!\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01?\x10\x7f\xff\xd9'
    )


@pytest.fixture
def mock_handler(mocker):
    handler = mocker.Mock()
    handler.handle = mocker.Mock()
    return handler


@pytest.fixture
def mock_update(mocker):
    return mocker.Mock()


@pytest.fixture
def server_with_handlers(mock_handler):
    server = Server(
        None,
        "/webhook",
        None,
        None,
        None,
        None,
        "valid_token",
        None,
        None,
        None,
        None,
        None,
        True,
        False,
        False,
    )
    server._handlers = {Mock: [mock_handler]}
    return server


def test_invoke_callbacks_calls_all_handlers(
    server_with_handlers, mock_update, mock_handler
):
    server_with_handlers._invoke_callbacks(Mock, mock_update)
    mock_handler.handle.assert_called_once_with(server_with_handlers, mock_update)


def test_invoke_callbacks_stops_on_stop_handling(
    server_with_handlers, mock_update, mock_handler
):
    mock_handler.handle.side_effect = StopHandling
    server_with_handlers._invoke_callbacks(Mock, mock_update)
    mock_handler.handle.assert_called_once_with(server_with_handlers, mock_update)


def test_invoke_callbacks_continues_on_continue_handling(
    server_with_handlers, mock_update, mock_handler
):
    mock_handler.handle.side_effect = ContinueHandling
    server_with_handlers._invoke_callbacks(Mock, mock_update)
    mock_handler.handle.assert_called_once_with(server_with_handlers, mock_update)


def test_invoke_callbacks_stops_on_handled(
    server_with_handlers, mock_update, mock_handler
):
    mock_handler.handle.return_value = True
    server_with_handlers._invoke_callbacks(Mock, mock_update)
    mock_handler.handle.assert_called_once_with(server_with_handlers, mock_update)
