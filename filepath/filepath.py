import datetime
import os
import random as rnd
import re
import shutil
import logging
import subprocess
from enum import Enum


class SortOrder(Enum):
    """
    Different sorting orders for the LS function
    """
    RANDOM = 1
    ORDER = 2
    DATE = 3
    ALPHA = 4


class FilePath(object):
    """
    Wrapper for files and directories
    """

    def __init__(self, mpath):
        super().__init__()
        self.mpath = mpath

    def __add__(self, other):
        """
        Concatenates two file pathes
        """
        if isinstance(other, str):
            other = FilePath(other)
        return FilePath(os.path.join(self.mpath, other.mpath))

    def ls(self, order=SortOrder.ALPHA, hourly=False):
        """
        Lists the directory a FilePath represents
        :param order: how to sort the output
        :param hourly: whether should pick one file per hour (used for debug)
        :return: list of FilePathes
        """

        mlist = os.listdir(self.mpath)

        if order == SortOrder.RANDOM:
            # random sorting (used for picking random directories)
            rnd.shuffle(mlist)
        elif order == SortOrder.ORDER:
            # order by first number in file name (for debug)
            mlist.sort(key=lambda e: int(re.match(r"^(\d+)_.*", os.path.basename(e)).group(1)))
        elif order == SortOrder.DATE:
            # order by the timestamp in file name (for debug)
            mlist.sort(key=lambda e: int(re.match(r"^.*_(\d+)\.json", os.path.basename(e)).group(1)))
        elif order == SortOrder.ALPHA:
            # order alphabetically
            mlist.sort()

        if hourly:
            new_res = []
            last_picked = set()
            for fn in mlist:
                ts = int(re.match(r"^.*_(\d+)\.json", os.path.basename(fn)).group(1))
                city = re.match(r"(\d+)_([a-zA-Z]+)_.*", os.path.basename(fn)).group(2)
                d = datetime.datetime.fromtimestamp(ts).replace(minute=0, second=0, microsecond=0)
                if (city, d) not in last_picked:
                    last_picked.add((city, d))
                    new_res.append(fn)
            mlist = new_res

        res = [FilePath(os.path.join(self.mpath, f)) for f in mlist]

        return res

    def ensure(self):
        """
        Ensure the directory described by this FilePath exists
        i.e. create if doesn't exist
        """
        if not os.path.exists(self.mpath):
            os.makedirs(self.mpath)

    def open(self, mode='r'):
        """
        Open the file described by this FilePath
        :return: FilePathWithHelper to be used with "with" statement
        """
        return FilePathWithHelper(self, mode)

    def rmtree(self):
        """
        Remove the directory that this FilePath represents
        """
        shutil.rmtree(self.mpath)

    def basename(self):
        """
        File/directory name of this FilePath
        """
        return os.path.basename(self.mpath)

    def path(self):
        """
        Print full path
        """
        return self.mpath

    def find_files(self):
        """
        Do an equivalent of find in bash, listing all files in a
        directory tree
        """
        for dir, subdirs, files in os.walk(self.mpath):
            dfp = fp(dir)
            for f in files:
                yield dfp + fp(f)

    def __str__(self):
        return self.path()

    def __unicode__(self):
        return self.path()


class FilePathWithHelper(object):

    def __init__(self, filepath, mode):
        super().__init__()
        self.fp = filepath
        self.mode = mode

    def __enter__(self):
        self.fd = open(self.fp.mpath, mode=self.mode)
        return self.fd

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fd.close()


def fp(mpath):
    """
    Alias for FilePath constructor
    """
    if isinstance(mpath, FilePath):
        return FilePath(mpath.mpath)
    return FilePath(mpath)
