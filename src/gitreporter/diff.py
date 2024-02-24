from .commit import GitCommit
from difflib import SequenceMatcher
from .commit_statistic import GitCommitStatistic
from .statistic_values import empty_value
from .config import Config
from .textline import Textline


class GitDiff:
    def __init__(self, commit_a, commit_b: GitCommit, config, commit_a2 = None):
        self.commit_a: GitCommit = commit_a
        self.commit_b: GitCommit = commit_b
        self.commit_a2 = commit_a2
        self.config: Config = config

    def compute_similarity(self, left, right):
        s = SequenceMatcher(a=left, b=right, autojunk=False)
        return s.ratio()

    def compute_matched_lines(self, blocks, a, b, transfer_history, active_threshold):
        a_matched_lines = []
        b_matched_lines = []
        for block in blocks:
            """
            check minimum threshold for moved lines if recursion is applied
            """
            if active_threshold and block.size < self.config.options["diff-recursion-block-size-threshold"]:
                continue

            a_matched_lines += [i for i in range(block.a, block.a + block.size)]
            b_matched_lines += [i for i in range(block.b, block.b + block.size)]

            """
            Transfer history of the text lines
            """
            if transfer_history:
                for i in range(block.a, block.a + block.size):
                    b[i - block.a + block.b].history = a[i].history

        return a_matched_lines, b_matched_lines

    def lines_minus_matched_lines(self, text, matched_lines):
        result = []
        for i in range(len(text)):
            if i not in matched_lines:
                result.append(text[i])
        return result

    def compute_unmatched_lines(self, a: list, b: list, transfer_history=False, across_files=False):
        for i in range(self.config.options["diff-recursion-depth"]):
            s = SequenceMatcher(a=a, b=b, autojunk=False)
            blocks = s.get_matching_blocks()

            a_matched_lines, b_matched_lines = self.compute_matched_lines(blocks, a, b, transfer_history,
                                                                          across_files or i > 0)
            a = self.lines_minus_matched_lines(a, a_matched_lines)
            b = self.lines_minus_matched_lines(b, b_matched_lines)

        return a, b

    def compute_modifications(self, a: list, b: list):
        deletions = []
        insertions = []
        ins_mod = []
        modifications = []

        for b_line in b:
            if b_line.length_wo_whitespace() < self.config.options["modification-minimum-line-length"]:
                insertions.append(b_line)
            else:
                ins_mod.append(b_line)

        for a_line in a:
            if a_line.length_wo_whitespace() < self.config.options["modification-minimum-line-length"]:
                deletions.append(a_line)
                continue

            for i in range(len(ins_mod)):
                similarity = self.compute_similarity(a_line.to_string(), ins_mod[i].to_string())
                if similarity >= self.config.options["modification-similarity"]:
                    ins_mod[i].add_history(a_line.history)
                    ins_mod = ins_mod[:i] + ins_mod[i+1:]
                    modifications.append(a_line)
                    break
            else:
                deletions.append(a_line)

        return deletions, insertions + ins_mod, modifications

    def handle_modified_files(self, filename, commit):
        self.commit_b.files[filename].add_history(commit.files[filename].history)
        deletions, insertions = self.compute_unmatched_lines(list(commit.files[filename].lines),
                                                             list(self.commit_b.files[filename].lines),
                                                             transfer_history=True)
        if not self.config.options['allow-modifications']:
            self.commit_b.statistics.add_file(
                filename=filename,
                insertions=Textline.evaluate_lines(insertions),
                deletions=Textline.evaluate_lines(deletions),
                modifications=empty_value()
            )
        else:
            deletions, insertions, modifications = self.compute_modifications(deletions, insertions)
            self.commit_b.statistics.add_file(
                filename=filename,
                insertions=Textline.evaluate_lines(insertions),
                deletions=Textline.evaluate_lines(deletions),
                modifications=Textline.evaluate_lines(modifications)
            )

    def compute_diff(self):
        """
        compute the diff, without considering diffs between different files
        """

        for file in self.commit_b.added_files:
            self.commit_b.statistics.add_file(
                filename=file,
                insertions=Textline.evaluate_lines(self.commit_b.files[file].lines),
                deletions=empty_value(),
                modifications=empty_value()
            )

        for file in self.commit_b.deleted_files:
            self.commit_b.statistics.add_file(
                filename=file,
                insertions=empty_value(),
                deletions=Textline.evaluate_lines(self.commit_a.files[file].lines),
                modifications=empty_value()
            )

        for filename in self.commit_b.modified_files:
            self.handle_modified_files(filename, self.commit_a)

        if self.commit_a2:
            for file in self.commit_b.deleted_files_p2:
                self.commit_b.statistics.add_file(
                    filename=file,
                    insertions=Textline.evaluate_lines(self.commit_a2.files[file].lines),
                    deletions=empty_value(),
                    modifications=empty_value()
                )

            for filename in self.commit_b.modified_files_p2:
                self.handle_modified_files(filename, self.commit_a2)

        for filename in self.commit_b.merge_files:
            self.commit_b.files[filename].merge_histories(self.commit_a.files[filename].history,
                                                          self.commit_a2.files[filename].history)
            parent_1_unmatched_lines, child_p1_unmatched_lines = \
                self.compute_unmatched_lines(list(self.commit_a.files[filename].lines),
                                             list(self.commit_b.files[filename].lines),
                                             transfer_history=True)

            parent_2_unmatched_lines, _ = \
                self.compute_unmatched_lines(list(self.commit_a2.files[filename].lines),
                                             list(self.commit_b.files[filename].lines))

            """
            # compute insertions iteratively
            """
            _, insertions = \
                self.compute_unmatched_lines(list(self.commit_a2.files[filename].lines),
                                             list(child_p1_unmatched_lines),
                                             transfer_history=True)

            """
            # deletions are the symmetric difference of parent_1 and parent_2
            """
            parent_1_deletions, parent_2_deletions = \
                self.compute_unmatched_lines(list(parent_1_unmatched_lines), list(parent_2_unmatched_lines))

            self.commit_b.statistics.add_file(
                filename=filename,
                insertions=Textline.evaluate_lines(insertions),
                deletions=Textline.evaluate_lines(parent_1_deletions + parent_2_deletions),
                modifications=empty_value()
            )

    def create_diff(self):
        """
        basic diff, w/o any preprocessing or postprocessing of input / diff
        """
        self.commit_b.statistics = GitCommitStatistic()
        self.compute_diff()
