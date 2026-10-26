# Sending Media Messages

## Sending media from URL


```python title="Media message from URL" linenums="1"
from pywa import WhatsApp

wa = WhatsApp(phone_id="972123456789", token="xxxxx")
recipient = "972987654321"

# - From URL
wa.send_image(
    to=recipient,
    image="https://cdn.pixabay.com/photo/2014/10/01/10/44/animal-468228_1280.jpg",
)
```


## Sending media from local file


```python title="Media message from local file" linenums="1"
from pywa import WhatsApp

wa = WhatsApp(phone_id="972123456789", token="xxxxx")
recipient = "972987654321"

# - From local file
wa.send_video(to=recipient, video="/path/to/video.mp4")
```


## Sending media from file id


```python title="Media message from file id" linenums="1"
from pywa import WhatsApp

wa = WhatsApp(phone_id="972123456789", token="xxxxx")
recipient = "972987654321"

audio_id = wa.upload_media(media="/path/to/audio.ogg", mime_type="audio/ogg")
wa.send_audio(to=recipient, audio=audio_id)
```


## Sending media from bytes


```python title="Media message from bytes" linenums="1"
from pywa import WhatsApp
import requests

wa = WhatsApp(phone_id="972123456789", token="xxxxx")
recipient = "972987654321"

res = requests.get(
    "https://cdn.pixabay.com/photo/2014/10/01/10/44/animal-468228_1280.jpg"
)
wa.send_document(to=recipient, document=res.content, filename="animal.jpg")
```
