#    Copyright 2020, A10 Networks
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


import copy
import imp
try:
    from unittest import mock
except ImportError:
    import mock

from oslo_config import cfg
from oslo_config import fixture as oslo_fixture
from oslo_utils import uuidutils

from octavia.common import data_models as c_data_models
from octavia.network import data_models as n_data_models

from a10_octavia.common.config_options import A10_GLOBAL_OPTS
from a10_octavia.common import data_models
from a10_octavia.controller.worker.tasks import a10_database_tasks as task
from a10_octavia.tests.common import a10constant
from a10_octavia.tests.unit import base


VTHUNDER_ID_1 = uuidutils.generate_uuid()
VTHUNDER = data_models.VThunder(id=VTHUNDER_ID_1)
FIXED_IP = n_data_models.FixedIP(ip_address='10.10.10.10')
PORT = n_data_models.Port(id=uuidutils.generate_uuid(), fixed_ips=[FIXED_IP])
LB = c_data_models.LoadBalancer(id=a10constants.MOCK_LOAD_BALANCER_ID)


class TestA10DatabaseTasks(base.BaseTaskTestCase):
    def setUp(self):
        super(TestA10DatabaseTasks, self).setUp()
        imp.reload(task)
        self.conf = self.useFixture(oslo_fixture.Config(cfg.CONF))
        self.conf.register_opts(A10_GLOBAL_OPTS,
                                group=a10constants.A10_GLOBAL_OPTS)
        self.db_session = mock.patch(
            'a10_octavia.controller.worker.tasks.a10_database_tasks.db_apis.get_session')
        self.db_session.start()

    def tearDown(self):
        super(TestA10DatabaseTasks, self).tearDown()
        self.db_session.stop()

<<<<<<< HEAD
    @mock.patch('a10_octavia.common.utils.get_parent_project',
                return_value=a10constants.MOCK_PARENT_PROJECT_ID)
    def test_get_vthunder_by_loadbalancer_parent_partition_exists(self,
                                                                  mock_parent_project_id):
        self.conf.config(group=a10constants.A10_GLOBAL_OPTS, use_parent_partition=True)
        mock_vthunder = copy.deepcopy(VTHUNDER)
        mock_vthunder.partition_name = a10constants.MOCK_CHILD_PART
        mock_vthunder.undercloud = True
        mock_vthunder.hierarchical_multitenancy = True

        mock_get_vthunder = task.GetVThunderByLoadBalancer()
        mock_get_vthunder.vthunder_repo = mock.MagicMock()
        mock_get_vthunder.vthunder_repo.get_vthunder_from_lb().return_value = mock_vthunder
        vthunder = mock_get_vthunder.execute(LB)
        self.assertEqual(vthunder.partition_name, a10constants.MOCK_PARENT_PROJECT_ID[:14])

    @mock.patch('a10_octavia.common.utils.get_parent_project',
                return_value=None)
    def test_get_vthunder_by_loadbalancer_parent_partition_not_exists(self,
                                                                      mock_parent_project_id):
        self.conf.config(group=a10constants.A10_GLOBAL_OPTS, use_parent_partition=True)

        mock_vthunder = copy.deepcopy(VTHUNDER)
        mock_vthunder.partition_name = a10constants.MOCK_CHILD_PART
        mock_vthunder.undercloud = True
        mock_vthunder.hierarchical_multitenancy = True

        mock_get_vthunder = task.GetVThunderByLoadBalancer()
        mock_get_vthunder.vthunder_repo.get_vthunder_from_lb = mock.MagicMock()
        mock_get_vthunder.vthunder_repo.get_vthunder_from_lb.return_value = mock_vthunder
        vthunder = mock_get_vthunder.execute(LB)
        self.assertEqual(vthunder.partition_name, a10constants.MOCK_CHILD_PART)

    def test_get_vthunder_by_loadbalancer_parent_partition_no_ohm(self):
        self.conf.config(group=a10constants.A10_GLOBAL_OPTS, use_parent_partition=True)

        mock_vthunder = copy.deepcopy(VTHUNDER)
        mock_vthunder.partition_name = a10constants.MOCK_CHILD_PART
        mock_vthunder.undercloud = True
        mock_vthunder.hierarchical_multitenancy = False

        mock_get_vthunder = task.GetVThunderByLoadBalancer()
        mock_get_vthunder.vthunder_repo.get_vthunder_from_lb = mock.MagicMock()
        mock_get_vthunder.vthunder_repo.get_vthunder_from_lb.return_value = mock_vthunder
        vthunder = mock_get_vthunder.execute(LB)
        self.assertEqual(vthunder.partition_name, a10constants.MOCK_CHILD_PART)

    def test_get_vthunder_by_loadbalancer_parent_partition_ohm_no_use_parent_partition(self):
        self.conf.config(group=a10constants.A10_GLOBAL_OPTS, use_parent_partition=False)

        mock_vthunder = copy.deepcopy(VTHUNDER)
        mock_vthunder.partition_name = a10constants.MOCK_CHILD_PROJECT_ID[:14]
        mock_vthunder.undercloud = True
        mock_vthunder.hierarchical_multitenancy = True

        mock_get_vthunder = task.GetVThunderByLoadBalancer()
        mock_get_vthunder.vthunder_repo.get_vthunder_from_lb = mock.MagicMock()
        mock_get_vthunder.vthunder_repo.get_vthunder_from_lb.return_value = mock_vthunder
        vthunder = mock_get_vthunder.execute(LB)
        self.assertEqual(vthunder.partition_name, a10constants.MOCK_CHILD_PROJECT_ID[:14])

    def test_update_vthunder_vrrp_entry_with_port_info(self):
        mock_vthunder_entry = task.UpdateVThunderVRRPEntry()
        mock_vthunder_entry.vthunder_repo = mock.Mock()
        mock_vthunder_entry.execute(VTHUNDER, PORT)
        mock_vthunder_entry.vthunder_repo.update.assert_called_once_with(
            mock.ANY,
            VTHUNDER_ID_1,
            vrrp_port_id=PORT.id,
            vrid_floating_ip=PORT.fixed_ips[0].ip_address)

    def test_update_vthunder_vrrp_entry_with_none_port(self):
        mock_vthunder_entry = task.UpdateVThunderVRRPEntry()
        mock_vthunder_entry.vthunder_repo = mock.Mock()
        mock_vthunder_entry.execute(VTHUNDER, None)
        mock_vthunder_entry.vthunder_repo.update.assert_not_called()
