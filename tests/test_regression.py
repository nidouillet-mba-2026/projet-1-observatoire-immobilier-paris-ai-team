"""Unit tests for analysis/regression.py."""

import pytest

import analysis.regression as regression


def test_predict_returns_line_value():
	assert regression.predict(alpha=1.5, beta=2.0, x_i=3.0) == pytest.approx(7.5)


def test_error_is_observed_minus_predicted():
	predicted = regression.predict(alpha=1.0, beta=0.5, x_i=4.0)
	assert regression.error(alpha=1.0, beta=0.5, x_i=4.0, y_i=5.0) == pytest.approx(5.0 - predicted)


def test_sum_of_sqerrors_is_zero_for_perfect_line():
	x = [0.0, 1.0, 2.0, 3.0]
	y = [1.0, 3.0, 5.0, 7.0]  # y = 1 + 2x
	assert regression.sum_of_sqerrors(alpha=1.0, beta=2.0, x=x, y=y) == pytest.approx(0.0)


def test_sum_of_sqerrors_matches_manual_computation():
	x = [1.0, 2.0, 3.0]
	y = [2.0, 2.5, 5.0]
	# Model y = 1 + 1x gives residuals [0.0, -0.5, 1.0], squared sum = 1.25
	assert regression.sum_of_sqerrors(alpha=1.0, beta=1.0, x=x, y=y) == pytest.approx(1.25)


def test_least_squares_fit_uses_stats_helpers(monkeypatch):
	monkeypatch.setattr(regression, "correlation", lambda _x, _y: 0.5)
	monkeypatch.setattr(regression, "standard_deviation", lambda values: 8.0 if values == [10.0, 14.0] else 4.0)
	monkeypatch.setattr(regression, "mean", lambda values: 12.0 if values == [10.0, 14.0] else 2.0)

	alpha, beta = regression.least_squares_fit(x=[1.0, 3.0], y=[10.0, 14.0])

	# beta = corr * sy / sx = 0.5 * 8 / 4 = 1.0
	# alpha = mean(y) - beta * mean(x) = 12 - 1 * 2 = 10
	assert beta == pytest.approx(1.0)
	assert alpha == pytest.approx(10.0)


def test_total_sum_of_squares_correct():
	y = [1.0, 2.0, 3.0]
	# mean = 2.0, (1-2)^2 + (2-2)^2 + (3-2)^2 = 1 + 0 + 1 = 2.0
	assert regression.total_sum_of_squares(y) == pytest.approx(2.0)


def test_r_squared_is_one_for_zero_residuals(monkeypatch):
	monkeypatch.setattr(regression, "sum_of_sqerrors", lambda _a, _b, _x, _y: 0.0)
	monkeypatch.setattr(regression, "total_sum_of_squares", lambda _y: 10.0)

	r2 = regression.r_squared(alpha=0.0, beta=1.0, x=[1.0], y=[1.0])
	assert r2 == pytest.approx(1.0)


def test_r_squared_matches_formula(monkeypatch):
	monkeypatch.setattr(regression, "sum_of_sqerrors", lambda _a, _b, _x, _y: 2.5)
	monkeypatch.setattr(regression, "total_sum_of_squares", lambda _y: 10.0)

	r2 = regression.r_squared(alpha=0.0, beta=1.0, x=[1.0], y=[1.0])
	assert r2 == pytest.approx(0.75)

