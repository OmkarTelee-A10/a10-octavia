#    Copyright 2019, A10 Networks
#
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

from oslo_config import cfg
from oslo_log import log as logging
from taskflow import task

from a10_octavia.common import openstack_mappings
from a10_octavia.controller.worker.tasks import utils
from a10_octavia.controller.worker.tasks.decorators import axapi_client_decorator

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PoolParent(object):

    def set(self, set_method, pool, axapi_client):

        args = {'service_group': utils.meta(pool, 'service_group', {})}
        service_group_temp = {}
        service_group_temp['template-server'] = CONF.service_group.template_server
        service_group_temp['template-port'] = CONF.service_group.template_port
        service_group_temp['template-policy'] = CONF.service_group.template_policy
        protocol = openstack_mappings.service_group_protocol(axapi_client, pool.protocol)
        lb_method = openstack_mappings.service_group_lb_method(axapi_client, pool.lb_algorithm)
        try:
            set_method(pool.id,
                       protocol=protocol,
                       lb_method=lb_method,
                       service_group_templates=service_group_temp,
                       axapi_args=args)
            LOG.debug("Pool created successfully: %s", pool.id)
            return pool
        except Exception as e:
            LOG.exception("Failed to create pool: %s", str(e))
            raise


class PoolCreate(PoolParent, task.Task):
    """Task to create pool"""

    @axapi_client_decorator
    def execute(self, vthunder, pool):
        return self.set(self.axapi_client.slb.service_group.create, pool, self.axapi_client)


class PoolDelete(task.Task):
    """ Task to delete pool """

    @axapi_client_decorator
    def execute(self, pool, vthunder):
        try:
            self.axapi_client.slb.service_group.delete(pool.id)
            LOG.debug("Pool deleted successfully: %s", pool.id)
        except Exception as e:
            LOG.warning("Failed to delete pool: %s", str(e))


class PoolUpdate(PoolParent, task.Task):
    """Task to update pool"""

    @axapi_client_decorator
    def execute(self, pool, vthunder, update_dict):
        if 'session_persistence' in update_dict:
            pool.session_persistence.__dict__.update(update_dict['session_persistence'])
            del update_dict['session_persistence']
        pool.__dict__.update(update_dict)
        self.set(self.axapi_client.slb.service_group.update, pool, self.axapi_client)