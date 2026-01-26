from pathlib import Path


def setup(app):
    app.connect("build-finished", generate_redirects)


def generate_redirects(app, exception):
    if exception:
        return

    outdir = Path(app.outdir)

    for index in outdir.rglob("index.html"):
        overview = index.parent / "overview.html"

        if overview.exists():
            continue

        overview.write_text(
            """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Moved</title>
  <link rel="canonical" href="./" />
  <meta http-equiv="refresh" content="0; url=./" />
  <script>window.location.replace("./");</script>
</head>
<body>
  <p>This page has moved to <a href="./">the new location</a>.</p>
</body>
</html>
""",
            encoding="utf-8",
        )
