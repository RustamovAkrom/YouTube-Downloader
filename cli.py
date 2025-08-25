import argparse
from typing import Optional, List


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="ytdown",
        description="Надёжный загрузчик YouTube на yt-dlp (видео/аудио/плейлисты/субтитры).",
    )
    p.add_argument("--url", required=True, help="Ссылка на видео или плейлист")
    p.add_argument("--type", choices=["video", "audio", "playlist", "subs"], default="video")
    p.add_argument("--outdir", default=None, help="Папка сохранения (по умолчанию зависит от типа)")
    p.add_argument("--quality", default="1080", help="Максимальная высота видео (например 720/1080/1440/2160)")
    p.add_argument("--container", choices=["mp4", "mkv"], default="mp4", help="Контейнер выходного файла")
    p.add_argument("--audio-format", choices=["m4a", "mp3"], default="m4a", help="Формат аудио при --type audio")
    p.add_argument("--rate-limit", default=None, help="Ограничение скорости, напр. 2M (байт/сек)")
    p.add_argument("--subs", action="store_true", help="Скачать/встроить субтитры (для видео/плейлиста)")
    p.add_argument("--subs-embed", action="store_true", help="Встраивать субтитры в контейнер")
    p.add_argument("--subs-langs", default="en,ru,auto", help="Языки субтитров через запятую")
    p.add_argument("-q", "--quiet", action="store_true", help="Тише логирование")
    return p.parse_args(argv)
