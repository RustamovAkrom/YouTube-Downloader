from __future__ import annotations
import os
import shutil
from helper import LOG
from typing import Dict, Any, Optional, List

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


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
        a_pref += "bestaudio"
    
    return f"{v_pref}+{a_pref}/best[height<={quality}]/best"


def progress_hook(d: dict[str, any]) -> None:
    if d.get("status") == "downloading":
        eta = d.get("eta")
        speed = d.get("speed")
        percent = d.get("_percent_str")
        LOG.info("⬇️ %s | %s | ETA: %ss", percent, d.get("_speed_str") or speed, eta)

    elif  d.get("status") == "finished":
        LOG.info("✅ Загрузка завершена: %s", d.get("filename"))


def build_ydl_opts(
        outdir: str,
        filename_template: str,
        concurent_fragments: int = 4,
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
        "concurent_fragment downloads": concurent_fragments, # для HLS/DASH
        "retries": retries,
        "fragment_retries": retries,
        "ignoreerrors": False,
        "noprogress": False if not quiet else True,
        "progress_hooks": [progress_hook],
        "ratelimit": rate_limit, # например "2M" (байт/сек)
        "restrictfilenames": True, # без пробелов/юникода в именах
        "windowsfilenames": True, # безопасные имена для Windows
        "logger": LOG,
        # Небольшая защита от зависаний сети
        "socket_timeout": 30,
        # Иногда полезно:
        "cachedir": os.path.join(outdir, ".cache-yt"),
        "nopart": False, # сохранять .part, чтобы возобновлять
    }

    if write_subs:
        opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": sub_langs or ['en', 'ru', 'auto'],
            "embedsubtitles": embed_subs,
        })

    if postprocessors:
        opts['postprocessors'] = postprocessors
    
    if format_str:
        opts['format'] = format_str
    
    if keep_video:
        opts['keepvideo'] = True

    return opts


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
        raise RuntimeError("FFmpeg not found in PATH. You must install FFmpeg.")
    
    fmt = pick_video_format(quality, container)

    post = [
        {
            "key": "FFmpegVideoConvertor",
            "preferedformat": container, # mp4/mkv
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
            raise RuntimeError(f"Error in download video: {e}") from e
        

def download_audio(
    url: str,
    outdir: str = "downloads/audio",
    audio_format: str = "m4a", # m4a или mp3
    rate_limit: Optional[str] = None,
) -> None:
    """
    Выкачивает аудио дорожку (без видео) и приводит к m4a/mp3.
    """

    if not ffmpeg_available():
        raise RuntimeError("FFmpeg not found in PATH. You must install FFmpeg.")
    
    # Извлекаем лучшую аудио дорожку и конвертируем
    post = [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": "0", # без потерь сверху
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
            raise RuntimeError(f"Error download audio: {e}") from e
        

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
