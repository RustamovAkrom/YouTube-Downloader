Ниже — **практичный, устойчивый к ошибкам** шаблон на Python для скачивания **видео, аудио, плейлистов и субтитров** с YouTube через библиотеку **yt-dlp**. Он аккуратно управляет форматами, качеством, ретраями, логами, путями и даёт чистый API (функции) + удобный CLI.

> ⚖️ Юр-момент: скачивайте только то, на что у вас есть право (собственный контент, разрешённые лицензии, офлайн-доступ с согласия правообладателя). Не обходите DRM и не нарушайте условия YouTube.

---

# Установка

```bash
# 1) Установить Python 3.10+
python -m pip install --upgrade pip

# 2) Установить yt-dlp
pip install yt-dlp

# 3) Поставить FFmpeg (для mux в mp4/mkv и извлечения аудио)
# Windows (через winget):
winget install --id Gyan.FFmpeg -e
# или скачайте сборку FFmpeg и добавьте в PATH
```

---

# Готовый скрипт: `ytdown.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ytdown.py — аккуратный загрузчик YouTube:
- Видео (mp4/mkv) с автосборкой bestvideo+bestaudio через FFmpeg
- Аудио (m4a/mp3) с нормализацией метаданных
- Плейлисты (с сохранением порядка)
- Субтитры (авто и указанные языки)
- Прогресс-хуки, повторы, структурированные пути

Зависимости: yt-dlp, FFmpeg в PATH
"""

from __future__ import annotations
import argparse
import logging
import os
import sys
import shutil
from typing import Dict, Any, Optional, List
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

LOG = logging.getLogger("ytdown")

# --------- Утилиты ----------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None

def pick_video_format(quality: str, container: str) -> str:
    """
    Возвращает выражение формата для yt-dlp.
    Примеры:
      - best с предпочитаемым разрешением: "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
      - контейнер можно подсказать постпроцессором, но формат подберём оптимальный.
    """
    # приоритет по высоте; ограничиваем верх по запросу
    # если контейнер mp4 — стараемся избегать webm при равенстве (хорошо для совместимости)
    prefer_mp4 = container.lower() == "mp4"
    v_pref = "bestvideo[height<=%s]" % quality if quality.isdigit() else "bestvideo"
    a_pref = "bestaudio"

    # предпочесть кодеки, совместимые с mp4
    if prefer_mp4:
        v_pref += "[ext=mp4]/bestvideo[height<=%s]" % (quality if quality.isdigit() else "4320")
        a_pref += "[ext=m4a]/bestaudio"

    # Комбинация + fallback на простой "best"
    return f"{v_pref}+{a_pref}/best[height<={quality}]/best"

def progress_hook(d: Dict[str, Any]) -> None:
    if d.get("status") == "downloading":
        eta = d.get("eta")
        speed = d.get("speed")
        percent = d.get("_percent_str")
        LOG.info("⬇️ %s | %s | ETA: %ss", percent, d.get("_speed_str") or speed, eta)
    elif d.get("status") == "finished":
        LOG.info("✅ Загрузка завершена: %s", d.get("filename"))

# --------- Конфигурация YDL ----------

def build_ydl_opts(
    outdir: str,
    filename_template: str,
    concurrent_fragments: int = 4,
    retries: int = 5,
    rate_limit: Optional[str] = None,
    quiet: bool = False,
    write_subs: bool = False,
    sub_langs: Optional[List[str]] = None,
    embed_subs: bool = False,
    format_str: Optional[str] = None,
    keep_video: bool = False,
    postprocessors: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    ensure_dir(outdir)

    opts: Dict[str, Any] = {
        "outtmpl": {
            "default": os.path.join(outdir, filename_template)
        },
        "concurrent_fragment downloads": concurrent_fragments,  # для HLS/DASH
        "retries": retries,
        "fragment_retries": retries,
        "ignoreerrors": False,
        "noprogress": False if not quiet else True,
        "progress_hooks": [progress_hook],
        "ratelimit": rate_limit,  # например "2M" (байт/сек)
        "restrictfilenames": True,  # без пробелов/юникода в именах
        "windowsfilenames": True,   # безопасные имена для Windows
        "logger": LOG,
        # Небольшая защита от зависаний сети
        "socket_timeout": 30,
        # Иногда полезно:
        "cachedir": os.path.join(outdir, ".cache-yt"),
        "nopart": False,  # сохранять .part, чтобы возобновлять
    }

    if write_subs:
        opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": sub_langs or ["en", "ru", "auto"],
            "embedsubtitles": embed_subs,
        })

    if postprocessors:
        opts["postprocessors"] = postprocessors

    if format_str:
        opts["format"] = format_str

    if keep_video:
        opts["keepvideo"] = True

    return opts

# --------- Высокоуровневые операции ----------

def download_video(
    url: str,
    outdir: str = "downloads/video",
    quality: str = "1080",
    container: str = "mp4",
    rate_limit: Optional[str] = None,
    write_subs: bool = False,
    sub_langs: Optional[List[str]] = None,
    embed_subs: bool = False,
) -> None:
    """
    Скачивает лучшее видео + аудио, мержит через FFmpeg в указанный контейнер.
    """
    if not ffmpeg_available():
        raise RuntimeError("FFmpeg не найден в PATH. Установите FFmpeg.")

    fmt = pick_video_format(quality, container)

    post = [
        {
            "key": "FFmpegVideoConvertor",
            "preferedformat": container,  # mp4/mkv
        }
    ]

    ydl_opts = build_ydl_opts(
        outdir=outdir,
        filename_template="%(playlist_index|>03)s-%(title).200B-%(id)s.%(ext)s",
        rate_limit=rate_limit,
        write_subs=write_subs,
        sub_langs=sub_langs,
        embed_subs=embed_subs,
        format_str=fmt,
        postprocessors=post,
    )

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except DownloadError as e:
            raise RuntimeError(f"Ошибка загрузки видео: {e}") from e

def download_audio(
    url: str,
    outdir: str = "downloads/audio",
    audio_format: str = "m4a",  # m4a или mp3
    rate_limit: Optional[str] = None,
) -> None:
    """
    Выкачивает аудио дорожку (без видео) и приводит к m4a/mp3.
    """
    if not ffmpeg_available():
        raise RuntimeError("FFmpeg не найден в PATH. Установите FFmpeg.")

    # Извлекаем лучшую аудио дорожку и конвертируем
    post = [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": "0",  # без потерь сверху
        },
        {
            "key": "FFmpegMetadata",
        }
    ]

    ydl_opts = build_ydl_opts(
        outdir=outdir,
        filename_template="%(playlist_index|>03)s-%(title).200B-%(id)s.%(ext)s",
        rate_limit=rate_limit,
        format_str="bestaudio/best",
        postprocessors=post,
    )

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except DownloadError as e:
            raise RuntimeError(f"Ошибка загрузки аудио: {e}") from e

def download_playlist(
    url: str,
    outdir: str = "downloads/playlist",
    mode: str = "video",   # "video" или "audio"
    quality: str = "1080",
    container: str = "mp4",
    audio_format: str = "m4a",
    rate_limit: Optional[str] = None,
    write_subs: bool = False,
    sub_langs: Optional[List[str]] = None,
    embed_subs: bool = False,
) -> None:
    """
    Скачивает весь плейлист, сохраняя индекс треков.
    """
    if mode == "video":
        download_video(
            url=url,
            outdir=outdir,
            quality=quality,
            container=container,
            rate_limit=rate_limit,
            write_subs=write_subs,
            sub_langs=sub_langs,
            embed_subs=embed_subs,
        )
    elif mode == "audio":
        download_audio(
            url=url,
            outdir=outdir,
            audio_format=audio_format,
            rate_limit=rate_limit,
        )
    else:
        raise ValueError("mode должен быть 'video' или 'audio'.")

def download_subtitles_only(
    url: str,
    outdir: str = "downloads/subs",
    sub_langs: Optional[List[str]] = None,
    embed_subs: bool = False,
) -> None:
    """
    Только субтитры (авто и явные языки), без видео/аудио.
    """
    ydl_opts = build_ydl_opts(
        outdir=outdir,
        filename_template="%(title).200B-%(id)s.%(ext)s",
        write_subs=True,
        sub_langs=sub_langs or ["en", "ru", "auto"],
        embed_subs=embed_subs,
        format_str="best",  # чтобы получить метаданные и субы
    )
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise RuntimeError("Не удалось получить информацию о ролике.")
            # включаем скачивание субтитров
            ydl.download([url])
        except DownloadError as e:
            raise RuntimeError(f"Ошибка загрузки субтитров: {e}") from e

# --------- CLI ----------

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

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )

    try:
        if args.type == "video":
            download_video(
                url=args.url,
                outdir=args.outdir or "downloads/video",
                quality=args.quality,
                container=args.container,
                rate_limit=args.rate_limit,
                write_subs=args.subs,
                sub_langs=[s.strip() for s in args.subs_langs.split(",")],
                embed_subs=args.subs_embed,
            )
        elif args.type == "audio":
            download_audio(
                url=args.url,
                outdir=args.outdir or "downloads/audio",
                audio_format=args.audio_format,
                rate_limit=args.rate_limit,
            )
        elif args.type == "playlist":
            download_playlist(
                url=args.url,
                outdir=args.outdir or "downloads/playlist",
                mode="video",  # хотите только аудио — запустите с --type audio и url плейлиста
                quality=args.quality,
                container=args.container,
                rate_limit=args.rate_limit,
                write_subs=args.subs,
                sub_langs=[s.strip() for s in args.subs_langs.split(",")],
                embed_subs=args.subs_embed,
            )
        elif args.type == "subs":
            download_subtitles_only(
                url=args.url,
                outdir=args.outdir or "downloads/subs",
                sub_langs=[s.strip() for s in args.subs_langs.split(",")],
                embed_subs=args.subs_embed,
            )
        else:
            raise ValueError("Неизвестный тип операции.")
        return 0
    except Exception as e:
        LOG.error("⚠️ %s", e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## Примеры запуска

```bash
# 1) Видео 1080p в MP4 (автосборка лучшего видео+аудио через FFmpeg)
python ytdown.py --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" --type video --quality 1080 --container mp4

# 2) Аудио-трек в M4A (лучше для мобильных)
python ytdown.py --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" --type audio --audio-format m4a

# 3) Плейлист целиком в 720p
python ytdown.py --url "https://www.youtube.com/playlist?list=PLXXXXXXXX" --type playlist --quality 720

# 4) Только субтитры (авто + en/ru)
python ytdown.py --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" --type subs --subs-langs "en,ru,auto"

# 5) Ограничить скорость (чтобы не душить сеть)
python ytdown.py --url "https://www.youtube.com/watch?v=XXXXXXXXXXX" --type video --rate-limit 2M
```

---

## Почему это «структурно и оптимизично»

* **Надёжность**: повторные попытки (`retries`), возобновляемые `.part` файлы, таймауты сокетов.
* **Чистые имена файлов**: `restrictfilenames`, безопасно для Windows.
* **Качество под контроль**: выражение формата выбирает лучшую пару `bestvideo+bestaudio` c ограничением по высоте и предпочтением `mp4`.
* **FFmpeg-постпроцессы**: аккуратный mux видео/аудио и извлечение аудио с метаданными.
* **Субтитры**: автоматические и ручные языки, опционально встраивание.
* **Плейлисты**: сохранение индекса `%(playlist_index|>03)s-...` для стабильного порядка.
* **Ограничение скорости**: чтобы не ловить троттлинг сети/провайдера.
* **Единый API**: функции `download_video/audio/playlist/...` легко встраивать в ваш код/бота.

---

## Интеграция в бота/веб

* **Пул потоков**: вызывайте `download_*` в `ThreadPoolExecutor`, чтобы не блокировать event-loop `aiogram`.
* **Очередь задач**: кладите ссылки в очередь, возвращайте пользователю статус и путь готового файла.
* **Валидация URL**: заранее проверяйте, что это YouTube-ссылка и что ролик доступен.

Если понадобится, могу дописать асинхронный «обёртчик» для Aiogram и Django-админку, чтобы видеть очередь загрузок, прогресс и ошибки, а также добавить конвертацию в нужные пресеты (например, H.264 + AAC, размер <= X МБ) и автозачистку старых файлов.
