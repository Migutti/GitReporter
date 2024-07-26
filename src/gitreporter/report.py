import os, chevron, json
from importlib.resources import files

from .commit import GitCommit
from .config import Config
from .repository_statistic import GitRepositoryStatistic
from .types import GitRepositoryStatisticCategory as RepoCategory, GitLineCategory as LineCategory


class Report:
    TITLE = 'GitReporter'

    def __init__(self, config, statistics, commit_list):
        self.config: Config = config
        self.statistics: GitRepositoryStatistic = statistics
        self.commit_list: list[GitCommit] = commit_list
        self.idx_mapping = {}
        self.table_template = []

    def create(self):
        if self.config.options['json']:
            repository_report = self.json_repository_report()
            with open('gitreport.json', 'w', encoding='utf-8', errors='ignore') as f:
                json.dump(repository_report, f, indent=4)
            return

        if "gitreport" not in os.listdir("."):
            os.mkdir("gitreport")
        if "files" not in os.listdir("gitreport"):
            os.mkdir("gitreport/files")

        self.entire_repository_report()
        self.file_reports()
        return

    def json_repository_report(self):
        dictionary = {
            'title': self.TITLE,
            'repository': self.config.options['repo'].split('/')[-1],
            'authors': []
        }

        dictionary['authors'].append({
            'author-name': 'Total',
            'statistics': self.statistics.totals
        })

        for author in sorted(self.statistics.authors):
            if author in self.statistics.authors:
                dictionary['authors'].append({
                    'author-name': author,
                    'statistics': self.statistics.authors[author]
                })

        return dictionary

    def entire_repository_report(self):
        dictionary = {
            'title': self.TITLE,
            'subtitle': 'Entire Repository',
            'repository': self.config.options['repo'].split('/')[-1],
            'is-file': False,
            'visibility_settings': self.visibility_settings()
        }
        dictionary |= self.summary_table(self.statistics.totals, self.statistics.authors)
        dictionary |= self.file_table()
        self.generate_html("repository_report", "report_template", dictionary)
        return

    def file_reports(self):
        for file in self.statistics.totals_per_file:
            dictionary = {
                'title': self.TITLE,
                'subtitle': f'File: {file}',
                'repository': self.config.options['repo'].split('/')[-1],
                'is-file': True,
                'visibility_settings': self.visibility_settings()
                # TODO: line_mapping visibility settings
            }
            dictionary |= self.summary_table(
                self.statistics.totals_per_file[file],
                {author: self.statistics.authors_per_file[author][file]
                    for author in self.statistics.authors_per_file
                    if file in self.statistics.authors_per_file[author]}
            )
            if file in self.commit_list[0].files:
                dictionary |= self.line_mapping(file)
            else:
                dictionary |= {
                    'line-mapping': []
                }
            self.generate_html(f"files/{file.replace('.', '_').replace('/', '_')}", "report_template", dictionary)

    def generate_html(self, html_name, template_name, dictionary):
        template = files('gitreporter.templates').joinpath(f'{template_name}.mustache').read_text()
        with open(f'gitreport/{html_name}.html', 'w', encoding='utf-8', errors='ignore') as g:
            g.write(chevron.render(template, dictionary))

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
            'author-id': 'total',
            'statistics': self.statistic_block(total_data)
        })

        # create section for each author
        for author in sorted(self.statistics.authors):
            if author in author_data:
                result['authors'].append({
                    'author-name': author,
                    "author-id": author.lower().replace(" ", "_"),
                    'statistics': self.statistic_block(
                        author_data[author],
                        total_data
                    )
                })

        return result

    def find_author(self, binsha):
        commit = next(
            filter(
                lambda commit:
                    commit.commit.binsha == binsha and \
                    self.config.in_time_interval(commit.commit.committed_datetime),
                self.commit_list
            ),
            None
        )
        return commit.commit.author.email if commit else None

    def line_mapping(self, file):
        dictionary = {
            'line-mapping': []
        }

        lines = self.commit_list[0].files[file].lines
        for idx, line in enumerate(lines, start=1):
            author = self.find_author(line.history[0])
            dictionary['line-mapping'].append({
                'number': idx,
                'type': line.get_type().value.lower().replace(" ", "_"),
                'content': line.text[:120],
                'author': author.lower().replace(" ", "_") if author else None
            })

        return dictionary

    def file_table(self):
        return {
            'files': sorted([{
                'name': filename,
                'link': './files/' + filename.replace('.', '_').replace('/', '_') + '.html',
                'value': self.statistics.totals_per_file[filename].get_sum(RepoCategory.SURVIVED_LINES)
            } for filename in self.statistics.totals_per_file], key=lambda x: x['value'], reverse=True)
        }
