from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Schema(object):
    def __init__(self, config):
        # Get the database configuration
        db_uri = config.get_database_uri()
        db_user = config.get_database_user()
        db_password = config.get_database_password()

        # TODO Set the SQL server user/password if tey are separetly
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

    info = relationship("Info", back_populates="streams")
    fields = relationship("Field", back_populates="stream")


class Field(Base):
    __tablename__ = "fields"
    id = Column(Integer, primary_key=True)

    stream_id = Column(Integer, ForeignKey("streams.id"))

    name = Column(String)
    value = Column(String)

    stream = relationship("Stream", back_populates="fields")
