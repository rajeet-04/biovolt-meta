import math

import pytest

from biovolt_backend.domain.optical import calculate_od680


def test_od680_uses_dark_and_blank_correction():
    value = calculate_od680(sample_raw=12080, dark_raw=320, blank_raw=23840)
    expected = -math.log10((12080 - 320) / (23840 - 320))
    assert value == pytest.approx(expected)


@pytest.mark.parametrize(
    "sample,dark,blank",
    [
        (None, 320, 23840),
        (12080, None, 23840),
        (12080, 320, None),
        (320, 320, 23840),
        (12080, 320, 320),
        (30000, 320, 23840),
    ],
)
def test_invalid_optical_reference_returns_none(sample, dark, blank):
    assert calculate_od680(sample, dark, blank) is None
