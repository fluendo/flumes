import datetime
import importlib
import logging
import os
import re
import sys
from datetime import timezone
from urllib.parse import urlparse

import dateutil.parser
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstPbutils", "1.0")
from gi.repository import Gio, GLib, Gst, GstPbutils

from .options import Options
from .schema import Field, File, Info, Schema, Stream

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DiscovererOptions(Options):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = self.add_argument_group("discovery")
        group.add_argument(
            "-q", "--quit", action="store_true", default=False, help="Quit after scan"
        )


class Discoverer(object):
    def __init__(self, config, args):
        Gst.init()

        self.config = config
        self.loop = GLib.MainLoop()
        self.quit = args.quit
        schema = Schema(config)
        self.session = schema.create_session()
        # TODO Set the logging level

        # Start analyzing the provided media path
        path = Gio.File.new_for_path(self.config.get_media_files_directory())
        self.discoverer = GstPbutils.Discoverer.new(5 * Gst.SECOND)
        self.discoverer.connect("discovered", self.on_discovered)
        self.discoverer.connect("finished", self.on_finished)
        self.numdiscovery = 0
        self.discoverer.start()
        # Iterate over the files in the directory
        self.numdirs = 1
        path.enumerate_children_async(
            "*",
            Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
            0,
            None,
            self.on_directory_content,
            None,
        )

    def discovery_done(self):
        self.numdiscovery -= 1
        if not self.numdirs:
            logger.debug("No more discoveries")
        self.check_quit()

    def dir_done(self):
        self.numdirs -= 1
        if not self.numdirs:
            logger.debug("No more dirs")
        self.check_quit()

    def check_quit(self):
        if not self.numdirs and not self.numdiscovery and self.quit:
            self.stop()

    def file_stat(self, name, path, mtime):
        # Check if a file exists in the database
        f = self.get_file(name, path)
        if not f:
            return (False, True)
        # Make the mtime UTC otherwise the comparison will always fail
        fmtime = f.mtime.replace(tzinfo=timezone.utc)
        return (True, fmtime != mtime)

    def add_file(self, name, path, mtime):
        logger.debug("Adding file name={} path={} mtime={}".format(name, path, mtime))
        db_file = File(name=name, path=path, mtime=mtime)
        self.session.add(db_file)
        self.session.commit()
        return db_file

    def get_file(self, name, path):
        db_file = self.session.query(File).filter_by(name=name, path=path).first()
        return db_file

    def store_structure(self, db_stream, s):
        def store_field(field_id, value, _unused):
            # Add every GstStructure field
            db_field = Field(stream=db_stream)
            db_field.name = GLib.quark_to_string(field_id)
            db_field.value = Gst.value_serialize(value)
            self.session.add(db_field)
            return True

        # FIXME we need python3-gst-1.0 package to be installed in the virtualenv for unknown types (overrides)
        found = importlib.util.find_spec("gi.overrides.Gst")
        if found:
            s.foreach(store_field, None)
        else:
            fields = s.to_string().split(",")
            if len(fields) > 1:
                regex = (
                    r"(?P<key>\w+([-]\w+)*)\=\((?P<type>\w+)\)(?P<value>\w+([-]\w+)*)"
                )
                regex_c = re.compile(regex)
                # Remove trailing semicolon
                for field in fields[1:-1] + [fields[-1][:-1]]:
                    groups = re.match(regex_c, field.strip())
                    db_field = Field(stream=db_stream)
                    db_field.name = groups.group("key")
                    db_field.value = groups.group("value")
                    self.session.add(db_field)

    def store_stream_info(self, db_info, sinfo):
        if not sinfo:
            return

        s = sinfo.get_caps().get_structure(0)
        # Add the stream
        db_stream = Stream(info=db_info)
        db_stream.media_type = s.get_name()
        self.session.add(db_stream)
        self.store_structure(db_stream, s)

        next_sinfo = sinfo.get_next()
        if next_sinfo:
            self.store_stream_info(db_info, next_sinfo)
        elif sinfo.__gtype__.name == "GstDiscovererContainerInfo":
            for s in sinfo.get_streams():
                self.store_stream_info(db_info, s)

    def on_discovered(self, discoverer, info, error, *user_data):
        logger.debug("Discovered {}".format(info.get_uri()))
        if not info:
            self.discovery_done()
            return

        if error:
            logger.error("With error {}".format(error))

        path = urlparse(info.get_uri()).path
        rel_path = os.path.relpath(path, self.config.get_media_files_directory())
        (dirname, basename) = os.path.split(rel_path)

        result = info.get_result()
        db_file = self.get_file(basename, dirname)
        db_info = db_file.info
        if not db_info:
            db_info = Info(file=db_file)
            self.session.add(db_info)

        # Common properties
        db_info.duration = info.get_duration()
        db_info.live = info.get_live()
        db_info.seekable = info.get_seekable()
        # Number of streams
        db_info.audio_streams = len(info.get_audio_streams())
        db_info.video_streams = len(info.get_video_streams())
        db_info.subtitle_streams = len(info.get_subtitle_streams())

        # Topology
        # Remove every previous stream
        db_info.streams[:] = []
        sinfo = info.get_stream_info()
        self.store_stream_info(db_info, sinfo)

        # TODO Add the tags
        self.session.commit()
        self.discovery_done()

    def on_finished(self, discoverer, *user_data):
        logger.debug("Finished")

    def on_file_found(self, enum, res, user_data):
        files = enum.next_files_finish(res)
        if not files:
            self.dir_done()
            return

        for f in files:
            file_type = f.get_file_type()
            if file_type == Gio.FileType.DIRECTORY:
                # recurse
                path = "{}/{}".format(enum.get_container().get_path(), f.get_name())
                subdir = Gio.File.new_for_path(path)
                logger.debug("Recursing {} (numdirs: {})".format(path, self.numdirs))
                self.numdirs += 1
                subdir.enumerate_children_async(
                    "*",
                    Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
                    0,
                    None,
                    self.on_directory_content,
                    None,
                )
            elif file_type == Gio.FileType.REGULAR:
                path = "{}/{}".format(enum.get_container().get_path(), f.get_name())
                rel_path = os.path.relpath(
                    path, self.config.get_media_files_directory()
                )
                (dirname, basename) = os.path.split(rel_path)
                mtime = dateutil.parser.parse(
                    f.get_modification_date_time().format_iso8601()
                )
                (exists, needs_update) = self.file_stat(basename, dirname, mtime)
                if not exists:
                    # Fill the File information
                    self.add_file(basename, dirname, mtime)
                if needs_update:
                    # Start discovering
                    uri = "file://{}".format(path)
                    logger.debug(
                        "Discovering {} (numdiscovery: {})".format(
                            uri, self.numdiscovery
                        )
                    )
                    self.numdiscovery += 1
                    self.discoverer.discover_uri_async(uri)
        enum.next_files_async(1, 0, None, self.on_file_found, None)

    def on_directory_content(self, path, res, user_data):
        enum = path.enumerate_children_finish(res)
        enum.next_files_async(1, 0, None, self.on_file_found, None)

    def start(self):
        self.loop.run()

    def stop(self):
        self.discoverer.stop()
        self.loop.quit()
