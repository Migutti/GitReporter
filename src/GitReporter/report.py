import copy
import os

from .commit import GitCommit
from .config import Config
from .html_report import HTMLReport
from .repository_statistic import GitRepositoryStatistic
from .types import GitRepositoryStatisticCategory as RepoCategory, GitLineCategory as LineCategory


class Report:
    def __init__(self, config, statistics, commit_list):
        self.config: Config = config
        self.statistics: GitRepositoryStatistic = statistics
        self.commit_list: list[GitCommit] = commit_list
        self.idx_mapping = {}
        self.table_template = []

    @staticmethod
    def calc_percentage(a, b):
        if b != 0:
            return a / b * 100
        else:
            return 0

    def get_idx(self, email):
        if not email:
            return ""
        if email in self.idx_mapping:
            return self.idx_mapping[email]
        return ""

    def find_author(self, binsha):
        for commit in self.commit_list:
            if commit.commit.binsha == binsha:
                if self.config.in_time_interval(commit.commit.committed_datetime):
                    return commit.commit.author.email
                return None
        return None

    def create_table_template(self):
        self.table_template.append([
            "Student",
            "Line Category",
            "Survived Lines",
            "Insertions",
            "Deletions",
            "Modifications",
            "Commits",
            "Merge-Insertions",
            "Merge-Deletions",
            "Merge-Modifications",
            "Merge-Commits"
        ])
        self.table_template.append(["", "Total", "", "TOTAL"] + (9 * ["     -", "      -"]))
        for line_category in LineCategory:
            self.table_template.append(["", "", "", line_category] + (9 * ["     -", "      -"]))

        for idx, (email, value) in enumerate(self.statistics.authors.items()):
            self.idx_mapping[email] = idx
            self.table_template.append(["", email, "", "TOTAL"] + (9 * ["     -", "      -"]))
            for line_category in LineCategory:
                self.table_template.append(["", "", "", line_category] + (9 * ["     -", "      -"]))

    @staticmethod
    def abs_format(value):
        return f'{value:6d}'

    def rel_format(self, value, total):
        return f'{self.calc_percentage(value, total):5.1f} %'

    def fill_table(self, author_statistic, total_statistic):
        table = copy.deepcopy(self.table_template)

        for i, r_category in enumerate(RepoCategory):
            if r_category is RepoCategory.COMMITS or r_category is RepoCategory.MERGE_COMMITS:
                table[1][4 + 2 * i] = self.abs_format(total_statistic[r_category])
            else:
                table[1][4 + 2 * i] = self.abs_format(total_statistic.get_sum(r_category))

        for k, line_category in enumerate(LineCategory):
            for i, r_category in enumerate(RepoCategory):
                if r_category is not RepoCategory.COMMITS and r_category is not RepoCategory.MERGE_COMMITS:
                    table[1 + k + 1][4 + 2 * i] = self.abs_format(total_statistic[r_category][line_category])

        for email, value in author_statistic.items():
            idx = (self.idx_mapping[email] + 1) * 6 + 1
            for i in range(idx, idx + 6):
                table[i][0] = self.idx_mapping[email]

            for i, r_category in enumerate(RepoCategory):
                if r_category is RepoCategory.COMMITS or r_category is RepoCategory.MERGE_COMMITS:
                    table[idx][4 + 2 * i] = self.abs_format(value[r_category])
                    table[idx][5 + 2 * i] = self.rel_format(value[r_category],
                                                            total_statistic[r_category])
                else:
                    table[idx][4 + 2 * i] = self.abs_format(value.get_sum(r_category))
                    table[idx][5 + 2 * i] = self.rel_format(value.get_sum(r_category),
                                                            total_statistic.get_sum(r_category))

            for k, line_category in enumerate(LineCategory):
                for i, r_category in enumerate(RepoCategory):
                    if r_category is not RepoCategory.COMMITS and r_category is not RepoCategory.MERGE_COMMITS:
                        table[idx + 1 + k][4 + 2 * i] = self.abs_format(value[r_category][line_category])
                        table[idx + 1 + k][5 + 2 * i] = self.rel_format(value[r_category][line_category],
                                                                        total_statistic[r_category][line_category])
        return table

    def entire_repository_report(self):
        html_report = HTMLReport()
        html_report.add_heading2('File: Entire Repository')
        html_report.add_heading3('Summary')

        table = self.fill_table(self.statistics.authors, self.statistics.totals)

        for filename, value in sorted(self.statistics.totals_per_file.items()):
            total = self.statistics.totals

            table_line = ["", filename, "", "Total"]

            # TODO: print total values
            for i, r_category in enumerate(RepoCategory):
                if r_category is RepoCategory.COMMITS or r_category is RepoCategory.MERGE_COMMITS:
                    table_line.append(self.abs_format(value[r_category]))
                    table_line.append(self.rel_format(value[r_category], total[r_category]))
                else:
                    table_line.append(self.abs_format(value.get_sum(r_category)))
                    table_line.append(self.rel_format(value.get_sum(r_category), total.get_sum(r_category)))

            table.append(table_line)

        html_report.add_commit_table(table, 1 + (1 + len(self.statistics.authors)) * 6)
        html_report.save('report/report.html')

        return

    def file_report(self):
        for filename, total in self.statistics.totals_per_file.items():
            html_report = HTMLReport()
            html_report.add_heading2(f'File: {filename}')
            html_report.add_heading3('Summary')

            author_statistic = {}
            for email, files in self.statistics.authors_per_file.items():
                for file, value in files.items():
                    if file == filename:
                        author_statistic[email] = value
                        break

            table = self.fill_table(author_statistic, total)
            html_report.add_commit_table(table)

            if filename not in self.commit_list[0].files:
                html_report.add_heading3("This file got deleted!")
            else:
                html_report.add_heading3("Survived Lines")

                file_output = []
                file_output.append([""] + [f"{i}" for i in range(len(self.idx_mapping))] + ["Type", "Code"])

                for line in self.commit_list[0].files[filename].lines:
                    email_author = self.find_author(line.history[0])
                    email_co_authors = []
                    for h in line.history[1:]:
                        email = self.find_author(h)
                        if email not in email_co_authors and email != email_author:
                            email_co_authors.append(email)

                    idx_author = self.get_idx(email_author)
                    idx_co_authors = [self.get_idx(e) for e in email_co_authors]

                    if idx_author == "":
                        file_output.append([""] + len(self.idx_mapping) * [" "] + [line.get_type()[:4],
                                                                                   line.text])
                    else:
                        output = [idx_author]
                        for i in range(len(self.idx_mapping)):
                            if i == idx_author:
                                output.append("A")
                            elif i in idx_co_authors:
                                output.append("M")
                            else:
                                output.append(" ")
                        file_output.append(output + [line.get_type()[:4], line.text])

                html_report.add_file(file_output)

            html_report.save(f"report/files/{filename.replace('.', '_').replace('/', '_')}.html")

    def create(self):
        self.create_table_template()

        if "report" not in os.listdir("."):
            os.mkdir("report")
        if "files" not in os.listdir("report"):
            os.mkdir("report/files")

        self.entire_repository_report()
        self.file_report()
