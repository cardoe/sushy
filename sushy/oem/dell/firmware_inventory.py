# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


"""Helpers for Dell iDRAC UpdateService FirmwareInventory."""

INSTALLED_PREFIX = 'Installed-'
"""Id prefix iDRAC uses for the firmware currently installed.

iDRAC lists each component several times in FirmwareInventory, keyed by
an Id prefix: ``Installed-`` for the running firmware, ``Previous-`` for
the rollback image, ``Available-`` for staged packages and, for some
components, ``Current-`` duplicating the ``Installed-`` entry.
"""


def get_installed_members(members):
    """Filter FirmwareInventory members down to installed firmware.

    :param members: an iterable of
        :class:`sushy.resources.updateservice.softwareinventory.SoftwareInventory`
        instances, e.g. from
        ``update_service.firmware_inventory_expanded.get_members()``.
    :returns: a list of the members whose Id starts with ``Installed-``,
        preserving the order of ``members``.
    """
    return [m for m in members
            if m.identity and m.identity.startswith(INSTALLED_PREFIX)]
