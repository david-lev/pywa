# Media

::: pywa.types.media.Media
    options:
      members: ["download", "stream", "get_bytes", "delete", "reupload", "expires_at", "is_expired", "days_until_expiration"]
      inherited_members: ["download", "stream", "get_bytes", "delete", "reupload", "expires_at", "is_expired", "days_until_expiration"]

::: pywa.types.media.ArrivedMedia
    options:
      members: ["extension", "from_flow_completion"]
      inherited_members: ["extension", "from_flow_completion"]
      show_bases: true

::: pywa.types.media.MediaURL
    options:
      members: ["regenerate_url", "expires_at", "is_expired", "minutes_until_expiration"]
      inherited_members: ["regenerate_url", "expires_at", "is_expired", "minutes_until_expiration"]

::: pywa.types.media.UploadedBy
    options:
      members: false
