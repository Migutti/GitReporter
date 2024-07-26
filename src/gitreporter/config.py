import copy
import json
import argparse
from datetime import datetime
from typing import Union

from .commit import GitCommit


class ConfigException(Exception):
    pass

class Config:
    DEFAULT_CONFIG = {
        "repo": ".",
        "branch": "main",
        "author-whitelist": [],
        "author-blacklist": [],
        "file-whitelist": [],
        "start-date": None,
        "end-date": None,
        "hard-end-date": None,
        "diff-recursion-depth": 2,
        "diff-recursion-block-size-threshold": 4,
        "allow-modifications": False,
        "modification-similarity": 0.8,
        "modification-minimum-line-length": 2,
        "comments-and-coding-standard": False,
        "json": False
    }

    def __init__(self, options: Union[dict, None]=None):
        self.options = options \
            if options \
            else copy.copy(self.DEFAULT_CONFIG)

        for key, value in self.options.items():
            match key:
                case "repo" | "branch":
                    if type(value) != str:
                        raise ConfigException(f"error: invalid type for {key}.")
                case "author-whitelist" | "author-blacklist" | "file-whitelist":
                    if type(value) != list:
                        raise ConfigException(f"error: invalid type for {key}.")
                case "start-date" | "end-date" | "hard-end-date":
                    if not value:
                        continue
                    try:
                        self.options[key] = datetime.fromisoformat(value)
                    except:
                        raise ConfigException(f"error: invalid datetime format: {key}.")
                case "diff-recursion-depth" | "diff-recursion-block-size-threshold" | "modification-minimum-line-length":
                    if type(value) != int and type <= 0:
                        raise ConfigException(f"error: invalid type/value for {key}.")
                case "allow-modifications" | "comments-and-coding-standard" | "json":
                    if type(value) != bool:
                        raise ConfigException(f"error: invalid type for {key}.")
                case "modification-similarity":
                    if type(value) != float and value < 0 or value > 1:
                        raise ConfigException(f"error: invalid type/value for {key}.")
                case _:
                    raise ConfigException(f"error: invalid option in config file: {key}")

    def in_time_interval(self, timestamp):
        return (not self.options["start-date"] or timestamp >= self.options["start-date"]) \
            and (not self.options["end-date"] or timestamp < self.options["end-date"])

    def check_commit_admissible(self, commit: GitCommit):
        return (not self.options["start-date"] or commit.commit.committed_datetime >= self.options["start-date"]) \
            and (not self.options["end-date"] or commit.commit.committed_datetime < self.options["end-date"]) \
            and commit.commit.author.email not in self.options["author-blacklist"] \
            and (not self.options["author-whitelist"] or commit.commit.author.email in self.options["author-whitelist"])

    def get_options_with_datetime_string(self):
        options = copy.copy(self.options)

        for setting in ["start-date", "end-date", "hard-end-date"]:
            if options[setting]:
                options[setting] = datetime.isoformat(options[setting])

        return options
