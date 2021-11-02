from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, declared_attr, relationship, sessionmaker

Base = declarative_base()


class Schema(object):
    def __init__(self, config):
        # Get the database configuration
        db_uri = config.get_database_uri()
        # Create, if needed, the database
        self.engine = create_engine(db_uri)
        # TODO Check for pending migrations
        Base.metadata.create_all(self.engine)
        self.sessionmaker = sessionmaker(bind=self.engine)

    def create_session(self):
        return self.sessionmaker()

    def get_structs(self):
        return ["file", "info"]

    def get_structs_cls(self):
        return [File, Info]


class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    path = Column(String)
    mtime = Column(DateTime)

    info = relationship("Info", uselist=False, back_populates="file")


class Info(Base):
    __tablename__ = "infos"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"))

    duration = Column(Integer)
    seekable = Column(Boolean)
    live = Column(Boolean)
    audio_streams = Column(Integer)
    video_streams = Column(Integer)
    subtitle_streams = Column(Integer)

    file = relationship("File", back_populates="info")
    streams = relationship("Stream", back_populates="info")


class Stream(Base):
    __tablename__ = "streams"
    id = Column(Integer, primary_key=True)

    info_id = Column(Integer, ForeignKey("infos.id"))
    media_type = Column(String)
    type = Column(String)

    info = relationship("Info", back_populates="streams")
    fields = relationship("Field", back_populates="stream")

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

    stream_id = Column(Integer, ForeignKey("streams.id"))

    name = Column(String)
    value = Column(String)

    stream = relationship("Stream", back_populates="fields")
