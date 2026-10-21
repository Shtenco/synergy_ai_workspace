# SYNERGY AI WORKSPACE V0.9 — Windows release gate

## Что добавлено
- Windows Actions workflow для **реальной** сборки NSIS из исходников.
- Импорт трех оригинальных upstream репозиториев при запуске workflow.
- Fail-closed проверка шести SMM кабинетов, всех копируемых файлов, SHA-256 и Git commit provenance.
- 25+ локальных тестов сервера/HTTP; внешняя отправка не разрешена.

## Запуск в GitHub
1. Разместите **все файлы текущей папки** в отдельном репозитории `Shtenco/synergy_ai_workspace` (либо в отдельной ветке существующего репозитория), не удаляя исходные upstream репозитории.
2. Actions → `SYNERGY Windows Build V0.9` → Run workflow.
3. Если обязательные кабинеты отсутствуют, сборка остановится, а не выдаст ложный релиз.
4. После прохождения workflow получите NSIS `.exe` во вкладке Artifacts.

## Известные ограничения
- GitHub Actions **не запускался** в этой сессии: проект еще не опубликован в отдельном репозитории.
- Rust/Tauri сборка и desktop GUI E2E не проверены здесь.
- OAuth credentials не добавлены. Реальные Avito/VK/Telegram отправки отключены.
- Оригинальные SMM и AUTOPILOT исходники подтягиваются только во время import. Архив не содержит их копий.
- Для production необходимо закрепить commit SHA upstream и получить подтверждённую подпись Windows дистрибутива.
