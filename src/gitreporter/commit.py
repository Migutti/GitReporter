import git

from .file import GitFile
from .textline import Textline
from .commit_statistic import GitCommitStatistic as GitCStats
import copy
from enum import Enum

class GitCommitStatus(Enum):
    UNVISITED = 0
    VISITED = 1

class GitCommit:
    def __init__(self, commit: git.Commit):
        self.commit: git.Commit = commit
        self.children = 0
        self.remaining_children = 0
        self.status = GitCommitStatus.UNVISITED
        self.parents = []

        self.files: dict[str, GitFile] = {}
        self.added_files = []
        self.copied_files = []
        self.deleted_files = []
        self.modified_files = []

        self.added_files_p2 = []
        self.copied_files_p2 = []
        self.deleted_files_p2 = []
        self.modified_files_p2 = []

        self.merge_files = []

        self.statistics: [GitCStats, None] = None

    def add_child(self):
        self.children += 1
        self.remaining_children += 1

    def add_parent(self, parent_commit):
        self.parents.append(parent_commit)

    def update_files(self, old_commit, new_files):
        """
        splitting the changes in their different types
        """
        if old_commit.remaining_children > 0:
            self.files: dict[str, GitFile] = copy.deepcopy(old_commit.files)
        else:
            self.files: dict[str, GitFile] = old_commit.files.copy()
        for f in new_files:
            assert f[0] == 'A' or f[0] == 'D' or f[0] == 'M', "unexpected mode from git"
            if f[0] == 'A':
                self.added_files.append(f[1])
                """
                elif f[0] == 'C':
                    self.copied_files.append(f[1])
                """
            elif f[0] == 'D':
                self.files.pop(f[1])
                self.deleted_files.append(f[1])
            elif f[0] == 'M':
                self.modified_files.append(f[1])
                """
                elif f[0].startswith('R'):
                    self.files.pop(f[1])
                    self.renamed_files.append(f[1:])
                """
            else:
                assert False, "copy not implemented yet..."

    def update_files_merge(self, parent_1, new_files_1, parent_2, new_files_2):
        filenames_1 = {nf[1]: nf[0] for nf in new_files_1}
        filenames_2 = {nf[1]: nf[0] for nf in new_files_2}
        for f in filenames_1:
            assert filenames_1[f] == 'A' or filenames_1[f] == 'D' or filenames_1[f] == 'M'
        for f in filenames_2:
            assert filenames_2[f] == 'A' or filenames_2[f] == 'D' or filenames_2[f] == 'M'

        if parent_1.remaining_children > 0:
            self.files: dict[str, GitFile] = copy.deepcopy(parent_1.files)
        else:
            self.files: dict[str, GitFile] = parent_1.files.copy()

        files_to_update = []
        for filename in \
                set(list(self.files.keys()) + list(parent_2.files.keys()) + list(filenames_1) + list(filenames_2)):
            if filename not in filenames_1 and filename not in filenames_2:
                if parent_2.files[filename].history[-1] not in parent_1.files[filename].history:
                    self.files[filename] = copy.deepcopy(parent_2.files[filename])
                continue
            if filename not in filenames_1 and filename in filenames_2:
                # parent_1 has the latest version
                continue
            if filename in filenames_1 and filename not in filenames_2:
                # parent_2 has the latest version
                if filenames_1[filename] == 'D':
                    self.files.pop(filename)
                else:
                    self.files[filename] = copy.deepcopy(parent_2.files[filename])
                continue
            assert filename in filenames_1 and filename in filenames_2, "WTF..."

            if filenames_1[filename] == 'A' and filenames_2[filename] == 'A':
                self.added_files.append(filename)
                files_to_update.append(filename)
                continue
            if filenames_1[filename] == 'A':
                self.modified_files_p2.append(filename)
                files_to_update.append(filename)
                continue
            if filenames_2[filename] == 'A':
                self.modified_files.append(filename)
                files_to_update.append(filename)
                continue

            if filenames_1[filename] == 'D' and filenames_2[filename] == 'D':
                if parent_2.files[filename].history[-1] not in parent_1.files[filename].history:
                    self.deleted_files_p2.append(filename)
                else:
                    self.deleted_files.append(filename)
                self.files.pop(filename)
                continue

            if filenames_1[filename] == 'M' and filenames_2[filename] == 'M':
                if parent_1.files[filename].history[-1] in parent_2.files[filename].history:
                    # diff to parent_2 (ignore parent_1)
                    self.modified_files_p2.append(filename)
                elif parent_2.files[filename].history[-1] in parent_1.files[filename].history:
                    self.modified_files.append(filename)
                else:
                    self.merge_files.append(filename)
                files_to_update.append(filename)
                continue

            assert False, "You forget one case :(..."

        return files_to_update

    def add_file(self, filename: str, file, config, add_too=False):
        if add_too:
            self.added_files.append(filename)
        self.files[filename] = GitFile(file, self.commit.binsha, config)

    def print_statistics(self):
        print(f"Commit: {self.commit.binsha.hex()}, merge: {len(self.commit.parents) > 1}")
        print(f"Author: {self.commit.author.name}")
        print(f"Message: {self.commit.message}")
        print(self.statistics)
