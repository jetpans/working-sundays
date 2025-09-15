import os
from util import load_json, store_json, count_sundays
import numpy as np
FOR_YEAR = 2025


def sample_profit_for_sundays(n, rating, user_ratings):
    # Positive normal sample
    profits = np.random.normal(loc=user_ratings, scale=(5-rating)*user_ratings/2, size=n)
    profits = np.clip(profits, 0, None)

    return profits.tolist()


n_sundays = count_sundays(FOR_YEAR)
data = load_json("data/rawdata.json")
for key in data.keys():
    data[key]["profit"] = sample_profit_for_sundays(n_sundays, data[key]["rating"], data[key]["user_ratings_total"])
store_json(data, "data/sample_profit.json")
