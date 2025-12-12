Создайте и активируйте виртуальное окружение (пример для bash, используйте `python3`):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Установка зависимостей: `python3 -m pip install -r requirements.txt` (убедитесь, что активировано нужное venv).

Модель: `base` (многоязычная, лучше качество, медленнее `tiny`), язык фиксированный (`LANGUAGE` в `app/stt.py`, по умолчанию "en").

Запуск сервера (без hot-reload для стабильности):
```bash
cd project
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app
```

Проверка: откройте в браузере `http://localhost:8000/` — там минимальная страница для записи микрофона и отправки чанков в WebSocket.

Пример использования WebSocket через JavaScript:
```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
  const recorder = new MediaRecorder(stream);
  recorder.ondataavailable = e => ws.send(e.data);
  ws.onmessage = ev => console.log(JSON.parse(ev.data));
  recorder.start(250);
});
```
