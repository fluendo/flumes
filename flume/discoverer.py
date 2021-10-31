#!/usr/bin/env python

import datetime
import logging
import os
import sys
from datetime import timezone
from urllib.parse import urlparse

import dateutil.parser
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstPbutils", "1.0")
from config import Config
from gi.repository import Gio, GLib, Gst, GstPbutils
from options import Options
from schema import File, Info, Schema

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Discoverer(object):
    def __init__(self, config):
        Gst.init()

        self.config = config
        self.loop = GLib.MainLoop()
        schema = Schema(config)
        self.session = schema.create_session()
        # Set the logging level

        # Start analyzing the provided media path
        path = Gio.File.new_for_path(self.config.get_media_files_directory())
        self.discoverer = GstPbutils.Discoverer.new(5 * Gst.SECOND)
        self.discoverer.connect("discovered", self.on_discovered)
        self.discoverer.connect("finished", self.on_finished)
        self.discoverer.start()
        # Iterate over the files in the directory
        path.enumerate_children_async(
            "*",
            Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS,
            0,
            None,
            self.on_directory_content,
            None,
        )

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
        f = File(name=name, path=path, mtime=mtime)
        self.session.add(f)
        self.session.commit()
        return f

    def get_file(self, name, path):
        f = self.session.query(File).filter_by(name=name, path=path).first()
        return f

    def on_discovered(self, discoverer, info, error, *user_data):
        logger.debug("Discovered {}".format(info.get_uri()))
        if not info:
            return

        if error:
            logger.error("With error {}".format(error))

        path = urlparse(info.get_uri()).path
        rel_path = os.path.relpath(path, self.config.get_media_files_directory())
        (dirname, basename) = os.path.split(rel_path)

        result = info.get_result()
        f = self.get_file(basename, dirname)
        finfo = f.info
        if not finfo:
            finfo = Info(file=f)
            self.session.add(finfo)
        finfo.duration = info.get_duration()
        finfo.live = info.get_live()
        finfo.seekable = info.get_seekable()
        # TODO Add the streams
        # TODO Add the tags
        self.session.commit()

    def on_finished(self, discoverer, *user_data):
        logger.debug("Finished")

    def on_file_found(self, enum, res, user_data):
        files = enum.next_files_finish(res)
        if not files:
            return

        for f in files:
            file_type = f.get_file_type()
            if file_type == Gio.FileType.DIRECTORY:
                # recurse
                path = "{}/{}".format(enum.get_container().get_path(), f.get_name())
                subdir = Gio.File.new_for_path(path)
                logger.debug("Recursing {}".format(path))
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
                    logger.debug("Discovering {}".format(uri))
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


def main(argv):
    options = Options()
    args = options.parse_args(argv)
    # Read the config file
    config = Config(args)
    discoverer = Discoverer(config)
    discoverer.start()


if __name__ == "__main__":
    main(sys.argv[1:])
