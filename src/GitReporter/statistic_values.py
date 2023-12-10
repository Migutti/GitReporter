import copy

from .types import GitCommitStatisticCategory as CommitCategory, GitLineCategory as LineCategory, \
    GitRepositoryStatisticCategory as RepoCategory


EMPTY_COMMIT_VALUE = {
    LineCategory.EMPTY: 0,
    LineCategory.SYMBOLS_ONLY: 0,
    LineCategory.CODE: 0,
    LineCategory.COMMENT: 0,
    LineCategory.UNKNOWN: 0
}


def empty_value():
    return copy.deepcopy(EMPTY_COMMIT_VALUE)


class GitCommitStatisticValues(dict):
    def __init__(self, insertions, deletions, modifications):
        dict.__init__(self, {
            CommitCategory.INSERTIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            CommitCategory.DELETIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            CommitCategory.MODIFICATIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            }
        })

        for cat in LineCategory:
            self[CommitCategory.INSERTIONS][cat] += insertions[cat]
            self[CommitCategory.DELETIONS][cat] += deletions[cat]
            self[CommitCategory.MODIFICATIONS][cat] += modifications[cat]

    def __iadd__(self, other):
        for c_category in CommitCategory:
            for l_category in LineCategory:
                self[c_category][l_category] += other[c_category][l_category]
        return self


class GitRepositoryStatisticValues(dict):
    def __init__(self, values, merge, empty=False):
        dict.__init__(self, {
            RepoCategory.SURVIVED_LINES: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            RepoCategory.INSERTIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            RepoCategory.DELETIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            RepoCategory.MODIFICATIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            RepoCategory.COMMITS: 0,
            RepoCategory.MERGE_INSERTIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            RepoCategory.MERGE_DELETIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            RepoCategory.MERGE_MODIFICATIONS: {
                LineCategory.EMPTY: 0,
                LineCategory.SYMBOLS_ONLY: 0,
                LineCategory.CODE: 0,
                LineCategory.COMMENT: 0,
                LineCategory.UNKNOWN: 0
            },
            RepoCategory.MERGE_COMMITS: 0
        })

        if merge:
            for cat in LineCategory:
                self[RepoCategory.MERGE_INSERTIONS][cat] += values[CommitCategory.INSERTIONS][cat]
                self[RepoCategory.MERGE_DELETIONS][cat] += values[CommitCategory.DELETIONS][cat]
                self[RepoCategory.MERGE_MODIFICATIONS][cat] += values[
                    CommitCategory.MODIFICATIONS][cat]
            self[RepoCategory.MERGE_COMMITS] += 1

        else:
            for cat in LineCategory:
                self[RepoCategory.INSERTIONS][cat] += values[CommitCategory.INSERTIONS][cat]
                self[RepoCategory.DELETIONS][cat] += values[CommitCategory.DELETIONS][cat]
                self[RepoCategory.MODIFICATIONS][cat] += values[CommitCategory.MODIFICATIONS][cat]
            self[RepoCategory.COMMITS] += 1

        if empty:
            self[RepoCategory.COMMITS] = 0
            self[RepoCategory.MERGE_COMMITS] = 0

    def add(self, values, merge):
        if merge:
            for cat in LineCategory:
                self[RepoCategory.MERGE_INSERTIONS][cat] += values[CommitCategory.INSERTIONS][cat]
                self[RepoCategory.MERGE_DELETIONS][cat] += values[CommitCategory.DELETIONS][cat]
                self[RepoCategory.MERGE_MODIFICATIONS][cat] += values[CommitCategory.MODIFICATIONS][cat]
            self[RepoCategory.MERGE_COMMITS] += 1

        else:
            for cat in LineCategory:
                self[RepoCategory.INSERTIONS][cat] += values[CommitCategory.INSERTIONS][cat]
                self[RepoCategory.DELETIONS][cat] += values[CommitCategory.DELETIONS][cat]
                self[RepoCategory.MODIFICATIONS][cat] += values[CommitCategory.MODIFICATIONS][cat]
            self[RepoCategory.COMMITS] += 1

    def __iadd__(self, other):
        for r_category in RepoCategory:
            if r_category is RepoCategory.COMMITS or r_category is RepoCategory.MERGE_COMMITS:
                self[r_category] += other[r_category]
            else:
                for l_category in LineCategory:
                    self[r_category][l_category] += other[r_category][l_category]
        return self

    def get_sum(self, category):
        sum = 0
        for cat in LineCategory:
            sum += self[category][cat]
        return sum
