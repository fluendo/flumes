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

from . import __version__
from .config import Config
from .options import Options
from .schema import (
    Audio,
    Container,
    Field,
    File,
    Info,
    Meta,
    Schema,
    Stream,
    Subtitle,
    Tag,
    Video,
)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DiscovererOptions(Options):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = self.add_argument_group("discovery")
        group.add_argument(
            "-q", "--quit", action="store_true", default=False, help="Quit after scan"
        )
        group.add_argument(
            "-d", "--dir", action="store", help="media content directory"
        )
        group.add_argument(
            "-f", "--force", action="store_true", default=False, help="force rescanning"
        )


class Discoverer(object):
    def __init__(self, config, args):
        Gst.init()

        self.config = config
        self.loop = GLib.MainLoop()
        self.quit = args.quit
        self.dir = args.dir
        self.force = args.force
        schema = Schema(config)
        self.session = schema.create_session()
        # TODO Set the logging level
        # Write down the Meta table
        meta = self.session.query(Meta).one_or_none()
        if not meta:
            meta = Meta()
            meta.version = __version__
            meta.root = self.dir
            self.session.add(meta)
        else:
            meta.version = __version__
        self.session.commit()
        # TODO Check in case we have provided a different folder
        # Start analyzing the provided media path
        self.path = Gio.File.new_for_path(self.dir)
        # Add a monitor
        self.monitor = self.path.monitor_directory(0, None)
        self.monitor.connect("changed", self.on_changed)
        self.discoverer = GstPbutils.Discoverer.new(5 * Gst.SECOND)
        self.discoverer.connect("discovered", self.on_discovered)
        self.discoverer.connect("finished", self.on_finished)
        self.numdiscoveries = 0
        self.discoverer.start()
        # Iterate over the files in the directory
        self.numdirs = 1
        self.path.enumerate_children_async(
            "*",
            Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
            0,
            None,
            self.on_directory_content,
            None,
        )

    def _has_gst_override(self):
        # FIXME we need python3-gst-1.0 package to be installed in the virtualenv for
        # unknown types (overrides). Sadly there is no pip package for it.
        spec = importlib.util.find_spec("gi.overrides.Gst")
        if spec:
            return True
        else:
            return False

    def _parse_type_value(self, s):
        fields = s.split(",")
        if len(fields) > 1:
            regex = r"(?P<key>[\w-]*)\=\((?P<type>\w+)\)[\"]?(?P<value>[\w -\\]*)[\"]?"
            regex_c = re.compile(regex)
            # Remove trailing semicolon
            for field in fields[1:-1] + [fields[-1][:-1]]:
                groups = re.match(regex_c, field.strip())
                yield (groups.group("key"), groups.group("type"), groups.group("value"))

    def rel_path(self, path):
        rel_path = os.path.relpath(path, self.path.get_path())
        (dirname, basename) = os.path.split(rel_path)
        return (dirname, basename)

    def discover_file(self, path, mtime):
        (dirname, basename) = self.rel_path(path)
        (exists, needs_update) = self.file_stat(basename, dirname, mtime)
        if not exists:
            # Fill the File information
            self.add_file(basename, dirname, mtime)
        if needs_update or self.force:
            # Start discovering
            uri = "file://{}".format(path)
            logger.debug(
                "Discovering {} (numdiscoveries: {})".format(uri, self.numdiscoveries)
            )
            self.numdiscoveries += 1
            self.discoverer.discover_uri_async(uri)

    def on_changed(self, monitor, f, of, event_type):
        logger.debug(
            "A change of type {} happened in the media directory".format(event_type)
        )
        if event_type == Gio.FileMonitorEvent.CREATED:
            logger.debug("File {} created".format(f.get_path()))
            finfo = f.query_info(Gio.FILE_ATTRIBUTE_TIME_MODIFIED, 0, None)
            mtime = dateutil.parser.parse(
                finfo.get_modification_date_time().format_iso8601()
            )
            self.discover_file(f.get_path(), mtime)
        elif event_type == Gio.FileMonitorEvent.DELETED:
            logger.debug("File {} deleted".format(f.get_path()))
            (dirname, basename) = self.rel_path(f.get_path())
            db_file = self.get_file(basename, dirname)
            self.session.delete(db_file)

    def discovery_done(self):
        self.numdiscoveries -= 1
        if not self.numdiscoveries:
            logger.debug("No more discoveries")
        self.check_quit()

    def dir_done(self):
        self.numdirs -= 1
        if not self.numdirs:
            logger.debug("No more dirs")
        self.check_quit()

    def check_quit(self):
        if not self.numdirs and not self.numdiscoveries and self.quit:
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

    def store_stream_tags(self, db_stream, tags):
        def store_tag(tl, tag, *user_data):
            (copied, value) = Gst.TagList.copy_value(tl, tag)
            if copied:
                db_tag = Tag(stream=db_stream)
                db_tag.name = tag
                db_tag.value = Gst.value_serialize(value)
                self.session.add(db_tag)

        found = self._has_gst_override()
        if found:
            tags.foreach(store_tag, None)
        else:
            for (key, t, value) in self._parse_type_value(tags.to_string()):
                db_tag = Tag(stream=db_stream)
                db_tag.name = key
                db_tag.value = value
                self.session.add(db_tag)

    def store_structure(self, db_stream, s):
        def store_field(field_id, value, _unused):
            # Add every GstStructure field
            db_field = Field(stream=db_stream)
            db_field.name = GLib.quark_to_string(field_id)
            db_field.value = Gst.value_serialize(value)
            self.session.add(db_field)
            return True

        found = self._has_gst_override()
        if found:
            s.foreach(store_field, None)
        else:
            for (key, t, value) in self._parse_type_value(s.to_string()):
                db_field = Field(stream=db_stream)
                db_field.name = key
                db_field.value = value
                self.session.add(db_field)

    def store_stream_info(self, db_info, sinfo, parent=None):
        if not sinfo:
            return

        # Add the stream
        if sinfo.__gtype__.name == "GstDiscovererContainerInfo":
            db_stream = Container(info=db_info)
        elif sinfo.__gtype__.name == "GstDiscovererVideoInfo":
            db_stream = Video(info=db_info)
            db_stream.bitrate = sinfo.get_bitrate()
            db_stream.depth = sinfo.get_depth()
            db_stream.framerate_denom = sinfo.get_framerate_denom()
            db_stream.framerate_num = sinfo.get_framerate_num()
            db_stream.height = sinfo.get_height()
            db_stream.max_bitrate = sinfo.get_max_bitrate()
            db_stream.par_denom = sinfo.get_par_denom()
            db_stream.par_num = sinfo.get_par_num()
            db_stream.width = sinfo.get_width()
            db_stream.is_image = sinfo.is_image()
            db_stream.is_interlaced = sinfo.is_interlaced()
        elif sinfo.__gtype__.name == "GstDiscovererAudioInfo":
            db_stream = Audio(info=db_info)
            db_stream.channel_mask = sinfo.get_channel_mask()
            db_stream.channels = sinfo.get_channels()
            db_stream.sample_rate = sinfo.get_sample_rate()
            db_stream.bitrate = sinfo.get_bitrate()
            db_stream.max_bitrate = sinfo.get_max_bitrate()
            db_stream.sample_rate = sinfo.get_sample_rate()
            db_stream.depth = sinfo.get_depth()
            db_stream.language = sinfo.get_language()
        elif sinfo.__gtype__.name == "GstDiscovererSubtitleInfo":
            db_stream = Subtitle(info=db_info)
            db_stream.language = sinfo.get_language()
        elif sinfo.__gtype__.name == "GstDiscovererStreamInfo":
            db_stream = Stream(info=db_info)

        # Common fields
        if parent:
            parent.children.append(db_stream)
        s = sinfo.get_caps().get_structure(0)
        db_stream.media_type = s.get_name()
        self.session.add(db_stream)
        # Now the fields
        self.store_structure(db_stream, s)

        # Now the tags
        tags = sinfo.get_tags()
        if tags:
            self.store_stream_tags(db_stream, tags)

        next_sinfo = sinfo.get_next()
        if next_sinfo:
            self.store_stream_info(db_info, next_sinfo)
        elif sinfo.__gtype__.name == "GstDiscovererContainerInfo":
            for s in sinfo.get_streams():
                self.store_stream_info(db_info, s, db_stream)

    def on_discovered(self, discoverer, info, error):
        logger.debug("Discovered {}".format(info.get_uri()))
        if not info:
            self.discovery_done()
            return

        if error:
            logger.error("With error {}".format(error))

        path = urlparse(info.get_uri()).path
        (dirname, basename) = self.rel_path(path)

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
        self.session.query(Stream).filter(Stream.info_id == db_info.id).delete()
        self.session.commit()

        sinfo = info.get_stream_info()
        self.store_stream_info(db_info, sinfo)

        # Finally commit
        self.session.commit()
        self.discovery_done()

    def on_finished(self, discoverer):
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
                path = os.path.join(enum.get_container().get_path(), f.get_name())
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
                path = os.path.join(enum.get_container().get_path(), f.get_name())
                mtime = dateutil.parser.parse(
                    f.get_modification_date_time().format_iso8601()
                )
                self.discover_file(path, mtime)

        enum.next_files_async(1, 0, None, self.on_file_found, None)

    def on_directory_content(self, path, res, user_data):
        enum = path.enumerate_children_finish(res)
        enum.next_files_async(1, 0, None, self.on_file_found, None)

    def start(self):
        self.loop.run()

    def stop(self):
        self.discoverer.stop()
        self.loop.quit()


def run():
    options = DiscovererOptions()
    args = options.parse_args()
    # Read the config file
    config = Config(args)
    discoverer = Discoverer(config, args)
    discoverer.start()
