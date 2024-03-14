from git import Repo
from .commit import GitCommit, GitCommitStatus
from .config import Config
from .diff import GitDiff
from .report import Report
from .repository_statistic import GitRepositoryStatistic
from .progressbar import ProgressBar


class GitRepository:
    def __init__(self, config: Config):
        self.repo_path = config.options["repo"]
        self.repo: Repo = Repo(self.repo_path)
        self.branch = config.options["branch"]
        self.repo.git.checkout(self.branch)
        self.commit_list = self.create_commit_list()
        self.statistics = GitRepositoryStatistic(config)
        self.config = config

    def trim_by_whitelist(self, files):
        if not self.config.options["file-whitelist"]:
            return files
        nice_files = []
        for file in files:
            for ending in self.config.options["file-whitelist"]:
                if file[1].endswith(ending):
                    nice_files.append(file)
                    break
        return nice_files

    def create_commit_list(self):
        """
        Creates a list of all commits and calculates how many children every single commit has.
        """
        commits = [GitCommit(commit) for commit in self.repo.iter_commits(self.branch)]

        for git_commit_child in commits:
            for parent in git_commit_child.commit.parents:
                found_parent = False

                for git_commit_parent in commits:
                    if parent.binsha == git_commit_parent.commit.binsha:
                        git_commit_parent.add_child()
                        git_commit_child.add_parent(git_commit_parent)
                        found_parent = True

                assert found_parent, "Could not find a parent, although it must exist"

        return commits

    def split_git_output(self, files_raw):
        if len(files_raw) == 1 and not len(files_raw[0]):
            return []
        files = []
        for f in files_raw:
            split_f = f.split('\t')
            files.append(split_f)
        return files

    def update_commit(self, commit: GitCommit, progress_bar: ProgressBar):
        """
        For a given commit, this function creates a mapping from each line of every file to the corresponding commit.
        This is done with a dynamic programming approach, such that every parent commit has to be considered only once.
        """
        commit.remaining_children -= 1
        if commit.status == GitCommitStatus.VISITED:
            return
        commit.status = GitCommitStatus.VISITED

        if not commit.parents:
            files = self.split_git_output(self.repo.git.show(commit.commit, '--pretty=', '--name-status').split('\n'))
            files = self.trim_by_whitelist(files)
            for file in files:
                assert file[0] == 'A', "newly created file is treated not as added..."
                commit.add_file(file[1], self.repo.git.show(f'{commit.commit}:{file[1]}'), self.config,
                                add_too=True)

            diff = GitDiff(None, commit, self.config)
            diff.create_diff()
            progress_bar.increment()
            return

        for parent in commit.parents:
            self.update_commit(parent, progress_bar)

        if len(commit.parents) == 1:
            files = self.split_git_output(self.repo.git.diff(commit.parents[0].commit, commit.commit,
                                                             "--name-status", "--no-renames").split('\n'))
            files = self.trim_by_whitelist(files)
            commit.update_files(commit.parents[0], files)
            for file in files:
                if file[0] == 'A' or file[0] == 'M':
                    commit.add_file(file[1], self.repo.git.show(f'{commit.commit}:{file[1]}'), self.config)

            diff = GitDiff(commit.parents[0], commit, self.config)
            diff.create_diff()
            progress_bar.increment()
            return

        assert len(commit.parents) == 2, "we dont want to merge three commits..."
        files_parent_1 = self.split_git_output(self.repo.git.diff(commit.parents[0].commit, commit.commit,
                                                                  "--name-status", "--no-renames").split('\n'))
        files_parent_1 = self.trim_by_whitelist(files_parent_1)
        files_parent_2 = self.split_git_output(self.repo.git.diff(commit.parents[1].commit, commit.commit,
                                                                  "--name-status", "--no-renames").split('\n'))
        files_parent_2 = self.trim_by_whitelist(files_parent_2)

        files_to_update = commit.update_files_merge(commit.parents[0], files_parent_1, commit.parents[1],
                                                    files_parent_2)

        for file in files_to_update:
            commit.add_file(file, self.repo.git.show(f'{commit.commit}:{file}'), self.config)

        diff = GitDiff(commit.parents[0], commit, self.config, commit.parents[1], )
        diff.create_diff()
        progress_bar.increment()
        return

    def analyze(self):
        if self.config.options["hard-end-date"]:
            self.commit_list = [commit for commit in self.commit_list if commit.commit.committed_datetime <=
                                self.config.options["hard-end-date"]]

        assert self.commit_list, "no commits could be found in this repository before hard end date..."
        start_commit = self.commit_list[0]

        with ProgressBar('Processing Commits', len(self.commit_list)) as progress_bar:
            self.update_commit(start_commit, progress_bar)

    def create_report(self):
        self.statistics.add_commits(self.commit_list)
        self.statistics.survived_lines(self.commit_list)

        report = Report(self.config, self.statistics, self.commit_list)
        report.create()
