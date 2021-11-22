import os
from sqlite3 import Connection as SQLite3Connection

from alembic import command
from alembic.config import Config
from packaging.version import Version
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    create_engine,
    event,
    inspect,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, declared_attr, relationship, sessionmaker

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Base = declarative_base()
Base.metadata = MetaData(naming_convention=naming_convention)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


class Schema(object):
    def __init__(self, config):
        self.config = config
        # Get the database configuration
        db_uri = config.get_database_uri()
        # Create, if needed, the database
        self.engine = create_engine(db_uri)
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.migrate(db_uri)

    def migrate(self, db_uri):
        config = Config()
        cwd = os.path.abspath(os.path.dirname(__file__))
        config.set_main_option("script_location", os.path.join(cwd, "alembic"))
        config.set_main_option("sqlalchemy.url", db_uri)

        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        # Check if the table exists
        if "metas" in tables:
            session = self.create_session()
            meta = session.query(Meta).one_or_none()
            # Check the version in Meta
            # If version < 0.1.5, then stamp to e827c1336bb4
            if meta and Version(meta.version) < Version("0.1.5"):
                command.stamp(config, "e827c1336bb4")
        # Let alembic migrate to head, if needed
        command.upgrade(config, "head")

    def get_config(self):
        return self.config

    def create_session(self):
        return self.sessionmaker()


class Meta(Base):
    __tablename__ = "metas"
    id = Column(Integer, primary_key=True)
    version = Column(String)
    root = Column(String)


class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    path = Column(String)
    mtime = Column(DateTime)

    info = relationship(
        "Info", uselist=False, back_populates="file", cascade="all, delete-orphan"
    )


class Info(Base):
    __tablename__ = "infos"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))

    duration = Column(Integer)
    seekable = Column(Boolean)
    live = Column(Boolean)
    audio_streams = Column(Integer)
    video_streams = Column(Integer)
    subtitle_streams = Column(Integer)

    file = relationship("File", back_populates="info")
    streams = relationship(
        "Stream", back_populates="info", cascade="all, delete-orphan"
    )


class Stream(Base):
    __tablename__ = "streams"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("streams.id", ondelete="CASCADE"))

    info_id = Column(Integer, ForeignKey("infos.id", ondelete="CASCADE"))
    media_type = Column(String)
    type = Column(String)

    info = relationship("Info", back_populates="streams")
    fields = relationship(
        "Field", back_populates="stream", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", back_populates="stream", cascade="all, delete-orphan")
    children = relationship("Stream", cascade="all, delete-orphan")

    __mapper_args__ = {"polymorphic_identity": "stream", "polymorphic_on": type}


class Video(Stream):
    framerate_denom = Column(Integer)
    framerate_num = Column(Integer)
    height = Column(Integer)
    par_denom = Column(Integer)
    par_num = Column(Integer)
    width = Column(Integer)
    is_image = Column(Boolean)
    is_interlaced = Column(Boolean)

    __mapper_args__ = {
        "polymorphic_identity": "video",
    }

    # Common columns found in other stream types
    @declared_attr
    def bitrate(cls):
        return Stream.__table__.c.get("bitrate", Column(Integer))

    @declared_attr
    def max_bitrate(cls):
        return Stream.__table__.c.get("max_bitrate", Column(Integer))

    @declared_attr
    def depth(cls):
        return Stream.__table__.c.get("depth", Column(Integer))


class Audio(Stream):
    channel_mask = Column(Integer)
    channels = Column(Integer)
    sample_rate = Column(Integer)

    __mapper_args__ = {
        "polymorphic_identity": "audio",
    }

    # Common columns found in other stream types
    @declared_attr
    def bitrate(cls):
        return Stream.__table__.c.get("bitrate", Column(Integer))

    @declared_attr
    def max_bitrate(cls):
        return Stream.__table__.c.get("max_bitrate", Column(Integer))

    @declared_attr
    def depth(cls):
        return Stream.__table__.c.get("depth", Column(Integer))

    @declared_attr
    def language(cls):
        return Stream.__table__.c.get("language", Column(String))


class Subtitle(Stream):
    __mapper_args__ = {
        "polymorphic_identity": "subtitle",
    }

    # Common columns found in other stream types
    @declared_attr
    def language(cls):
        return Stream.__table__.c.get("language", Column(String))


class Container(Stream):
    __mapper_args__ = {
        "polymorphic_identity": "container",
    }


class Field(Base):
    __tablename__ = "fields"
    id = Column(Integer, primary_key=True)

    stream_id = Column(Integer, ForeignKey("streams.id", ondelete="CASCADE"))

    name = Column(String)
    value = Column(String)

    stream = relationship("Stream", back_populates="fields")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)

    stream_id = Column(Integer, ForeignKey("streams.id", ondelete="CASCADE"))

    name = Column(String)
    value = Column(String)

    stream = relationship("Stream", back_populates="tags")
