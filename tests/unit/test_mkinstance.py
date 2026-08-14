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

"""Module implementing the unit tests for csspin_ce.mkinstance"""

import pytest
from csspin import config

from csspin_ce import mkinstance


@pytest.mark.parametrize(
    "umbrella, expected_package",
    [
        ("16.0", "yarn"),
        ("2026.1", "yarn"),
        ("2026.2", "yarn"),
        ("2027.1", "@yarnpkg/cli-dist"),
    ],
)
def test_default_yarn_version(umbrella, expected_package):
    """Test whether the default yarn package is being determined correctly."""
    cfg = config(contact_elements=config(umbrella=umbrella))

    result = mkinstance.default_yarn_version(cfg)

    assert result == expected_package


def test_configure_resolves_callables_within_npm_requires():
    """Test whether 'configure' resolves callables nested in a list, as is
    the case for 'mkinstance.requires.npm', which contains
    'default_yarn_version' alongside plain string entries."""
    cfg = config(
        contact_elements=config(umbrella="2027.1"),
        mkinstance=config(
            requires=config(npm=["sass", mkinstance.default_yarn_version]),
        ),
    )

    mkinstance.configure(cfg)

    assert cfg.mkinstance.requires.npm == ["sass", "@yarnpkg/cli-dist"]
