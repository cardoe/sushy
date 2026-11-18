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


import json
from unittest import mock

from oslotest.base import BaseTestCase

from sushy.oem.dell import firmware_inventory
from sushy.resources.updateservice import softwareinventory


class FirmwareInventoryTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        conn = mock.Mock()
        with open('sushy/tests/unit/json_samples/'
                  'firmwareinventory_collection_expanded.json') as f:
            conn.get.return_value.json.return_value = json.load(f)
        self.collection = softwareinventory.SoftwareInventoryCollection(
            conn, '/redfish/v1/UpdateService/FirmwareInventory',
            redfish_version='1.3.0')

    def test_get_installed_members(self):
        members = firmware_inventory.get_installed_members(
            self.collection.get_members())
        self.assertEqual(
            ['Installed-25227-7.10.30.00', 'Installed-159-2.19.1'],
            [m.identity for m in members])

    def test_get_installed_members_filters_other_prefixes(self):
        members = [mock.Mock(identity=i) for i in (
            'Current-1-1.0', 'Installed-1-1.0', 'Previous-1-0.9',
            'Available-1-1.1', 'BMC')]
        self.assertEqual(
            ['Installed-1-1.0'],
            [m.identity for m in
             firmware_inventory.get_installed_members(members)])

    def test_get_installed_members_empty(self):
        self.assertEqual([], firmware_inventory.get_installed_members([]))
