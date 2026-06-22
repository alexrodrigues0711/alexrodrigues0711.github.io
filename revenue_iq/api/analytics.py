from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = {
    "date",
    "order_id",
    "region",
    "channel",
    "segment",
    "product",
    "customer",
    "units",
    "revenue",
    "cost",
    "gross_profit",
    "margin",
    "target_revenue",
}

SEGMENT_MAP = {
    "all": None,
    "enterprise": "Enterprise",
    "mid": "Mid-market",
    "smb": "SMB",
}
REGION_MAP = {
    "brasil": None,
    "sudeste": "Sudeste",
    "sul": "Sul",
    "nordeste": "Nordeste",
    "centro": "Centro-Oeste",
}


@dataclass(frozen=True)
class Filters:
    segment: str = "all"
    region: str = "brasil"
    period: str = "12"

    def normalized(self) -> "Filters":
        segment = self.segment if self.segment in SEGMENT_MAP else "all"
        region = self.region if self.region in REGION_MAP else "brasil"
        period = self.period if self.period in {"6", "12", "ytd"} else "12"
        return Filters(segment=segment, region=region, period=period)


def load_data(path: str | Path) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["date"])
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"CSV sem colunas obrigatórias: {sorted(missing)}")
    if data[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("CSV contém valores ausentes em colunas obrigatórias")

    data = data.copy()
    data["month"] = data["date"].dt.to_period("M")
    return data


def _period_bounds(data: pd.DataFrame, period: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    max_date = data["date"].max().normalize()
    max_month = max_date.to_period("M")
    if period == "ytd":
        start = pd.Timestamp(year=max_date.year, month=1, day=1)
    else:
        months = int(period)
        start = (max_month - (months - 1)).start_time
    return start, max_month.end_time.normalize()


def apply_filters(data: pd.DataFrame, filters: Filters) -> pd.DataFrame:
    filters = filters.normalized()
    start, end = _period_bounds(data, filters.period)
    mask = data["date"].between(start, end)

    segment = SEGMENT_MAP[filters.segment]
    region = REGION_MAP[filters.region]
    if segment:
        mask &= data["segment"].eq(segment)
    if region:
        mask &= data["region"].eq(region)
    return data.loc[mask].copy()


def _previous_period(data: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    start = current["date"].min().to_period("M").start_time
    end = current["date"].max().to_period("M").end_time
    month_count = (end.to_period("M") - start.to_period("M")).n + 1
    previous_end = (start.to_period("M") - 1).end_time
    previous_start = (previous_end.to_period("M") - (month_count - 1)).start_time
    return data[data["date"].between(previous_start, previous_end)].copy()


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current / previous - 1) * 100


def _breakdown(frame: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    grouped = frame.groupby(column, as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    total = grouped["revenue"].sum()
    return [
        {
            "name": row[column],
            "revenue": round(float(row["revenue"]), 2),
            "share": round(float(row["revenue"] / total * 100), 1) if total else 0.0,
        }
        for _, row in grouped.iterrows()
    ]


def _product_metrics(current: pd.DataFrame, previous: pd.DataFrame) -> list[dict[str, Any]]:
    current_group = current.groupby("product").agg(
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
    )
    previous_group = previous.groupby("product").agg(
        previous_revenue=("revenue", "sum"),
        previous_gross_profit=("gross_profit", "sum"),
    )
    merged = current_group.join(previous_group, how="left").fillna(0)
    merged["margin"] = merged["gross_profit"].div(merged["revenue"]).fillna(0)
    merged["previous_margin"] = merged["previous_gross_profit"].div(merged["previous_revenue"]).fillna(0)
    merged["growth"] = [
        _pct_change(float(row.revenue), float(row.previous_revenue))
        for row in merged.itertuples()
    ]
    merged["margin_delta_pp"] = (merged["margin"] - merged["previous_margin"]) * 100
    merged = merged.sort_values("revenue", ascending=False)
    return [
        {
            "name": index,
            "revenue": round(float(row["revenue"]), 2),
            "growth": round(float(row["growth"]), 1),
            "margin": round(float(row["margin"] * 100), 1),
            "margin_delta_pp": round(float(row["margin_delta_pp"]), 1),
        }
        for index, row in merged.iterrows()
    ]


def _monthly_metrics(frame: pd.DataFrame) -> list[dict[str, Any]]:
    grouped = frame.groupby("month").agg(
        revenue=("revenue", "sum"),
        target=("target_revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
    ).reset_index()
    return [
        {
            "month": str(row["month"]),
            "revenue": round(float(row["revenue"]), 2),
            "target": round(float(row["target"]), 2),
            "margin": round(float(row["gross_profit"] / row["revenue"] * 100), 1),
        }
        for _, row in grouped.iterrows()
    ]


def dashboard_snapshot(data: pd.DataFrame, filters: Filters) -> dict[str, Any]:
    filters = filters.normalized()
    current = apply_filters(data, filters)
    if current.empty:
        raise ValueError("Nenhum dado encontrado para os filtros selecionados")

    filtered_unbounded = data.copy()
    segment = SEGMENT_MAP[filters.segment]
    region = REGION_MAP[filters.region]
    if segment:
        filtered_unbounded = filtered_unbounded[filtered_unbounded["segment"].eq(segment)]
    if region:
        filtered_unbounded = filtered_unbounded[filtered_unbounded["region"].eq(region)]
    previous = _previous_period(filtered_unbounded, current)

    revenue = float(current["revenue"].sum())
    gross_profit = float(current["gross_profit"].sum())
    target = float(current["target_revenue"].sum())
    previous_revenue = float(previous["revenue"].sum())
    monthly = _monthly_metrics(current)
    monthly_growth = _pct_change(monthly[-1]["revenue"], monthly[-2]["revenue"]) if len(monthly) > 1 else 0.0

    customer_revenue = current.groupby("customer")["revenue"].sum().sort_values(ascending=False)
    top_five_revenue = float(customer_revenue.head(5).sum())

    return {
        "filters": {
            "segment": filters.segment,
            "region": filters.region,
            "period": filters.period,
        },
        "kpis": {
            "revenue": round(revenue, 2),
            "revenue_growth": round(_pct_change(revenue, previous_revenue), 1),
            "gross_margin": round(gross_profit / revenue * 100, 1),
            "target_attainment": round(revenue / target * 100, 1),
            "target_gap": round(revenue - target, 2),
            "monthly_growth": round(monthly_growth, 1),
        },
        "monthly": monthly,
        "regions": _breakdown(current, "region"),
        "channels": _breakdown(current, "channel"),
        "products": _product_metrics(current, previous),
        "concentration": {
            "top_five_share": round(top_five_revenue / revenue * 100, 1),
            "top_customer": str(customer_revenue.index[0]),
            "top_customer_share": round(float(customer_revenue.iloc[0] / revenue * 100), 1),
        },
    }


def _month_comparison(data: pd.DataFrame, month: str) -> dict[str, Any] | None:
    target_period = pd.Period(month, freq="M")
    previous_period = target_period - 1
    current = data[data["month"].eq(target_period)]
    previous = data[data["month"].eq(previous_period)]
    if current.empty or previous.empty:
        return None

    current_revenue = float(current["revenue"].sum())
    previous_revenue = float(previous["revenue"].sum())

    def largest_drop(column: str) -> tuple[str, float]:
        current_values = current.groupby(column)["revenue"].sum()
        previous_values = previous.groupby(column)["revenue"].sum()
        delta = current_values.sub(previous_values, fill_value=0).sort_values()
        return str(delta.index[0]), float(delta.iloc[0])

    region, region_delta = largest_drop("region")
    product, product_delta = largest_drop("product")
    return {
        "current_revenue": current_revenue,
        "previous_revenue": previous_revenue,
        "change_pct": _pct_change(current_revenue, previous_revenue),
        "region": region,
        "region_delta": region_delta,
        "product": product,
        "product_delta": product_delta,
    }


def evidence_catalog(data: pd.DataFrame, snapshot: dict[str, Any]) -> dict[str, dict[str, str]]:
    evidence_data = data.copy()
    selected_segment = SEGMENT_MAP[snapshot["filters"]["segment"]]
    selected_region = REGION_MAP[snapshot["filters"]["region"]]
    if selected_segment:
        evidence_data = evidence_data[evidence_data["segment"].eq(selected_segment)]
    if selected_region:
        evidence_data = evidence_data[evidence_data["region"].eq(selected_region)]
    march = _month_comparison(evidence_data, "2025-03")
    regions = snapshot["regions"]
    products = snapshot["products"]
    concentration = snapshot["concentration"]
    margin_pressure = sorted(products, key=lambda item: item["margin_delta_pp"])[0]
    evidence: dict[str, dict[str, str]] = {
        "KPI_REVENUE": {
            "type": "DADO",
            "text": f"Receita no período: R$ {snapshot['kpis']['revenue']:,.0f}",
        },
        "KPI_MARGIN": {
            "type": "DADO",
            "text": f"Margem bruta: {snapshot['kpis']['gross_margin']:.1f}%",
        },
        "TOP_REGION": {
            "type": "DADO",
            "text": f"{regions[0]['name']} lidera com {regions[0]['share']:.1f}% da receita",
        },
        "TOP_PRODUCT": {
            "type": "DADO",
            "text": f"{products[0]['name']} é o maior produto, com R$ {products[0]['revenue']:,.0f}",
        },
        "MARGIN_PRESSURE": {
            "type": "INSIGHT",
            "text": f"{margin_pressure['name']} teve variação de margem de {margin_pressure['margin_delta_pp']:.1f} pp",
        },
        "CONCENTRATION": {
            "type": "RISCO",
            "text": f"Top 5 clientes representam {concentration['top_five_share']:.1f}% da receita",
        },
    }
    if march:
        evidence.update({
            "MARCH_CHANGE": {
                "type": "DADO",
                "text": f"Receita de março variou {march['change_pct']:.1f}% frente a fevereiro",
            },
            "MARCH_REGION": {
                "type": "DADO",
                "text": f"{march['region']} teve a maior redução regional: R$ {march['region_delta']:,.0f}",
            },
            "MARCH_PRODUCT": {
                "type": "DADO",
                "text": f"{march['product']} teve a maior redução por produto: R$ {march['product_delta']:,.0f}",
            },
        })
    return evidence


def demo_analysis(question: str, data: pd.DataFrame, snapshot: dict[str, Any]) -> dict[str, Any]:
    catalog = evidence_catalog(data, snapshot)
    normalized = question.casefold()

    if "março" in normalized or "marco" in normalized or "caiu" in normalized:
        ids = ["MARCH_CHANGE", "MARCH_REGION", "MARCH_PRODUCT"]
        answer = (
            "A queda de março foi concentrada em uma região e em um produto específicos. "
            "Os dados abaixo mostram os principais componentes da variação frente a fevereiro."
        )
    elif "margem" in normalized:
        ids = ["KPI_MARGIN", "MARGIN_PRESSURE", "TOP_PRODUCT"]
        answer = (
            "A margem agregada permanece positiva, mas existe pressão localizada em um produto. "
            "Vale revisar descontos e mix antes de buscar crescimento adicional."
        )
    elif "região" in normalized or "regiao" in normalized:
        ids = ["TOP_REGION", "KPI_REVENUE", "TOP_PRODUCT"]
        answer = (
            "A liderança regional está concentrada no principal mercado do período. "
            "O produto de maior receita também explica parte relevante desse desempenho."
        )
    elif "concentra" in normalized or "cliente" in normalized:
        ids = ["CONCENTRATION", "KPI_REVENUE", "TOP_REGION"]
        answer = (
            "Há concentração relevante nos maiores clientes, embora a receita também esteja distribuída regionalmente. "
            "O principal risco é a dependência de renovações de contas de maior porte."
        )
    else:
        ids = ["KPI_REVENUE", "KPI_MARGIN", "TOP_REGION", "CONCENTRATION"]
        answer = (
            "A visão executiva combina crescimento, rentabilidade e concentração. "
            "Os principais pontos de atenção estão na margem e na dependência dos maiores clientes."
        )

    ids = [item for item in ids if item in catalog]
    return {
        "answer": answer,
        "evidence": [{"id": item, **catalog[item]} for item in ids],
        "confidence": "high",
        "mode": "demo",
    }
