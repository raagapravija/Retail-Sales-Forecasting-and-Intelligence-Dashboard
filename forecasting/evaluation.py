"""Forecast accuracy at the levels decisions are actually made.

A single product in a single store on a single day sells a handful of units, and
most of that count is chance: even a forecast that knew the true expected demand
would miss by roughly half. Scored there, accuracy (``100 - WMAPE``) looks poor no
matter how good the model is. Buyers order per product per week or month, and
planners look at stores and departments, where that noise largely cancels. This
module scores the same test-window forecast summed to each of those levels.

Imported by the notebook (which writes the result into ``model_metadata.json``)
so the number on the dashboard has exactly one definition.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

#: (key, label, grouping columns), finest first. ``week`` and ``window`` are
#: derived from ``d_num`` relative to the first day of the scored window.
LEVELS: list[tuple[str, str, list[str]]] = [
    ("item_store_day", "Product · store · day", ["item_id", "store_id", "d_num"]),
    ("item_store_week", "Product · store · week", ["item_id", "store_id", "week"]),
    ("item_store_28d", "Product · store · 28 days", ["item_id", "store_id", "window"]),
    ("dept_store_week", "Department · store · week", ["dept_id", "store_id", "week"]),
    ("store_day", "Store · day", ["store_id", "d_num"]),
    ("store_week", "Store · week", ["store_id", "week"]),
    ("chain_day", "All stores · day", ["d_num"]),
]


def _accuracy(actual: np.ndarray, pred: np.ndarray) -> float:
    total = actual.sum()
    if total <= 0:
        return float("nan")
    return float(max(0.0, 100.0 - np.abs(pred - actual).sum() / total * 100.0))


def accuracy_by_level(
    frame: pd.DataFrame,
    actual: str = "sales",
    pred: str = "pred",
    naive: str | None = "naive",
) -> list[dict]:
    """Score one forecast window at every level in :data:`LEVELS`.

    Parameters
    ----------
    frame
        One row per (``item_id``, ``store_id``, ``d_num``) in the scored window,
        with the actual units and the forecast. ``dept_id`` is derived from
        ``item_id`` (``FOODS_3_090`` -> ``FOODS_3``) when absent.
    actual, pred, naive
        Column names. ``naive`` is an optional baseline forecast (the seasonal
        naive ``lag_28``) scored alongside, so each level shows the model's lift.

    Returns
    -------
    ``[{"level", "label", "accuracy_pct", "naive_accuracy_pct"}, ...]`` where
    accuracy is ``100 - WMAPE`` of the summed forecast against the summed actuals.
    """
    df = frame.copy()
    if "dept_id" not in df.columns:
        df["dept_id"] = df["item_id"].astype(str).str.rsplit("_", n=1).str[0]
    first = int(df["d_num"].min())
    df["week"] = (df["d_num"] - first) // 7
    df["window"] = 0

    cols = [actual, pred] + ([naive] if naive else [])
    df[cols] = df[cols].astype("float64").fillna(0.0)

    out = []
    for key, label, keys in LEVELS:
        g = df.groupby(keys, observed=True)[cols].sum()
        a = g[actual].to_numpy()
        out.append({
            "level": key,
            "label": label,
            "accuracy_pct": _accuracy(a, g[pred].to_numpy()),
            "naive_accuracy_pct": _accuracy(a, g[naive].to_numpy()) if naive else None,
        })
    return out
