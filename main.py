from __future__ import annotations
import logging
import sys
from typing import Optional, List

from helper import LOG
from ytdown import download_video, download_audio, download_playlist, download_subtitles_only
from cli import parse_args


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
