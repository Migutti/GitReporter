from .config import Config, ConfigException
from .repository import GitRepository

def main():
    """
    python -m gitreporter [-h] -c CONFIG [-b BRANCH]
    """
    try:
        config = Config(read_cli_args=True)
    except ConfigException as e:
        print(e)
        return 1

    git_repo = GitRepository(config)
    git_repo.analyze()
    git_repo.create_report()

    return 0
