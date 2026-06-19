# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CONTACT Software GmbH
# https://www.contact-software.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module implementing the unit tests for csspin-ce"""

from unittest.mock import patch

import pytest

# ce_services calls _default_solr_version() at module level to populate
# defaults.solr.version, so interpolate1 must be patched before the import.
with patch("csspin.interpolate1", return_value="2026.3"):
    from csspin_ce import ce_services


@pytest.mark.parametrize(
    "umbrella, expected_version",
    [
        ("16.0", "9.10.1"),
        ("2026.1", "9.10.1"),
        ("2026.2", "9.10.1"),
        ("2026.3", "10.0.0"),
    ],
)
def test_default_solr_version(umbrella, expected_version):
    """Test whether the default solr version is being determined correctly."""
    with patch.object(
        ce_services, "interpolate1", return_value=umbrella
    ) as mock_interpolate1:
        result = ce_services._default_solr_version()  # pylint: disable=protected-access

    mock_interpolate1.assert_called_once_with("{contact_elements.umbrella}")
    assert result == expected_version
