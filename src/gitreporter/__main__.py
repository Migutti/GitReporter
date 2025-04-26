import sys
import copy
import json
import argparse

from .config import Config, ConfigException
from .repository import GitRepository

ARGUMENT_DESCRIPTION = \
"""
Sample usages:
- Create a default configuration file:
    gitreporter -c CONFIG --create-config
- Use a configuration file:
    gitreporter -c CONFIG
- Use command line arguments (see below):
    gitreporter -r REPO -b BRANCH [<options>]
"""

def parse_arguments() -> dict:
    parser = argparse.ArgumentParser(
        prog="gitreporter",
        description=ARGUMENT_DESCRIPTION,
        usage="gitreporter [-h] | [-c CONFIG --create-config] | [-c CONFIG] | <options>",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-c",
        help="path to configuration file, overwrites all other settings",
        dest="config"
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="create a configuration file, stores it in the config path",
        dest="create-config"
    )

    # repository settings
    parser.add_argument(
        "-r",
        help="path to the git repository",
        dest="repo"
    )
    parser.add_argument(
        "-b",
        help="branch that should be analysed",
        dest="branch"
    )

    # author, file and date settings
    parser.add_argument(
        "--author-whitelist",
        nargs="+",
        help="only commits from these authors will be considered",
        dest="author-whitelist"
    )
    parser.add_argument(
        "--author-blacklist",
        nargs="+",
        help="commits from these authors will be ignored",
        dest="author-blacklist"
    )
    parser.add_argument(
        "--file-ending-whitelist",
        nargs="+",
        help="only files with these endings will be considered",
        dest="file-whitelist"
    )
    parser.add_argument(
        "--start-date",
        help="start date for the analysis",
        dest="start-date"
    )
    parser.add_argument(
        "--end-date",
        help="end date for the analysis, overall last commit is used as basis",
        dest="end-date"
    )
    parser.add_argument(
        "--hard-end-date",
        help="hard end date for the analysis, no commits after this date will be considered",
        dest="hard-end-date"
    )

    # analysis settings
    parser.add_argument(
        "--diff-recursion-depth",
        type=int,
        help="how many times the diff should be recursively analyzed",
        dest="diff-recursion-depth"
    )
    parser.add_argument(
        "--diff-recursion-block-size-threshold",
        type=int,
        help="minimum size of a block to be considered for recursive diff",
        dest="diff-recursion-block-size-threshold"
    )
    parser.add_argument(
        "--allow-modifications",
        action="store_true",
        help="allow modifications of existing code",
        dest="allow-modifications"
    )
    parser.add_argument(
        "--modification-similarity",
        type=float,
        help="similarity threshold for modifications",
        dest="modification-similarity"
    )
    parser.add_argument(
        "--modification-minimum-line-length",
        type=int,
        help="minimum line length for modifications",
        dest="modification-minimum-line-length"
    )
    parser.add_argument(
        "--comments-and-coding-standard",
        action="store_true",
        help="check for comments and coding standard (currently only supported for c-like languages)",
        dest="comments-and-coding-standard"
    )

    # report settings
    parser.add_argument(
        "--json",
        action="store_true",
        help="output the report in json format",
        dest="json"
    )

    return vars(parser.parse_args(sys.argv[1:] if len(sys.argv) > 1 else ["-h"]))

def main():
    print("GitReporter 0.2.12")

    args = parse_arguments()
    if args["create-config"]:
        if not args["config"]:
            print("error: specify a path to the configuration file with -c.")
            exit(-1)
        try:
            with open(args["config"], "w", encoding='utf-8') as f:
                json.dump(Config.DEFAULT_CONFIG, f, indent=4)
        except:
            print("error: could not create configuration file.")
            exit(-1)
        print(f"created configuration file at {args['config']}")
        exit(0)

    options = copy.copy(Config.DEFAULT_CONFIG)
    if args["config"]:
        try:
            with open(args["config"], "r", encoding='utf-8') as f:
                config_file = json.load(f)
        except:
            print("error: could not open configuration file.")
            exit(-1)

        for key, value in config_file.items():
            if key not in options:
                print(f"error: invalid option in config file: {key}")
                exit(-1)
            options[key] = value

    for key, value in args.items():
        if value is None or value == False or key in ['config', 'create-config']:
            continue
        options[key] = value

    try:
        config = Config(options)
    except ConfigException as e:
        print(e)
        exit(-1)

    git_repo = GitRepository(config)
    git_repo.analyze()
    git_repo.create_report()

    return 0

if __name__ == "__main__":
    main()
