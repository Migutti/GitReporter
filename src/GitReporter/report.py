import copy
import os
import chevron
from pprint import pprint

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

    def create(self):
        if "gitreport" not in os.listdir("."):
            os.mkdir("gitreport")
        if "files" not in os.listdir("gitreport"):
            os.mkdir("gitreport/files")

        self.entire_repository_report()

    def entire_repository_report(self):
        dictionary = {
            'title': 'GitReporter (Version 0.1)',
            'subtitle': 'Entire Repository',
            'repository': self.config.options['repo'].split('/')[-1],
            'visibility_settings': self.visibility_settings()
        }
        dictionary |= self.summary_table(self.statistics.totals, self.statistics.authors)
        self.generate_html("repository_report", "report_template", dictionary)
        return

    def generate_html(self, html_name, template_name, dictionary):
        with open(f'web/templates/{template_name}.mustache', 'r', encoding='utf-8') as f:
            with open(f'gitreport/{html_name}.html', 'w', encoding='utf-8') as g:
                g.write(chevron.render(f, dictionary))

    def data_with_ref(self, data, reference):
        if reference is None:
            return f'{data}' + 9 * ' '
        return f'{data} ({data / reference * 100 if reference != 0 else 0.0:5.1f}%)'

    def visibility_settings(self):
        line_categories = [{
            'id': f'{line_category.value.lower().replace(" ", "_")}',
            'name': f'{line_category.value}'
        } for line_category in LineCategory]

        repository_categories = [{
            'id': f'{r_category.value.lower().replace(" ", "_")}',
            'name': f'{r_category.value}'
        } for r_category in RepoCategory]

        result = []
        for idx in range(5):
            result.append({
                'sub_categories': [
                    line_categories[idx] if idx < len(line_categories) else None,
                    repository_categories[:5][idx] if idx < len(repository_categories[:5]) else None,
                    repository_categories[5:][idx] if idx < len(repository_categories[5:]) else None
                ]
            })

        return result

    def statistic_block(self, data, reference=None):
        block = {
            'total-columns': [],
            'line-categories': [{
                'name': line_category.value,
                'columns': []
            } for line_category in LineCategory]
        }

        for r_category in RepoCategory:
            if r_category in [RepoCategory.COMMITS, RepoCategory.MERGE_COMMITS]:
                block['total-columns'].append({
                    'value': self.data_with_ref(
                        data[r_category],
                        reference[r_category] if reference else None
                    )
                })
                for idx in range(len(LineCategory)):
                    block['line-categories'][idx]['columns'].append({
                        'value': '-'
                    })
            else:
                block['total-columns'].append({
                    'value': self.data_with_ref(
                        data.get_sum(r_category),
                        reference.get_sum(r_category) if reference else None
                    )
                })
                for idx, line_category in enumerate(LineCategory):
                    block['line-categories'][idx]['columns'].append({
                        'value': self.data_with_ref(
                            data[r_category][line_category],
                            reference[r_category][line_category] if reference else None
                        )
                    })

        return block

    def summary_table(self, total_data, author_data):
        result = {
            'row-names': [],
            'column-names': [],
            'authors': [],
            'number-of-line-categories': 6
        }

        # create row names, which are the lines categories
        for idx, line_category in enumerate(LineCategory):
            result['row-names'].append({
                'id': f'{line_category.value.lower().replace(" ", "_")}',
                'name': f'{line_category.value}',
                'index': f'{idx + 2}',
                'unchecked': line_category not in [
                    LineCategory.CODE,
                    LineCategory.COMMENT
                ]
            })

        # create column names, which are the repository categories
        for idx, r_category in enumerate(RepoCategory):
            result['column-names'].append({
                'id': f'{r_category.value.lower().replace(" ", "_")}',
                'name': f'{r_category.value}',
                'index': f'{idx + 3}',
                'unchecked': r_category not in [
                    RepoCategory.SURVIVED_LINES,
                    RepoCategory.INSERTIONS,
                    RepoCategory.COMMITS,
                    RepoCategory.MERGE_COMMITS
                ]
            })

        # create section for the totals
        result['authors'].append({
            'author-name': 'Total',
            'statistics': self.statistic_block(total_data)
        })

        # create section for each author
        for author in sorted(self.statistics.authors):
            result['authors'].append({
                'author-name': author,
                'statistics': self.statistic_block(
                    author_data[author],
                    total_data
                )
            })

        return result
