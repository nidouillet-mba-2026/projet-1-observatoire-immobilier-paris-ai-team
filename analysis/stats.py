"""
Fonctions statistiques from scratch.
Reference : Joel Grus, "Data Science From Scratch", chapitre 5.

IMPORTANT : N'importez pas numpy, pandas ou statistics pour ces fonctions.
Implementez-les avec du Python pur (listes, boucles, math).
"""

import math


def mean(xs: list[float]) -> float:
    """Retourne la moyenne d'une liste de nombres."""
    return sum(xs) / len(xs)

def de_mean(xs: list[float]) -> list[float]:
    """translate x by subtracting its mean (so the result has mean 0)"""
    x_bar = mean(xs)
    return [x_i - x_bar for x_i in xs]


def median(xs: list[float]) -> float:
    """Retourne la mediane d'une liste de nombres."""
    xs_sorted = sorted(xs)
    n=len(xs_sorted)
    mid = n//2
    if n%2==1:
        return xs_sorted[mid]
    else:
        return (xs_sorted[mid-1]+xs_sorted[mid])/2

def sum_of_squares(xs: list[float]) -> float:
    """Retourne la somme des carrés d'une liste de nombres."""
    return sum(x**2 for x in xs)

def variance(xs: list[float]) -> float:
    """Retourne la variance d'une liste de nombres."""
    n=len(xs)
    deviation=de_mean(xs)
    return sum_of_squares(deviation) / (n)


def standard_deviation(xs: list[float]) -> float:
    """Retourne l'ecart-type d'une liste de nombres."""
    return math.sqrt(variance(xs))


def covariance(xs: list[float], ys: list[float]) -> float:
    """Retourne la covariance entre deux series."""
    assert len(xs) == len(ys) #les listes doivent avoir la meme longueur
    n=len(xs)
    return sum(x*y for x,y in zip(de_mean(xs), de_mean(ys))) / (n - 1)


def correlation(xs: list[float], ys: list[float]) -> float:
    """
    Retourne le coefficient de correlation de Pearson entre deux series.
    Retourne 0 si l'une des series a un ecart-type nul.
    """
    assert len(xs) == len(ys)
    stdev_x = standard_deviation(xs)
    stdev_y = standard_deviation(ys)
    if stdev_x > 0 and stdev_y > 0:
        return covariance(xs, ys) / (stdev_x * stdev_y)
    else:
        return 0
