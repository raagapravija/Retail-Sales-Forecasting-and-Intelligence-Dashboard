"""API tests.

The contract tests matter more than they look: the dashboard's TypeScript
interfaces name these exact fields, and TypeScript cannot check a JSON payload it
never sees at compile time. A renamed column in the notebook would otherwise show
up as a blank panel in the browser, with no error anywhere.

Run from the repository root (so `forecasting` is importable):

    PYTHONPATH=. pytest backend/tests -q
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.store import store


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def any_item(client) -> str:
    return client.get("/api/products?limit=1").json()[0]["item_id"]


# ---------------------------------------------------------------------- ops
def test_health_reports_a_loaded_model(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["series_served"] > 0


# ----------------------------------------------------------------- contract
CONTRACT: dict[str, tuple[type, list[str]]] = {
    "/api/analytics/overview": (dict, [
        "total_revenue", "total_units", "forecast_units_28d", "forecast_revenue_28d",
        "forecast_accuracy_pct", "history_from", "history_to", "forecast_from",
        "forecast_to", "series_served"]),
    "/api/metrics": (dict, [
        "mae", "rmse", "wmape_pct", "wrmsse", "baseline_rmse",
        "improvement_vs_baseline_pct", "accuracy_pct", "accuracy_by_level"]),
    "/api/model/info": (dict, [
        "model_type", "target", "horizon_days", "framing", "trained_rows", "trained_series",
        "trained_from", "trained_to", "test_window", "last_observed_date", "features",
        "best_params", "library_versions"]),
    "/api/categories": (list, [
        "cat_id", "units", "revenue", "unit_share_pct", "revenue_share_pct"]),
    "/api/stores": (list, [
        "store_id", "state_id", "units", "revenue", "forecast_units_28d",
        "forecast_revenue_28d"]),
    "/api/analytics/top-products?limit=3": (list, [
        "item_id", "cat_id", "dept_id", "units", "revenue"]),
    "/api/analytics/weekday": (list, ["weekday", "mean_units"]),
    "/api/products?limit=3": (list, ["item_id", "dept_id", "cat_id"]),
    "/api/insights/attention?limit=3": (list, [
        "item_id", "store_id", "cat_id", "recent_daily_units", "forecast_daily_units",
        "change_pct", "forecast_revenue_28d"]),
    "/api/insights/restock?limit=3": (list, [
        "item_id", "store_id", "cat_id", "recent_daily_units", "forecast_daily_units",
        "change_pct", "forecast_revenue_28d"]),
    "/api/forecast/totals": (list, ["date", "predicted_units", "expected_revenue"]),
}


@pytest.mark.parametrize("path,spec", list(CONTRACT.items()), ids=list(CONTRACT))
def test_response_shape(client, path, spec):
    kind, fields = spec
    res = client.get(path)
    assert res.status_code == 200, res.text
    body = res.json()
    assert isinstance(body, kind)
    sample = body[0] if kind is list else body
    assert not [f for f in fields if f not in sample]


# ------------------------------------------------------------------ history
def test_chain_history_is_ordered(client):
    points = client.get("/api/sales/history?start=2016-01-01").json()["points"]
    dates = [p["date"] for p in points]
    assert dates == sorted(dates)
    assert all("units" in p for p in points)


def test_served_history_matches_the_forecast_scope(client):
    """The served-series history must cover the same series as the forecast.

    Its last days are rebuilt from the model's own serving history, so they must match
    exactly; and it must be a subset of the chain-wide total.
    """
    res = client.get("/api/sales/history?scope=served")
    if res.status_code == 404:
        pytest.skip("artifacts predate bi_daily_sales_served")
    body = res.json()
    assert body["scope"] == "served"
    served = pd.DataFrame(body["points"]).set_index("date")["units"]

    hist = store.history.groupby("d_num")["sales"].sum()
    dates = store.calendar.set_index("d_num").loc[hist.index, "date"]
    expected = pd.Series(hist.to_numpy(), index=pd.to_datetime(dates).dt.strftime("%Y-%m-%d"))
    np.testing.assert_allclose(served.loc[expected.index].to_numpy(), expected.to_numpy())

    chain = pd.DataFrame(client.get("/api/sales/history").json()["points"]).set_index("date")["units"]
    assert (served <= chain.loc[served.index] + 1e-9).all()


def test_series_history_needs_both_ids(client, any_item):
    assert client.get(f"/api/sales/history?item_id={any_item}").status_code == 400


# ----------------------------------------------------------------- forecast
def test_forecast_returns_the_full_horizon(client, any_item):
    body = client.post("/api/forecast",
                       json={"store_id": "CA_1", "item_id": any_item, "horizon": 28}).json()
    assert len(body["forecast"]) == 28
    assert body["forecast"][0]["date"] > body["generated_from"]
    assert all(p["predicted_sales"] >= 0 for p in body["forecast"])
    dates = [p["date"] for p in body["forecast"]]
    assert dates == sorted(dates) and len(set(dates)) == 28


def test_live_forecast_matches_the_notebook(client, any_item):
    """The API's feature pipeline must reproduce the notebook's, to the bit.

    This is the end-to-end version of the training/serving skew assertion in
    Part 6 of the notebook.
    """
    body = client.post("/api/forecast",
                       json={"store_id": "CA_1", "item_id": any_item, "horizon": 28}).json()
    live = np.array([p["predicted_units_exact"] for p in body["forecast"]])

    precomputed = store.forecast_28d
    ref = (precomputed[(precomputed["item_id"] == any_item)
                       & (precomputed["store_id"] == "CA_1")]
           .sort_values("d_num")["predicted_units"].to_numpy())

    assert len(ref) == len(live)
    np.testing.assert_allclose(live, ref, rtol=1e-6, atol=1e-6)


def test_shorter_horizons_are_a_prefix(client, any_item):
    full = client.post("/api/forecast",
                       json={"store_id": "CA_1", "item_id": any_item, "horizon": 28}).json()
    short = client.post("/api/forecast",
                        json={"store_id": "CA_1", "item_id": any_item, "horizon": 7}).json()
    assert len(short["forecast"]) == 7
    for a, b in zip(short["forecast"], full["forecast"][:7]):
        assert a["date"] == b["date"]
        assert a["predicted_units_exact"] == pytest.approx(b["predicted_units_exact"], rel=1e-6)


def test_revenue_is_units_times_price(client, any_item):
    body = client.post("/api/forecast",
                       json={"store_id": "CA_1", "item_id": any_item, "horizon": 28}).json()
    for p in body["forecast"]:
        if p["sell_price"] is not None:
            assert p["expected_revenue"] == pytest.approx(
                p["predicted_units_exact"] * p["sell_price"], rel=1e-6)


# -------------------------------------------------------------------- errors
def test_unknown_series_is_a_404_not_a_guess(client):
    res = client.post("/api/forecast",
                      json={"store_id": "CA_1", "item_id": "NOT_A_REAL_ITEM", "horizon": 28})
    assert res.status_code == 404
    assert "serves" in res.json()["detail"]


def test_horizon_beyond_the_model_is_rejected(client, any_item):
    res = client.post("/api/forecast",
                      json={"store_id": "CA_1", "item_id": any_item, "horizon": 90})
    assert res.status_code == 422


# ---------------------------------------------------------------- invariants
def test_metrics_beat_the_baseline(client):
    m = client.get("/api/metrics").json()
    assert m["rmse"] < m["baseline_rmse"]
    assert m["improvement_vs_baseline_pct"] > 0
    assert m["wrmsse"] < 1.0, "WRMSSE >= 1 means no skill over a naive forecast"


def test_accuracy_by_level_starts_at_the_headline(client):
    """The finest level is the headline number; coarser levels are scored on the same forecast."""
    m = client.get("/api/metrics").json()
    levels = m["accuracy_by_level"]
    if not levels:
        pytest.skip("artifacts predate accuracy_by_level")
    assert [lv["level"] for lv in levels][0] == "item_store_day"
    assert levels[0]["accuracy_pct"] == pytest.approx(m["accuracy_pct"], abs=1e-6)
    for lv in levels:
        assert {"level", "label", "accuracy_pct", "naive_accuracy_pct"} <= lv.keys()
        assert 0 <= lv["accuracy_pct"] <= 100
    by = {lv["level"]: lv["accuracy_pct"] for lv in levels}
    assert by["item_store_week"] >= by["item_store_day"]
    assert by["store_day"] >= by["item_store_day"]


def test_accuracy_by_level_sums_before_scoring():
    """Errors that cancel within a group must not count against the summed forecast."""
    from forecasting.evaluation import accuracy_by_level

    frame = pd.DataFrame({
        "item_id": ["FOODS_1_001"] * 14,
        "store_id": ["CA_1"] * 14,
        "d_num": range(1, 15),
        "sales": [2.0, 4.0] * 7,
        "pred": [4.0, 2.0] * 7,      # off by 2 every day, exact over the window
        "naive": [3.0] * 14,
    })
    by = {lv["level"]: lv for lv in accuracy_by_level(frame)}
    # days: 14 x |2| = 28 units wrong out of 42
    assert by["item_store_day"]["accuracy_pct"] == pytest.approx(100 - 28 / 42 * 100)
    # weeks: 20 vs 22, then 22 vs 20 -> 4 wrong out of 42
    assert by["item_store_week"]["accuracy_pct"] == pytest.approx(100 - 4 / 42 * 100)
    assert by["item_store_28d"]["accuracy_pct"] == pytest.approx(100.0)
    assert by["item_store_28d"]["naive_accuracy_pct"] == pytest.approx(100.0)


def test_forecast_window_follows_the_history(client):
    o = client.get("/api/analytics/overview").json()
    assert pd.Timestamp(o["forecast_from"]) > pd.Timestamp(o["history_to"])
    assert (pd.Timestamp(o["forecast_to"]) - pd.Timestamp(o["forecast_from"])).days == 27
