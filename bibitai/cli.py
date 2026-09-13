from __future__ import annotations

import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

from bibitai.backtest import run_backtest
from bibitai.binance_client import BinanceClient, BinanceError
from bibitai.config import load_config
from bibitai.engine import BotEngine
from bibitai.markets import ranging_sine_candles, trending_down_candles
from bibitai.paper import PaperBroker
from bibitai.statefile import load_paper, save_paper


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bibitai",
        description="Conservative Binance spot bot: adaptive range grid, paper-first.",
    )
    parser.add_argument("--config", help="Path to YAML config")
    sub = parser.add_subparsers(dest="command", required=True)

    backtest = sub.add_parser("backtest", help="Replay candles through the strategy")
    backtest.add_argument("--demo", action="store_true", help="Built-in ranging and trend scenarios")
    backtest.add_argument("--fetch", action="store_true", help="Fetch public Binance klines")
    backtest.add_argument("--limit", type=int, default=500)

    paper = sub.add_parser("paper", help="Live public prices, simulated orders")
    paper.add_argument("--once", action="store_true", help="Single tick then exit")

    sub.add_parser("doctor", help="Check public Binance connectivity")

    args = parser.parse_args(argv)
    config = load_config(args.config)

    try:
        if args.command == "doctor":
            client = BinanceClient()
            client.ping()
            price = client.get_price(config.symbol)
            print(f"ok {config.symbol} last={price}")
            return 0

        if args.command == "backtest":
            return _backtest(args, config)

        if args.command == "paper":
            return _paper(args, config)
    except BinanceError as exc:
        print(exc, file=sys.stderr)
        return 2

    return 1


def _backtest(args: argparse.Namespace, config) -> int:
    if args.fetch:
        client = BinanceClient()
        candles = client.get_klines(config.symbol, config.interval, limit=args.limit)
        report = run_backtest(candles, config=config)
        _print_report("fetched", report)
        return 0

    ranging = run_backtest(
        ranging_sine_candles(Decimal("100000"), 240, Decimal("2500")),
        config=config,
    )
    trend = run_backtest(
        trending_down_candles(Decimal("100000"), 180, Decimal("15000")),
        config=config,
    )
    _print_report("ranging-sine", ranging)
    _print_report("trending-down", trend)
    if not args.demo and not args.fetch:
        # default is demo scenarios
        pass
    return 0


def _print_report(name: str, report) -> None:
    payload = {
        "scenario": name,
        "ending_equity": str(report.ending_equity),
        "ending_price": str(report.ending_price),
        "trade_count": report.trade_count,
        "max_drawdown_pct": str(report.max_drawdown_pct),
        "max_base": str(report.max_base),
        "killed": report.killed,
        "ending_quote": str(report.ending_quote),
        "ending_base": str(report.ending_base),
        "notes": report.notes,
    }
    print(json.dumps(payload, indent=2))


def _paper(args: argparse.Namespace, config) -> int:
    client = BinanceClient()
    broker = PaperBroker(quote=config.paper.quote, base=config.paper.base, fee=config.strategy.maker_fee)
    engine = BotEngine(broker=broker, config=config)
    state_path = Path(config.runtime.state_dir) / "paper-state.json"
    load_paper(state_path, engine)

    def tick() -> None:
        candles = client.get_klines(config.symbol, config.interval, limit=200)
        price = client.get_price(config.symbol)
        snapshot = engine.on_candles(candles, last=price)
        save_paper(state_path, engine)
        print(
            json.dumps(
                {
                    "price": str(price),
                    "regime": None if snapshot.regime is None else snapshot.regime.value,
                    "decision": None if snapshot.decision is None else snapshot.decision.value,
                    "equity": str(broker.equity(price)),
                    "base": str(broker.base),
                    "quote": str(broker.quote),
                    "open_orders": len(broker.open_orders()),
                    "fills": len(snapshot.fills),
                    "stopped": snapshot.stopped,
                }
            )
        )

    tick()
    if args.once:
        return 0
    while True:
        time.sleep(config.runtime.poll_seconds)
        tick()


if __name__ == "__main__":
    sys.exit(main())
