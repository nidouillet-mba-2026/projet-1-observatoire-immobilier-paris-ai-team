"""Unit tests for analysis/stats.py using examples from its main block."""

import pytest

import analysis.stats as stats


def test_mean_main_example():
	xs = [1, 2, 3, 4, 5]
	assert stats.mean(xs) == pytest.approx(3.0)


def test_median_main_example():
	xs = [1, 2, 3, 4, 5]
	assert stats.median(xs) == pytest.approx(3.0)


def test_de_mean_main_example():
	xs = [1, 2, 3, 4, 5]
	assert stats.de_mean(xs) == pytest.approx([-2, -1, 0, 1, 2])


def test_sum_of_squares_main_example():
	xs = [1, 2, 3, 4, 5]
	assert stats.sum_of_squares(xs) == pytest.approx(55.0)


def test_variance_main_example():
	xs = [1, 2, 3, 4, 5]
	assert stats.variance(xs) == pytest.approx(2.5)


def test_standard_deviation_main_example():
	xs = [1, 2, 3, 4, 5]
	assert stats.standard_deviation(xs) == pytest.approx(1.5811, rel=1e-3)


def test_covariance_main_example():
	xs = [1, 2, 3, 4, 5]
	ys = [2, 4, 6, 8, 10]
	assert stats.covariance(xs, ys) == pytest.approx(5.0)


def test_correlation_main_example():
	xs = [1, 2, 3, 4, 5]
	ys = [2, 4, 6, 8, 10]
	assert stats.correlation(xs, ys) == pytest.approx(1.0)
