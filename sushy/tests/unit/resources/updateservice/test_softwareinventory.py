# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from unittest import mock

from sushy import exceptions
from sushy.resources import constants as res_cons
from sushy.resources.updateservice import softwareinventory
from sushy.tests.unit import base


class SoftwareInventoryTestCase(base.TestCase):

    def setUp(self):
        super().setUp()
        conn = mock.Mock()
        with open(
            'sushy/tests/unit/json_samples/softwareinventory.json') as f:
            self.json_doc = json.load(f)

        conn.get.return_value.json.return_value = self.json_doc

        self.soft_inv = softwareinventory.SoftwareInventory(
            conn,
            '/redfish/v1/UpdateService/SoftwareInventory/1',
            redfish_version='1.3.0')

    def test__parse_attributes(self):
        self.soft_inv._parse_attributes(self.json_doc)
        self.assertEqual('BMC', self.soft_inv.identity)
        self.assertEqual(
            '1.30.367a12-rev1',
            self.soft_inv.lowest_supported_version)
        self.assertEqual('Contoso', self.soft_inv.manufacturer)
        self.assertEqual('Contoso BMC Firmware', self.soft_inv.name)
        self.assertEqual('2017-08-22T12:00:00', self.soft_inv.release_date)
        self.assertEqual(
            res_cons.State.ENABLED,
            self.soft_inv.status.state)
        self.assertEqual(res_cons.Health.OK, self.soft_inv.status.health)
        self.assertEqual(
            '1624A9DF-5E13-47FC-874A-DF3AFF143089',
            self.soft_inv.software_id)
        self.assertTrue(self.soft_inv.updateable)
        self.assertEqual('1.45.455b66-rev4', self.soft_inv.version)

    def test__parse_attributes_return(self):
        attributes = self.soft_inv._parse_attributes(self.json_doc)

        # Test that various types are returned correctly
        self.assertEqual('BMC', attributes.get('identity'))
        self.assertEqual({'health': res_cons.Health.OK,
                          'health_rollup': None,
                          'state': res_cons.State.ENABLED},
                         attributes.get('status'))
        self.assertEqual(True, attributes.get('updateable'))

    def test__parse_attributes_missing_identity(self):
        self.soft_inv.json.pop('Id')
        self.assertRaisesRegex(
            exceptions.MissingAttributeError, 'attribute Id',
            self.soft_inv._parse_attributes, self.json_doc)


class SoftwareInventoryCollectionTestCase(base.TestCase):

    def setUp(self):
        super().setUp()
        conn = mock.Mock()
        with open('sushy/tests/unit/json_samples/'
                  'firmwareinventory_collection.json') as f:
            self.json_doc = json.load(f)

        conn.get.return_value.json.return_value = self.json_doc

        self.soft_inv_col = softwareinventory.SoftwareInventoryCollection(
            conn, '/redfish/v1/UpdateService/FirmwareInventory',
            redfish_version='1.3.0')

    def test__parse_attributes(self):
        self.soft_inv_col._parse_attributes(self.json_doc)
        self.assertEqual('1.3.0', self.soft_inv_col.redfish_version)
        self.assertEqual(
            'Firmware Inventory Collection',
            self.soft_inv_col.name)

    @mock.patch.object(
        softwareinventory, 'SoftwareInventory', autospec=True)
    def test_get_member(self, mock_softwareinventory):
        path = ('/redfish/v1/UpdateService/FirmwareInventory/'
                'Current-102303-19.0.12')
        self.soft_inv_col.get_member(path)
        mock_softwareinventory.assert_called_once_with(
            self.soft_inv_col._conn, path,
            self.soft_inv_col.redfish_version, None, self.soft_inv_col.root)

    @mock.patch.object(
        softwareinventory, 'SoftwareInventory', autospec=True)
    def test_get_members(self, mock_softwareinventory):
        members = self.soft_inv_col.get_members()
        calls = [
            mock.call(self.soft_inv_col._conn,
                      ('/redfish/v1/UpdateService/FirmwareInventory/'
                       'Current-101560-25.5.6.0009'),
                      redfish_version=self.soft_inv_col.redfish_version,
                      registries=None,
                      root=self.soft_inv_col.root),

            mock.call(self.soft_inv_col._conn,
                      ('/redfish/v1/UpdateService/FirmwareInventory/'
                       'Installed-101560-25.5.6.0009'),
                      redfish_version=self.soft_inv_col.redfish_version,
                      registries=None,
                      root=self.soft_inv_col.root),

            mock.call(self.soft_inv_col._conn,
                      ('/redfish/v1/UpdateService/FirmwareInventory/'
                       'Previous-102302-18.8.9'),
                      redfish_version=self.soft_inv_col.redfish_version,
                      registries=None,
                      root=self.soft_inv_col.root)
        ]
        mock_softwareinventory.assert_has_calls(calls)
        self.assertIsInstance(members, list)
        self.assertEqual(3, len(members))


class SoftwareInventoryCollectionExpandedTestCase(base.TestCase):

    def setUp(self):
        super().setUp()
        self.conn = mock.Mock()
        with open('sushy/tests/unit/json_samples/'
                  'firmwareinventory_collection_expanded.json') as f:
            self.json_doc = json.load(f)

        self.conn.get.return_value.json.return_value = self.json_doc

        self.soft_inv_col = softwareinventory.SoftwareInventoryCollection(
            self.conn,
            '/redfish/v1/UpdateService/FirmwareInventory?$expand=.($levels=1)',
            redfish_version='1.3.0')

    def test_get_members_expanded(self):
        self.conn.get.reset_mock()
        members = self.soft_inv_col.get_members()

        # All members came from the expanded document, nothing fetched.
        self.conn.get.assert_not_called()
        self.assertEqual(3, len(members))
        self.assertEqual(
            ['Installed-25227-7.10.30.00', 'Installed-159-2.19.1',
             'Previous-159-2.18.0'],
            [m.identity for m in members])
        self.assertEqual('Integrated Dell Remote Access Controller',
                         members[0].name)
        self.assertEqual('7.10.30.00', members[0].version)
        self.assertEqual('Dell', members[0].manufacturer)
        self.assertEqual('25227', members[0].software_id)
        self.assertEqual(
            '/redfish/v1/UpdateService/FirmwareInventory/'
            'Installed-25227-7.10.30.00', members[0].path)

    def test_get_members_not_expanded_fallback(self):
        with open('sushy/tests/unit/json_samples/'
                  'firmwareinventory_collection.json') as f:
            unexpanded = json.load(f)
        with open('sushy/tests/unit/json_samples/'
                  'softwareinventory.json') as f:
            member = json.load(f)
        self.conn.get.reset_mock()
        self.conn.get.return_value.json.side_effect = [
            unexpanded, member, member, member]

        col = softwareinventory.SoftwareInventoryCollection(
            self.conn,
            '/redfish/v1/UpdateService/FirmwareInventory?$expand=.($levels=1)',
            redfish_version='1.3.0')
        members = col.get_members()

        # One GET for the collection, one per member.
        self.assertEqual(4, self.conn.get.call_count)
        self.assertEqual(3, len(members))
        self.assertEqual('BMC', members[0].identity)

    def test_get_members_empty(self):
        self.conn.get.return_value.json.return_value = {
            '@odata.id': '/redfish/v1/UpdateService/FirmwareInventory',
            'Name': 'Firmware Inventory Collection',
            'Members': []}
        col = softwareinventory.SoftwareInventoryCollection(
            self.conn,
            '/redfish/v1/UpdateService/FirmwareInventory?$expand=.($levels=1)',
            redfish_version='1.3.0')
        self.assertEqual([], col.get_members())
