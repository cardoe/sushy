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

# BMC (Manager) settings are structurally identical to BIOS settings: a set of
# named, typed attributes described by an attribute registry. This resource is
# modelled on :class:`sushy.resources.system.bios.Bios` but reads the
# attributes exposed by a Redfish ``Manager`` (the BMC) rather than a
# ``ComputerSystem``.
# https://redfish.dmtf.org/schemas/

import logging

from sushy.resources import base
from sushy.resources import settings
from sushy import utils

LOG = logging.getLogger(__name__)


class Bmc(base.ResourceBase):

    def __init__(self, connector, path, redfish_version=None, registries=None,
                 root=None):
        """A class representing the settings of a BMC (Manager)

        :param connector: A Connector instance
        :param path: Sub-URI path to the resource exposing the BMC attributes
        :param redfish_version: The version of RedFish. Used to construct
            the object according to schema of the given version.
        :param registries: Dict of message registries to be used when
            parsing messages of attribute update status
        :param root: Sushy root object. Empty for Sushy root itself.
        """
        super().__init__(
            connector, path, redfish_version=redfish_version,
            registries=registries, root=root)

    identity = base.Field('Id')
    """The BMC settings resource identity string"""

    name = base.Field('Name')
    """The name of the resource"""

    description = base.Field('Description')
    """Human-readable description of the BMC settings resource"""

    _attribute_registry = base.Field('AttributeRegistry')
    """The Resource ID of the Attribute Registry for the BMC attributes"""

    _settings = settings.SettingsField()
    """Results of the last BMC attribute update"""

    attributes = base.Field('Attributes')
    """Vendor-specific key-value dict of effective BMC attributes

    Attributes cannot be updated directly.
    To update use :py:func:`~set_attribute` or :py:func:`~set_attributes`
    """

    maintenance_window = settings.MaintenanceWindowField(
        '@Redfish.MaintenanceWindow')
    """Indicates if a given resource has a maintenance window assignment
    for applying settings or operations"""

    _apply_time_settings = settings.SettingsApplyTimeField()

    @property
    @utils.cache_it
    def _pending_settings_resource(self):
        """Pending BMC settings resource"""
        return Bmc(
            self._conn, self._settings.resource_uri,
            registries=None,
            redfish_version=self.redfish_version, root=self.root)

    @property
    def pending_attributes(self):
        """Pending BMC attributes

        BMC attributes that have been committed to the BMC, but for them to
        take effect a restart is necessary.
        """
        return self._pending_settings_resource.attributes

    @property
    def apply_time_settings(self):
        return self._pending_settings_resource._apply_time_settings

    def set_attribute(self, key, value, apply_time=None,
                      maint_window_start_time=None,
                      maint_window_duration=None):
        """Update an attribute

        Attribute update is not immediate but may require a restart.
        Committed attributes can be checked at :py:attr:`~pending_attributes`
        property

        :param key: Attribute name
        :param value: Attribute value
        :param apply_time: When to update the attribute. Optional.
            An :py:class:`sushy.ApplyTime` value.
        :param maint_window_start_time: The start time of a maintenance window,
            datetime. Required when updating during maintenance window and
            default maintenance window not set by the system.
        :param maint_window_duration: Duration of maintenance time since
            maintenance window start time in seconds. Required when updating
            during maintenance window and default maintenance window not
            set by the system.
        """
        self.set_attributes({key: value}, apply_time, maint_window_start_time,
                            maint_window_duration)

    def set_attributes(self, value, apply_time=None,
                       maint_window_start_time=None,
                       maint_window_duration=None):
        """Update many attributes at once

        Attribute update is not immediate but may require a restart.
        Committed attributes can be checked at :py:attr:`~pending_attributes`
        property

        :param value: Key-value pairs for attribute name and value
        :param apply_time: When to update the attributes. Optional.
            An :py:class:`sushy.ApplyTime` value.
        :param maint_window_start_time: The start time of a maintenance window,
            datetime. Required when updating during maintenance window and
            default maintenance window not set by the system.
        :param maint_window_duration: Duration of maintenance time since
            maintenance window start time in seconds. Required when updating
            during maintenance window and default maintenance window not
            set by the system.
        """
        payload = {'Attributes': value}
        payload = utils.process_apply_time_input(
            payload, apply_time, maint_window_start_time,
            maint_window_duration)
        # NOTE: refresh to retrieve the current ETag of @Redfish.Settings but
        # do not update the cached _pending_settings_resource, because it is
        # the only cached property and a re-cache is not required.
        self.refresh(force=False)
        self._settings.commit(self._conn, payload)
        utils.cache_clear(self, force_refresh=False,
                          only_these=['_pending_settings_resource'])

    @property
    def update_status(self):
        """Status of the last attribute update

        :returns: :class:`sushy.resources.settings.SettingsUpdate` object
            containing status and any messages
        """
        return self._settings.get_status(self._registries)

    @property
    def supported_apply_times(self):
        """List of supported BMC update apply times

        :returns: List of supported update apply time names
        """
        return self._settings._supported_apply_times

    def get_attribute_registry(self, language='en'):
        """Get the Attribute Registry associated with this BMC instance

        :param language: RFC 5646 language code for Message Registries.
            Indicates language of registry to be used. Defaults to 'en'.
        :returns: the BMC Attribute Registry
        """
        return self._get_registry(self._attribute_registry,
                                  language=language,
                                  description='BMC attribute registry')
