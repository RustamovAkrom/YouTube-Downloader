# 🎬 YouTube Downloader (на Python + yt-dlp)

Надёжный инструмент для скачивания **видео, аудио, плейлистов и субтитров** с YouTube и других платформ.  
Проект построен на [yt-dlp](https://github.com/yt-dlp/yt-dlp) — это современная и улучшенная версия youtube-dl.  
Поддерживает работу с плейлистами, выбор качества, конвертацию через FFmpeg и встроенные субтитры.

---

## 🚀 Возможности

- Скачивание **видео** в лучшем качестве (автоматический выбор `bestvideo+bestaudio`).
- Скачивание **аудио** дорожек в форматах `m4a` или `mp3`.
- Работа с **плейлистами** (сохранение порядка).
- Поддержка **субтитров** (включая автоматические).
- **FFmpeg-постобработка** (конвертация и mux видео/аудио).
- Ограничение скорости скачивания (`--rate-limit`).
- Надёжная обработка ошибок, возобновление загрузок.

---

## ⚙️ Установка

### 1. Клонировать проект
```bash
git clone https://github.com/RustamovAkrom/YouTube-Downloader.git
cd YouTube-Downloader
````

### 2. Создать виртуальное окружение (опционально)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
```

Если PowerShell ругается на `ExecutionPolicy`, исправь так:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

Файл `requirements.txt`:

```txt
yt-dlp>=2025.1.15
```

### 4. Установить FFmpeg

FFmpeg нужен для объединения видео/аудио и извлечения звука.

* **Windows (через winget):**

  ```powershell
  winget install --id Gyan.FFmpeg -e
  ```
* **Linux (Debian/Ubuntu):**

  ```bash
  sudo apt update
  sudo apt install ffmpeg
  ```
* **MacOS (через brew):**

  ```bash
  brew install ffmpeg
  ```

Проверить установку:

```bash
ffmpeg -version
```

---

## ▶️ Использование

### Видео

```bash
python ytdown.py --url "https://www.youtube.com/watch?v=XXXX" --type video --quality 1080 --container mp4
```

### Аудио

```bash
python ytdown.py --url "https://www.youtube.com/watch?v=XXXX" --type audio --audio-format mp3
```

### Плейлист

```bash
python ytdown.py --url "https://www.youtube.com/playlist?list=XXXX" --type playlist --quality 720
```

### Субтитры

```bash
python ytdown.py --url "https://www.youtube.com/watch?v=XXXX" --type subs --subs-langs "en,ru,auto"
```

---

## ⚠️ Возможные ошибки и решения

* **`cannot be loaded because running scripts is disabled`**
  Нужно разрешить запуск скриптов:

  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

* **`ffmpeg not found`**
  Установи FFmpeg и добавь его в `PATH`.

* **`ERROR: Unable to extract video data`**
  Версия `yt-dlp` устарела. Обнови:

  ```bash
  pip install -U yt-dlp
  ```

* **Скачивание слишком медленное**
  Добавь `--concurrent-fragments 4` или убери `--rate-limit`.

---

## 📚 Полезные ссылки

* Официальный репозиторий yt-dlp: [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
* Документация по форматам: [https://github.com/yt-dlp/yt-dlp#format-selection](https://github.com/yt-dlp/yt-dlp#format-selection)
* FFmpeg: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

---

## 📝 Лицензия

Этот проект создан для **личного использования** (скачивание разрешённого контента, оффлайн-доступ к своим файлам).
Уважайте авторские права и условия YouTube.
