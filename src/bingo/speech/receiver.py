from pathlib import Path

UPLOAD_DIR = Path("/tmp/bingo")

UPLOAD_DIR.mkdir(
    exist_ok=True
)


class AudioReceiver:

    def save(
        self,
        filename,
        data
    ):

        path = UPLOAD_DIR / filename

        path.write_bytes(data)

        return path