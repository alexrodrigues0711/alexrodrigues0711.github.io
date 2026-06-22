"""API do dashboard Market Intel Bancário."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.bcb_client import (
    fetch_bank_snapshot,
    fetch_latest_available_period,
    fetch_metric,
    normalize_quarterly_lucro,
    period_label,
    quarter_periods_up_to,
)
from backend.config import BANKS, COL_LUCRO, HISTORY_START

STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Market Intel Bancário",
    description="Dashboard com dados públicos do BCB (IF.data)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/meta")
async def meta() -> dict:
    period = await fetch_latest_available_period()
    return {
        "period": period,
        "periodLabel": period_label(period),
        "source": "Banco Central do Brasil — IF.data (OData)",
        "scope": "Conglomerado prudencial (TipoInstituicao=1)",
        "supportedMetrics": ["lucro", "roe", "basileia", "historicoLucro"],
        "lucroNote": "Lucro trimestral isolado; 2T e 4T do IF.data são acumulados semestrais e são normalizados automaticamente",
        "unsupportedMetrics": {
            "clientes": "Sem série pública comparável por API",
            "inadimplencia": "Relatórios de crédito descontinuados/instáveis no IF.data",
            "reclameAqui": "Sem API oficial",
            "appRating": "Requer API das lojas (não incluído no MVP)",
        },
        "banks": [cfg["name"] for cfg in BANKS.values()],
    }


@app.get("/api/banks/current")
async def banks_current(period: int | None = None) -> dict:
    target_period = period or await fetch_latest_available_period()
    snapshots = await asyncio.gather(
        *[
            fetch_bank_snapshot(target_period, key, cfg)
            for key, cfg in BANKS.items()
        ]
    )
    return {
        "period": target_period,
        "periodLabel": period_label(target_period),
        "banks": snapshots,
    }


@app.get("/api/banks/history")
async def banks_history(metric: str = "lucro") -> dict:
    if metric != "lucro":
        raise HTTPException(status_code=400, detail="Métrica não suportada no MVP")

    periods = quarter_periods_up_to(await fetch_latest_available_period(), HISTORY_START)

    async def series_for_bank(bank_key: str, bank_cfg: dict) -> dict:
        raw_by_period: dict[int, float] = {}
        for period in periods:
            raw = await fetch_metric(period, bank_cfg["cod_inst"], COL_LUCRO)
            if raw is not None:
                raw_by_period[period] = raw

        values: dict[str, float | None] = {}
        for period in periods:
            label = period_label(period)
            raw = raw_by_period.get(period)
            if raw is None:
                values[label] = None
            else:
                quarterly = normalize_quarterly_lucro(period, raw, raw_by_period)
                values[label] = round(quarterly / 1e9, 2)
        return {"id": bank_key, "name": bank_cfg["name"], "color": bank_cfg["color"], "values": values}

    series = await asyncio.gather(
        *[series_for_bank(key, cfg) for key, cfg in BANKS.items()]
    )

    history_rows = []
    for period in periods:
        label = period_label(period)
        row: dict = {"period": label}
        for bank in series:
            row[bank["name"]] = bank["values"].get(label)
        history_rows.append(row)

    return {"metric": metric, "unit": "R$ Bi", "history": history_rows, "series": series}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
