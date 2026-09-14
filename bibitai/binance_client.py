from __future__ import annotations

import hashlib
import hmac
import os
import time
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import httpx

from bibitai.models import Candle


MAINNET = "https://api.binance.com"
TESTNET = "https://testnet.binance.vision"


class BinanceError(RuntimeError):
    pass


class BinanceClient:
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
        timeout: float = 15.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("BINANCE_API_SECRET", "")
        self.base_url = TESTNET if testnet else MAINNET
        self.timeout = timeout

    def get_klines(self, symbol: str, interval: str, limit: int = 200) -> list[Candle]:
        payload = self._public("GET", "/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
        candles: list[Candle] = []
        for row in payload:
            candles.append(
                Candle(
                    open_time=int(row[0]),
                    open=Decimal(str(row[1])),
                    high=Decimal(str(row[2])),
                    low=Decimal(str(row[3])),
                    close=Decimal(str(row[4])),
                    volume=Decimal(str(row[5])),
                )
            )
        return candles

    def get_price(self, symbol: str) -> Decimal:
        payload = self._public("GET", "/api/v3/ticker/price", {"symbol": symbol})
        return Decimal(str(payload["price"]))

    def ping(self) -> None:
        self._public("GET", "/api/v3/ping", {})

    def _public(self, method: str, path: str, params: dict[str, Any]) -> Any:
        return self._request(method, path, params, signed=False)

    def _request(self, method: str, path: str, params: dict[str, Any], signed: bool) -> Any:
        headers = {}
        query = dict(params)
        if signed:
            if not self.api_key or not self.api_secret:
                raise BinanceError("BINANCE_API_KEY and BINANCE_API_SECRET are required")
            query["timestamp"] = int(time.time() * 1000)
            query["recvWindow"] = 5000
            encoded = urlencode(query, doseq=True)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                encoded.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            query["signature"] = signature
            headers["X-MBX-APIKEY"] = self.api_key
        elif self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key

        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, url, params=query, headers=headers)
        if response.status_code == 451:
            raise BinanceError(
                "Binance blocked this IP (HTTP 451). Paper/doctor need a location Binance allows; backtest --demo works offline."
            )
        if response.status_code >= 400:
            raise BinanceError(f"Binance {response.status_code}: {response.text}")
        if not response.content:
            return {}
        return response.json()
