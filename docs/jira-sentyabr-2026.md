# Тикеты за сентябрь 2026

Исходный фильтр брал две группы:

1. Созданные в сентябре.
2. Созданные раньше сентября и **сейчас** не в Released / Rejected / Done / Idea / Backlog.

Из-за этого пропадали тикеты, которые **сделаны не в сентябре**, но **статус сменили в сентябре** — например, августовская задача, которую в сентябре закрыли в Done или Released. Вторая ветка их отсекала условием `status != Done` / `status != Released`.

## Что теперь попадает

1. Созданные в сентябре (любой текущий статус).
2. Созданные раньше сентября и всё ещё в работе (не Released, Rejected, Done, Idea, Backlog).
3. **Любые тикеты, у которых статус менялся в сентябре** — в том числе уже закрытые.

## JQL

```
(reporter = stavyshenko.anton OR assignee = stavyshenko.anton) AND ((created >= "2026-09-01" AND created < "2026-10-01") OR (created < "2026-09-01" AND status != Released AND status != Rejected AND status != Done AND status != Idea AND status != Backlog) OR status CHANGED DURING ("2026-09-01", "2026-09-30")) ORDER BY project ASC, updated DESC
```

Добавлена третья ветка:

```
status CHANGED DURING ("2026-09-01", "2026-09-30")
```

Это история смены статуса, а не поле `updated`. Комментарий или правка описания без смены статуса сюда не попадёт. Даты в `DURING` включительные: с 1 по 30 сентября.

## Тот же фильтр на текущий месяц

Чтобы не править даты каждый месяц:

```
(reporter = stavyshenko.anton OR assignee = stavyshenko.anton) AND ((created >= startOfMonth() AND created < startOfMonth(1)) OR (created < startOfMonth() AND status != Released AND status != Rejected AND status != Done AND status != Idea AND status != Backlog) OR status CHANGED DURING (startOfMonth(), endOfMonth())) ORDER BY project ASC, updated DESC
```
