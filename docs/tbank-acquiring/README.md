# Эквайринг Т‑Банка

**[Итого — читать сначала](ITOGO.md)**

Разбор ответа `Status=AUTHORIZED` по заказу `49332682` на 900 ₽: деньги на карте заморожены, списания ещё нет.

- [authorized.md](authorized.md) — статусы, Confirm / Cancel, как не перепутать с оплатой в 1С
- [payment-9167107039.json](payment-9167107039.json) — нормализованный дамп
- `python3 parse_payment.py dump.txt` — разбор текста из отладчика
