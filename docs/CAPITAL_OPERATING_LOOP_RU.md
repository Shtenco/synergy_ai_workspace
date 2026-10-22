# SYNERGY FINANCIAL OPERATING LOOP — локальный исполняемый прототип (V0.1)

## Суть
Реальный Python-контур в ветке `release/v1.0-desktop-rc` соединяет **задания Workspace**, **реестр разрешённых инструментов META-API-формата**, **локальную финансовую книгу**, **расчёт дельты** и **черновик распределения капитала**. 

Это **не** подключение к реальному банковскому счёту, **не** самостоятельный AI-инвестор и **не** публичный защищённый multi-tenant backend. Прямой вызов опубликованной GitHub Pages страницы не подключён к локальному серверу и не должен принимать токены. Никаких автоматических платежей, заказов, массовых рассылок или трейдинга.

## Контракт финансовых данных
`POST /v1/capital/import` — защищённый существующим локальным Bearer-токеном импорт записей с `source_id`, ISO-кодом валюты, диапазоном дат и уникальным `entry_id`. Суммы положительные, decimal string, максимум 2 знака после запятой. `kind` = `income`, `expense`, `transfer`, `investment`, `refund`.

Источник и все операции хэшируются SHA-256. Повтор того же источника с теми же данными возвращает `duplicate_ignored`; попытка изменить данные при том же `source_id` отклоняется. Это проверка целостности импорта, а **не банковская аттестация**. Перекрывающиеся источники по разным идентификаторам и одинаковые операции между банками ещё требуют межисточниковой сверки.

`GET /v1/capital/summary?currency=KZT&start=2026-10-01&end=2026-10-31` — агрегирует `income - expense`, отдельно показывает переводы, инвестиции и возвраты. **Переводы и инвестиции не являются операционной выручкой или расходами**. Разные валюты не конвертируются автоматически. Данные исходника имеют статус `SOURCE_SUPPLIED_UNVERIFIED`, `verified_by_bank:false`.

`POST /v1/capital/allocate/plan` — формирует черновик с `currency`, `start`, `end`, `reserve_pct`, `investment_pct`, опциональным `minimum_buffer`. **Никаких переводов средств и торговых ордеров**; только SQLite запись `draft_unapproved` и аудит.

Пример:

```json
{
  "source_id": "example-2026-10",
  "currency": "KZT",
  "period_start": "2026-10-01",
  "period_end": "2026-10-31",
  "entries": [
    {"entry_id": "salary-1", "date": "2026-10-04", "kind": "income", "amount": "500000.00"},
    {"entry_id": "rent-1", "date": "2026-10-06", "kind": "expense", "amount": "300000.00"}
  ]
}
```

## Оркестрация META-API-формата

`GET /v1/orchestration/capabilities` — локальный catalog с `capability_id` и политиками. `POST /v1/orchestration/run` — предварительно проверяет **всю** последовательность, затем может исполнить только:
- `workspace.tasks.list` — чтение существующего реестра заданий;
- `workspace.capital.summary` — расчёт на локальной книге;
- `workspace.capital.allocate.plan` — локальное создание финансового черновика.

`external.avito.publish`, `external.investment.trade`, произвольные команды, URL и внешние API — **запрещены**. Вызовы не требуют и не используют внешних credentials. Журнал содержит receipt-hash и число завершённых шагов.

Важно: это **совместимый по концепции внутренний registry**, а не сетевой мост к `Shtenco/synergy_meta_api`. У проекта META-API собственный прототип в ветке `integration/meta-api-mcp-v0.1`: ограниченный read-only MCP, OpenAPI discovery и allowlist GET. Для производственного объединения необходимы подписанная авторизация, tenant isolation, MFA, межсервисные идентификаторы, сетевой канал и честные E2E.

## Где AI CFO
Сегодня `Shtenco/synergy.github.io/cfo/app.js` обращается к приватному `/api/v3/cfo/parse` для разбора выписки, а не напрямую к SQLite Workspace. Безопасный маршрут интеграции должен быть **сервер-сервер**:

`CFO bank import → operator review → signed normalized ledger batch → Workspace import → summary → RiskGuard approval → Investor Folio projection`.

Этот перевод данных между CFO и Workspace **ещё не подключён**, а реальная `bank-verified` отметка появится только после проверки оригинала и подписанного доказательства от надёжного источника. Нельзя принимать её со стороны браузера.

## Запуск и проверки
На машине владельца с установленными исходниками:
```bash
python -m unittest -v tests.test_capital_engine tests.test_meta_orchestrator
python -m workspace.service
```
Сервер слушает **только** `127.0.0.1:8129`, требует локальный секрет `SYNERGY_TOKEN`; не пробрасывать напрямую в интернет. Текущие auth/CORS модели пригодны для локального desktop-клиента, не заменяют OIDC/tenant/RBAC production.

CI: workflow `capital-core-tests.yml` запускает тесты на GitHub push ветки `release/v1.0-desktop-rc`; фактический результат следует проверять в Actions.

## AI CFO → защищённый Workspace: практический импорт

1. Откройте `https://shtenco.github.io/synergy.github.io/cfo/`.
2. В приватном AI CFO выполните анализ выписки и **вручную проверьте** операции на шаге «Проверка». На дашборде заполните трёхбуквенную валюту и **постоянный идентификатор источника**, например `bank-main-2026-10`, и сохраните JSON.
3. На своём компьютере запустите Workspace (`python -m workspace.service`) и используйте тот же локальный токен, что и у оператора.
4. Выполните `python scripts/import_cfo_batch.py synergy-cfo-bank-main-2026-10.json`.
5. Сервис покажет количество импортированных строк, SHA-256 или `duplicate_ignored`. Только затем формируйте финансовую сводку и черновик распределения.

Не отправляйте `SYNERGY_TOKEN` в браузер GitHub Pages и не загружайте конфиденциальные выписки в публичные репозитории. Браузерный пакет имеет `operator_reviewed:true`, `verified_by_bank:false` — эта пометка **не является доказательством банковской подлинности**.

Команда только импортирует данные в локальную SQLite-базу; никакой перевод средств не выполняется.
