#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
from unittest import mock

from sushy.resources import constants as res_cons
from sushy.resources.manager import bmc
from sushy.resources import settings
from sushy.tests.unit import base


class BmcTestCase(base.TestCase):

    def setUp(self):
        super().setUp()
        self.conn = mock.Mock()
        with open('sushy/tests/unit/json_samples/manager.json') as f:
            self.manager_json = json.load(f)
        with open('sushy/tests/unit/json_samples/'
                  'manager_bmc_settings.json') as f:
            self.bmc_settings_json = json.load(f)

        self.conn.get.return_value.json.side_effect = [
            self.manager_json,
            self.bmc_settings_json,
            self.bmc_settings_json]

        self.bmc = bmc.Bmc(
            self.conn, '/redfish/v1/Managers/BMC',
            registries={},
            redfish_version='1.0.2')

    def test__parse_attributes(self):
        self.bmc._parse_attributes(self.manager_json)
        self.assertEqual('1.0.2', self.bmc.redfish_version)
        self.assertEqual('BMC', self.bmc.identity)
        self.assertEqual('Manager', self.bmc.name)
        self.assertEqual('ManagerAttributeRegistry.v1_0_0',
                         self.bmc._attribute_registry)
        self.assertEqual('Disabled', self.bmc.attributes['IPMI1_Enable'])
        self.assertEqual('Enabled',
                         self.bmc.attributes['SerialRedirection_Enable'])
        self.assertEqual(1800,
                         self.bmc.attributes['WebServer_SessionTimeout'])
        self.assertEqual([res_cons.ApplyTime.ON_RESET,
                          res_cons.ApplyTime.IMMEDIATE],
                         self.bmc.supported_apply_times)
        # testing here if settings subfield parsed by checking ETag,
        # other settings fields tested in specific settings test
        self.assertEqual('9234ac83b9700123cc32', self.bmc._settings._etag)
        self.assertEqual('Enabled',
                         self.bmc.pending_attributes['IPMI1_Enable'])

    def test_update_status(self):
        self.assertEqual(settings.UPDATE_FAILURE,
                         self.bmc.update_status.status)

    def test_set_attribute(self):
        self.conn.get.return_value.json.side_effect = [self.manager_json]

        self.bmc.set_attribute('IPMI1_Enable', 'Enabled')
        self.bmc._conn.patch.assert_called_once_with(
            '/redfish/v1/Managers/BMC/Settings',
            data={'Attributes': {'IPMI1_Enable': 'Enabled'}},
            etag='9234ac83b9700123cc32')

    def test_set_attributes(self):
        self.conn.get.return_value.json.side_effect = [self.manager_json]

        self.bmc.set_attributes(
            {'IPMI1_Enable': 'Enabled', 'Telnet_Enable': 'Enabled'})
        self.bmc._conn.patch.assert_called_once_with(
            '/redfish/v1/Managers/BMC/Settings',
            data={'Attributes': {'IPMI1_Enable': 'Enabled',
                                 'Telnet_Enable': 'Enabled'}},
            etag='9234ac83b9700123cc32')

    def test_set_attributes_apply_time(self):
        self.conn.get.return_value.json.side_effect = [self.manager_json]

        self.bmc.set_attributes(
            {'IPMI1_Enable': 'Enabled'}, res_cons.ApplyTime.IMMEDIATE)
        self.bmc._conn.patch.assert_called_once_with(
            '/redfish/v1/Managers/BMC/Settings',
            data={'Attributes': {'IPMI1_Enable': 'Enabled'},
                  '@Redfish.SettingsApplyTime': {
                      '@odata.type': '#Settings.v1_0_0.PreferredApplyTime',
                      'ApplyTime': 'Immediate'}},
            etag='9234ac83b9700123cc32')

    def test_get_attribute_registry(self):
        with mock.patch.object(self.bmc, '_get_registry',
                               autospec=True) as mock_get:
            self.bmc.get_attribute_registry()
            mock_get.assert_called_once_with(
                'ManagerAttributeRegistry.v1_0_0',
                language='en',
                description='BMC attribute registry')
