import copy, json

from .statistic_values import GitRepositoryStatisticValues, GitCommitStatisticValues, empty_value
from .types import GitRepositoryStatisticCategory as RepoCategory, GitLineCategory as LineCategory

from .commit import GitCommit, GitCommitStatus


class GitRepositoryStatistic:
    def __init__(self, config):
        self.authors_per_file: dict[str, dict[str, GitRepositoryStatisticValues]] = {}
        self.authors: dict[str, GitRepositoryStatisticValues] = {}
        self.totals_per_file: dict[str, GitRepositoryStatisticValues] = {}
        self.totals: GitRepositoryStatisticValues = \
            GitRepositoryStatisticValues(
                GitCommitStatisticValues(empty_value(), empty_value(), empty_value()),
                False,
                True)
        self.config = config

    def compute_totals_per_file(self):
        self.totals_per_file: dict[str, GitRepositoryStatisticValues] = {}
        for email, file in self.authors_per_file.items():
            for filename, values in file.items():
                if filename in self.totals_per_file:
                    self.totals_per_file[filename] += values
                else:
                    self.totals_per_file[filename] = copy.deepcopy(values)

    def add_commit(self, email, commit_statistic, merge):
        cumulative_value = GitCommitStatisticValues(empty_value(), empty_value(), empty_value())

        if email not in self.authors_per_file:
            self.authors_per_file[email] = {}
            for filename, values in commit_statistic.file_mapping.items():  # type: str, GitCommitStatisticValues
                cumulative_value += values
                self.authors_per_file[email][filename] = GitRepositoryStatisticValues(values, merge)
        else:
            for filename, values in commit_statistic.file_mapping.items():  # type: str, GitCommitStatisticValues
                cumulative_value += values
                if filename in self.authors_per_file[email]:
                    self.authors_per_file[email][filename].add(values, merge)
                else:
                    self.authors_per_file[email][filename] = GitRepositoryStatisticValues(values, merge)

        if email not in self.authors:
            self.authors[email] = GitRepositoryStatisticValues(cumulative_value, merge)
        else:
            self.authors[email].add(cumulative_value, merge)
        self.totals.add(cumulative_value, merge)

    def add_commits(self, commit_list):
        for commit in commit_list:
            if self.config.check_commit_admissible(commit) and commit.status == GitCommitStatus.VISITED:
                self.add_commit(commit.commit.author.email, commit.statistics, merge=len(commit.parents) > 1)
        self.compute_totals_per_file()

    def find_author(self, binsha, commit_list):
        for commit in commit_list:
            if commit.commit.binsha == binsha:
                if self.config.check_commit_admissible(commit):
                    return commit.commit.author.email
                return None
        return None

    def survived_lines(self, commit_list):
        last_commit: GitCommit = commit_list[0]
        for filename, total in self.totals_per_file.items():
            if filename not in last_commit.files:
                continue

            file = last_commit.files[filename].lines
            for line in file:
                binsha = line.history[0]
                email = self.find_author(binsha, commit_list)

                if email is None:
                    continue

                self.totals[RepoCategory.SURVIVED_LINES][line.get_type()] += 1
                total[RepoCategory.SURVIVED_LINES][line.get_type()] += 1

                self.authors[email][RepoCategory.SURVIVED_LINES][line.get_type()] += 1
                self.authors_per_file[email][filename][RepoCategory.SURVIVED_LINES][line.get_type()] += 1

    """
    def create_json(self, write_to_file=False):
        results = {
            "Options": self.config.get_options_with_datetime_string(),
            "Totals": self.totals,
            "Totals Authors": self.authors,
            "Totals per File": self.totals_per_file,
            "Authors per File": self.authors_per_file
        }
        if write_to_file:
            with open('report.json', 'w') as f:
                f.write(json.dumps(results, indent=4))

        return results
    """
