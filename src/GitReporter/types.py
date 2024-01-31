from enum import Enum

class GitLineCategory(str, Enum):
    CODE = "Code"
    EMPTY = "Empty"
    SYMBOLS_ONLY = "Symbols Only"
    COMMENT = "Comment"
    UNKNOWN = "Unknown"

class GitCommitStatisticCategory(str, Enum):
    INSERTIONS = "INSERTIONS"
    DELETIONS = "DELETIONS"
    MODIFICATIONS = "MODIFICATIONS"

class GitRepositoryStatisticCategory(str, Enum):
    SURVIVED_LINES = "Survived Lines"
    INSERTIONS = "Insertions"
    DELETIONS = "Deletions"
    MODIFICATIONS = "Modifications"
    COMMITS = "Commits"
    MERGE_INSERTIONS = "Merge Insertions"
    MERGE_DELETIONS = "Merge Deletions"
    MERGE_MODIFICATIONS = "Merge Modifications"
    MERGE_COMMITS = "Merge Commits"
