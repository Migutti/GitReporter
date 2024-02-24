from .statistic_values import GitCommitStatisticValues


class GitCommitStatistic:
    def __init__(self):
        self.file_mapping = {}

    def add_file(self, filename, insertions, deletions, modifications):
        self.file_mapping[filename] = GitCommitStatisticValues(insertions, deletions, modifications)

    """
    def ins_and_del(self):
        insertions = 0
        deletions = 0
        for _, value in self.file_mapping.items():
            insertions += value.insertions
            deletions += value.deletions
        return insertions, deletions
    """

    """
    def __repr__(self):
        str = ""
        total_ins = 0
        total_del = 0
        total_mod = 0
        for filename, value in self.file_mapping.items():
            str += f"File: {filename}\n\tIns: {value.insertions:4d} | Del: {value.deletions:4d} | Mod: " \
                   f"{value.modifications:4d}\n"
            total_ins += value.insertions
            total_del += value.deletions
            total_mod += value.modifications

        return f"Total:\n\tIns: {total_ins:4d} | Del: {total_del:4d} | Mod: {total_mod:4d}\n{str}"
    """
