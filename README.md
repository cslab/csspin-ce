# spin_ce

This repository contains the spin plugin-package `spin_ce`. It provides the
following spin-plugins:

- spin_ce.ce_services
- spin_ce.ce_support_tools
- spin_ce.mkinstance
- spin_ce.pkgtest

Initially, the sources for the plugins mkinstance and ce_services have been
copied from https://code.contact.de/qs/tooling/spin-plugins/-/tree/87399f327a5979c3ef5619291cd12bc26fce04ac.

## Creating a New Release

The version scheme used is `major.minor.patch` while following the well-known
standards @CONTACT (https://wiki.contact.de/index.php/Versionsnummer).

**Steps to create a release:**

0. Preparations:
    - Verify that all relevant changes are merged into the branch of which the
      release is based.
    - Also make sure that the latest non-scheduled pipeline for that branch is
      green.
1. Enter the Repository within GitLab > Releases > New Release, select the
   desired branch and tag. Further down, enter the release notes including a
   list of changes (e.g. link issue + related MR) and further information that
   might be useful.
2. Hit "Create release" ✨
