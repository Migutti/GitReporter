import copy
import json
import argparse
from datetime import datetime
from typing import Union

from .commit import GitCommit


class ConfigException(Exception):
    pass

class Config:
    def __init__(self, options: Union[dict, None]=None, read_cli_args: bool=False):
        if options:
            self.options = options  # TODO: validate options
        else:
            self.options = self.options = {
                "repo": ".",
                "branch": "main",
                "author-whitelist": [],
                "author-blacklist": [],
                "file-whitelist": [],
                "diff-recursion-depth": 1,
                "diff-recursion-block-size-threshold": 4,
                "allow-modifications": False,
                "modification-similarity": 0.8,
                "modification-minimum-line-length": 2,
                "comments-and-coding-standard": False,
                "start-date": None,
                "end-date": None,
                "hard-end-date": None
            }

        if read_cli_args:
            args = self.read_cli_arguments()

            try:
                with open(args.config[0], 'r') as f:
                    config_file = f.read()
            except OSError:
                raise ConfigException("[ERROR] Config file cannot be opened!")

            config_json = json.loads(config_file)

            if "repo" not in config_json:
                raise ConfigException("[ERROR] Config file does not specify a repository!")
            self.options["repo"] = config_json["repo"]

            for key, value in config_json.items():
                if key == "repo":
                    continue
                if key in self.options:
                    self.options[key] = value

                if key == "start-date" or key == "end-date" or key == "hard-end-date":
                    try:
                        self.options[key] = datetime.fromisoformat(value)
                    except:
                        raise ConfigException("[ERROR] Invalid datetime format!")

            if args.branch:
                self.options["branch"] = args.branch[0]

    def read_cli_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config', nargs=1, default=[], help='path to configuration file', required=True)
        parser.add_argument('-b', '--branch', nargs=1, default=[], help='branch that should be analysed')

        return parser.parse_args()

    def in_time_interval(self, timestamp):
        return (not self.options["start-date"] or timestamp >= self.options["start-date"]) \
            and (not self.options["end-date"] or timestamp < self.options["end-date"])

    def check_commit_admissible(self, commit: GitCommit):
        return (not self.options["start-date"] or commit.commit.committed_datetime >= self.options["start-date"]) \
            and (not self.options["end-date"] or commit.commit.committed_datetime < self.options["end-date"]) \
            and commit.commit.author.email not in self.options["author-blacklist"] \
            and (not self.options["author-whitelist"] or commit.commit.author.email in self.options["author-whitelist"])

    def get_options_with_datetime_string(self):
        options = copy.deepcopy(self.options)

        for setting in ["start-date", "end-date", "hard-end-date"]:
            if options[setting]:
                options[setting] = datetime.isoformat(options[setting])

        return options
