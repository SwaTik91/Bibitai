# Bibitai

Консервативный спотовый бот для Binance: адаптивная сетка в диапазоне, пауза в тренде, жёсткие стопы. По умолчанию торгует **на бумаге**.

Это не финансовый совет. Стратегию и архитектуру я выбрал сам: сначала сохранить счёт и получить проверяемое поведение, а не гнаться за доходностью.

Подробности: [docs/strategy.md](docs/strategy.md).

## Что делает бот

- Смотрит часовые свечи BTCUSDT
- Отличает боковик от тренда по EMA и ATR
- В боковике ставит сетку лимиток
- В тренде не докупает и сводит инвентарь
- Останавливается при дневном убытке 2% или просадке 6%

## Команды

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp config.example.yaml config.yaml

bibitai backtest --demo
bibitai doctor
bibitai paper --once
```

`paper` берёт публичные цены Binance и исполняет ордера локально. Состояние пишется в `data/paper-state.json`.

Если `doctor` или `paper` отвечают HTTP 451, IP заблокирован правилами Binance. `backtest --demo` работает офлайн.

Ключи биржи для paper не нужны. Если будете подключать live позже — только Spot, без withdraw, с IP whitelist. Файл `.env` не коммитить.

## Тесты

```bash
pytest
```
