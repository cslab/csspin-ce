# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
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
#

"""
Provides the configuration of `contact_elements.umbrella` which changes the
behavior of the other plugins of the csspin-ce plugin-package.
"""

from csspin import config, die, interpolate1

defaults = config()


def configure(cfg):
    """Configure the plugin by enforcing to choose a valid umbrella."""
    version = interpolate1(cfg.contact_elements.umbrella)
    ALLOWED_VERSIONS = ("16.0", "2026.1", "2026.2")
    if version not in ALLOWED_VERSIONS:
        die(
            f"Invalid value for contact_elements.umbrella: {version}. Possible values are: {ALLOWED_VERSIONS}"
        )
