"""Reproducible seasonal baseline on clearly synthetic workload observations."""
from datetime import date, timedelta
from statistics import mean


def workload():
    today = date.today()
    observations = []
    for index in range(56):
        day = today - timedelta(days=55 - index)
        value = [13, 25, 30, 28, 24, 16, 9][day.weekday()] + ((index * 7) % 9) - 4
        observations.append({"date": day.isoformat(), "label": day.strftime("%d %b"), "volume": value})
    train, holdout = observations[:-7], observations[-7:]
    predictions = [train[len(train) - 7 + i]["volume"] for i in range(7)]
    mae = mean(abs(a["volume"] - p) for a, p in zip(holdout, predictions))
    forecast = []
    for i in range(7):
        day = today + timedelta(days=i + 1)
        same_weekday = [x["volume"] for x in observations[-28:] if date.fromisoformat(x["date"]).weekday() == day.weekday()]
        value = round(mean(same_weekday))
        forecast.append({"date": day.isoformat(), "label": day.strftime("%a"), "volume": value, "lower": max(0, value - 5), "upper": value + 5})
    return {"history": observations, "forecast": forecast, "model": "Four-week weekday mean", "baseline": "Previous-week seasonal naive", "holdout_mae": round(mae, 2), "source": "Synthetic demonstration data — not real service demand", "uncertainty": "Illustrative ±5 workload band, not a calibrated prediction interval"}
