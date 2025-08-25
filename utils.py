import os
import shutil
from typing import Dict, Any, Optional, List
from helper import LOG


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
