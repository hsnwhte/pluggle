import pytest
from pydantic import ValidationError

from pluggle.enums import ContentFormat, PluggleIOType
from pluggle.models.dto import InputArgs


@pytest.fixture
def base_args():
    return {
        "source_type": PluggleIOType.FILE,
        "source_address": "./input.json",
        "target_type": PluggleIOType.FILE,
    }


def test_target_extension_must_match_format(base_args):
    with pytest.raises(ValidationError):
        InputArgs(
            **base_args, target_address="out.xml", target_format=ContentFormat.JSON
        )
