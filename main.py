from src.GitReporter.repository import GitRepository
from src.GitReporter.config import Config, ConfigException


def main():
    """
    python main.py [-h] -c CONFIG [-b BRANCH]
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


if __name__ == '__main__':
    exit(main())
