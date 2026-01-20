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

"""
Util which provides the extract function while it hasn't been implement into the spin core.
"""

import tarfile
import zipfile

from csspin import (
    die,
    echo,
)

try:
    from csspin import extract  # pylint: disable=unused-import
except ImportError:

    def extract(archive, extract_to, member=""):
        """Unpacks archives"""
        echo(f"Extracting {archive} to {extract_to}")
        member = member.replace("\\", "/")

        mode = None
        if tarfile.is_tarfile(archive):
            extractor = tarfile.open
            if archive.endswith(".tar.gz") or archive.endswith(".tgz"):
                mode = "r:gz"
            elif archive.endswith(".tar.xz"):
                mode = "r:xz"
        elif zipfile.is_zipfile(archive):
            extractor = zipfile.ZipFile
            mode = "r"
        if not mode:
            die(f"Unsupported archive type {archive}")

        with extractor(  # pylint: disable=possibly-used-before-assignment
            archive, mode=mode  # pylint: disable=possibly-used-before-assignment
        ) as arc:
            if isinstance(arc, tarfile.TarFile):
                members = (
                    entity
                    for entity in arc.getmembers()  # pylint: disable=maybe-no-member
                    if entity.name.startswith(member)
                )
            elif isinstance(arc, zipfile.ZipFile):
                members = (
                    entity
                    for entity in arc.namelist()  # pylint: disable=maybe-no-member
                    if entity.startswith(member)
                )
            else:
                members = ()

            arc.extractall(
                members=members,
                path=extract_to,
            )  # nosec: tarfile_unsafe_members
