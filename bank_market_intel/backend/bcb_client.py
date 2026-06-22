"""Cliente para a API OData IF.data do Banco Central."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import httpx

from backend.config import (
    BCB_IFDATA_BASE,
    COL_BASILEIA,
    COL_LUCRO,
    COL_PL,
    HISTORY_START,
    REPORT_RESUMO,
)

CACHE_TTL_SECONDS = 3600
_cache: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if time.time() > expires_at:
        del _cache[key]
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.time() + CACHE_TTL_SECONDS, value)


async def _fetch_rows(path: str) -> list[dict[str, Any]]:
    cache_key = path
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"{BCB_IFDATA_BASE}/{path}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url, headers={"User-Agent": "bank-market-intel/1.0"})
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("value", [])
    _cache_set(cache_key, rows)
    return rows


def _filter_expr(*parts: str) -> str:
    return quote(" and ".join(parts), safe="")


async def fetch_metric(period: int, cod_inst: str, column: str) -> float | None:
    """Busca um valor numérico do relatório Resumo para um conglomerado."""
    filt = _filter_expr(f"CodInst eq '{cod_inst}'", f"NomeColuna eq '{column}'")
    path = (
        f"IfDataValores(AnoMes={period},TipoInstituicao=1,Relatorio='{REPORT_RESUMO}')"
        f"?$filter={filt}&$format=json"
    )
    rows = await _fetch_rows(path)
    if not rows:
        return None
    value = rows[0].get("Saldo")
    return float(value) if value is not None else None


async def fetch_bank_snapshot(period: int, bank_key: str, bank_cfg: dict[str, str]) -> dict[str, Any]:
    cod_inst = bank_cfg["cod_inst"]

    periods_to_fetch = {period}
    month = period % 100
    year = period // 100
    if month == 6:
        periods_to_fetch.add(year * 100 + 3)
    elif month == 12:
        periods_to_fetch.add(year * 100 + 9)

    raw_by_period: dict[int, float] = {}
    for p in periods_to_fetch:
        val = await fetch_metric(p, cod_inst, COL_LUCRO)
        if val is not None:
            raw_by_period[p] = val

    raw_lucro = raw_by_period.get(period)
    lucro = None
    if raw_lucro is not None:
        lucro = round(normalize_quarterly_lucro(period, raw_lucro, raw_by_period) / 1e9, 2)

    basileia = await fetch_metric(period, cod_inst, COL_BASILEIA)
    pl = await fetch_metric(period, cod_inst, COL_PL)

    roe = None
    if lucro is not None and pl and pl > 0:
        # lucro já em bilhões; PL em reais — reconverte lucro para reais no numerador
        lucro_reais = lucro * 1e9
        roe = round((lucro_reais / pl) * 100 * 4, 2)

    return {
        "id": bank_key,
        "name": bank_cfg["name"],
        "color": bank_cfg["color"],
        "period": period,
        "lucro": lucro,
        "roe": roe,
        "basileia": round(basileia * 100, 2) if basileia is not None else None,
        "source": "BCB IF.data (conglomerado prudencial, relatório Resumo)",
    }


def quarter_periods_up_to(latest: int, start: int = HISTORY_START) -> list[int]:
    """Gera trimestres YYYYMM entre start e latest (mar/jun/set/dez)."""
    periods: list[int] = []
    start_year, end_year = start // 100, latest // 100
    for year in range(start_year, end_year + 1):
        for month in (3, 6, 9, 12):
            period = year * 100 + month
            if start <= period <= latest:
                periods.append(period)
    return periods


async def fetch_latest_available_period() -> int:
    """Descobre o trimestre mais recente com dados no IF.data."""
    from backend.config import BANKS, HISTORY_START

    itau_cod = BANKS["itau"]["cod_inst"]
    now = __import__("datetime").date.today()
    # Testa do trimestre corrente para trás (~3 anos)
    candidates: list[int] = []
    for year in range(now.year, now.year - 4, -1):
        for month in (12, 9, 6, 3):
            period = year * 100 + month
            if period >= HISTORY_START:
                candidates.append(period)

    for period in candidates:
        lucro = await fetch_metric(period, itau_cod, COL_LUCRO)
        if lucro is not None:
            return period
    return HISTORY_START


def period_label(period: int) -> str:
    year = period // 100
    quarter = (period % 100) // 3
    return f"{quarter}T{str(year)[2:]}"


def normalize_quarterly_lucro(period: int, raw_lucro: float, period_map: dict[int, float]) -> float:
    """Converte lucro do IF.data para trimestre isolado (2T/4T vêm acumulados semestrais)."""
    month = period % 100
    year = period // 100

    if month == 6:
        prev = period_map.get(year * 100 + 3)
        if prev is not None:
            return raw_lucro - prev
    elif month == 12:
        prev = period_map.get(year * 100 + 9)
        if prev is not None:
            return raw_lucro - prev

    return raw_lucro
