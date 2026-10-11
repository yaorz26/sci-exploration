import math

from scripts.analyze_funprm_calibration import pearson, percentile


def test_pearson_handles_identical_and_reversed_vectors() -> None:
    assert math.isclose(pearson([0.0, 0.5, 1.0], [0.0, 0.5, 1.0]), 1.0)
    assert math.isclose(pearson([0.0, 0.5, 1.0], [1.0, 0.5, 0.0]), -1.0)


def test_percentile_interpolates_between_ordered_values() -> None:
    assert percentile([0.0, 1.0], 0.25) == 0.25
    assert percentile([3.0, 1.0, 2.0], 0.5) == 2.0
