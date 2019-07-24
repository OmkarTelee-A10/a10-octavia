import datetime

from oslo_config import cfg
from oslo_db import api as oslo_db_api
from oslo_db import exception as db_exception
from oslo_log import log as logging
from oslo_serialization import jsonutils
from oslo_utils import excutils
from oslo_utils import uuidutils
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import noload
from sqlalchemy.orm import subqueryload

from octavia.common import constants as consts
from octavia.common import data_models
from octavia.common import exceptions
from octavia.common import validate
from a10_octavia.db import models

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class BaseRepository(object):
    model_class = None

    def count(self, session, **filters):
        """Retrieves a count of entities from the database.

        :param session: A Sql Alchemy database session.
        :param filters: Filters to decide which entities should be retrieved.
        :returns: int
        """
        return session.query(self.model_class).filter_by(**filters).count()

    def create(self, session, **model_kwargs):
        """Base create method for a database entity.

        :param session: A Sql Alchemy database session.
        :param model_kwargs: Attributes of the model to insert.
        :returns: octavia.common.data_model
        """
        with session.begin(subtransactions=True):
            model = self.model_class(**model_kwargs)
            session.add(model)
        return model.to_data_model()

    def delete(self, session, **filters):
        """Deletes an entity from the database.

        :param session: A Sql Alchemy database session.
        :param filters: Filters to decide which entity should be deleted.
        :returns: None
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        model = session.query(self.model_class).filter_by(**filters).one()
        with session.begin(subtransactions=True):
            session.delete(model)
            session.flush()

    def delete_batch(self, session, ids=None):
        """Batch deletes by entity ids."""
        ids = ids or []
        for id in ids:
            self.delete(session, id=id)

    def update(self, session, id, **model_kwargs):
        """Updates an entity in the database.

        :param session: A Sql Alchemy database session.
        :param model_kwargs: Entity attributes that should be updates.
        :returns: octavia.common.data_model
        """
        with session.begin(subtransactions=True):
            session.query(self.model_class).filter_by(
                id=id).update(model_kwargs)

    def get(self, session, **filters):
        """Retrieves an entity from the database.

        :param session: A Sql Alchemy database session.
        :param filters: Filters to decide which entity should be retrieved.
        :returns: octavia.common.data_model
        """
        deleted = filters.pop('show_deleted', True)
        model = session.query(self.model_class).filter_by(**filters)

        if not deleted:
            if hasattr(self.model_class, 'status'):
                model = model.filter(
                    self.model_class.status != consts.DELETED)
            else:
                model = model.filter(
                    self.model_class.provisioning_status != consts.DELETED)

        model = model.first()

        if not model:
            return None

        return model.to_data_model()

    def get_all(self, session, pagination_helper=None,
                query_options=None, **filters):

        """Retrieves a list of entities from the database.

        :param session: A Sql Alchemy database session.
        :param pagination_helper: Helper to apply pagination and sorting.
        :param query_options: Optional query options to apply.
        :param filters: Filters to decide which entities should be retrieved.
        :returns: [octavia.common.data_model]
        """
        deleted = filters.pop('show_deleted', True)
        query = session.query(self.model_class).filter_by(**filters)
        if query_options:
            query = query.options(query_options)

        if not deleted:
            if hasattr(self.model_class, 'status'):
                query = query.filter(
                    self.model_class.status != consts.DELETED)
            else:
                query = query.filter(
                    self.model_class.provisioning_status != consts.DELETED)

        if pagination_helper:
            model_list, links = pagination_helper.apply(
                query, self.model_class)
        else:
            links = None
            model_list = query.all()

        data_model_list = [model.to_data_model() for model in model_list]
        return data_model_list, links


    def exists(self, session, id):
        """Determines whether an entity exists in the database by its id.

        :param session: A Sql Alchemy database session.
        :param id: id of entity to check for existence.
        :returns: octavia.common.data_model
        """
        return bool(session.query(self.model_class).filter_by(id=id).first())

    def get_all_deleted_expiring(self, session, exp_age):
        """Get all previously deleted resources that are now expiring.

        :param session: A Sql Alchemy database session.
        :param exp_age: A standard datetime delta which is used to see for how
                        long can a resource live without updates before
                        it is considered expired
        :returns: A list of resource IDs
                """

        expiry_time = datetime.datetime.utcnow() - exp_age

        query = session.query(self.model_class).filter(
            self.model_class.updated_at < expiry_time)
        if hasattr(self.model_class, 'status'):
            query = query.filter_by(status=consts.DELETED)
        else:
            query = query.filter_by(operating_status=consts.DELETED)
        # Do not load any relationship
        query = query.options(noload('*'))
        model_list = query.all()

        id_list = [model.id for model in model_list]
        return id_list


class VThunderRepository(BaseRepository):
    model_class = models.VThunder

    def getVThunderFromLB(self, session, lb_id):
        model = session.query(self.model_class).filter(
            self.model_class.loadbalancer_id == lb_id).first()

        if not model:
            return None

        return model.to_data_model()

    def getVThunderByProjectID(self, session, project_id):
        model = session.query(self.model_class).filter(
            self.model_class.project_id == project_id).first()


        if not model:
            return None

        return model.to_data_model()

    def getDeleteComputeFlag(self, session, compute_id):
        count = session.query(self.model_class).filter(
            self.model_class.compute_id == compute_id).count()
       
        if count < 2:
            return True

        else:
            return False          
