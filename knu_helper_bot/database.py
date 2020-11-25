
import logging

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import config

logger = logging.getLogger(__name__)


db = create_engine()
base = declarative_base()

meta = MetaData(db)


