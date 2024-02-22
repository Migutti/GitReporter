from .textline import Textline
from .types import GitLineCategory as LineCategory

from pygments.lexer import RegexLexer
from pygments.token import *


class CppCommentLexer(RegexLexer):
    """
    Citation: https://pygments.org/docs/lexerdevelopment/ [2023/02/27]
    """
    tokens = {
        'root': [
            (r'//.*?$', Comment.Singleline),
            # . -> whatever char, *? -> greedy, as often as possible, -> $ -> stop before '\n
            (r'/\*', Comment.Multiline, 'comment-ml'),
            (r'/', Text),
            (r"'", String.Char, 'char'),
            (r'"', String, 'string'),
            (r'\n', Text.Whitespace),
            (r'[^\'"/\n]+', Text)
        ],
        'comment-ml': [
            (r'\*/', Comment.Multiline, 'root'),
            (r'\*', Comment.Multiline),
            (r'\n', Text.Whitespace),
            (r'[^\*\n]+', Comment.Multiline)
        ],
        'char': [
            (r"\\.", String.Char),
            (r"[^\\'\n]+", String.Char),
            (r"\n", Text.Whitespace),
            (r"'", String.Char, 'root')
        ],
        'string': [
            (r'\\\n', Text.Whitespace),
            (r'\\.', String),
            (r'[^"\\\n]+', String),
            (r"\n", Text.Whitespace),
            (r'"', String, 'root'),
        ]
    }


class GitFile:
    def __init__(self, file, binsha, config):
        self.history = [binsha]

        if config.options['comments-and-coding-standard']:
            self.lines = self.standardize_file(file, binsha)
        else:
            self.lines = [Textline(LineCategory.UNKNOWN, line, binsha) for line in file.split('\n')]

        raw_lines = file.split('\n')
        for i in range(len(self.lines)):
            self.lines[i].add_text(raw_lines[i])

    """
    def __repr__(self):
        str = ""
        for h in self.history:
            str += f'{h.hex()}, '
        str += f'length: {len(self.lines)}'
        return str
    """

    def add_history(self, history):
        self.history = history + self.history

    def merge_histories(self, history_1, history_2):
        history = history_1[:]
        for h in history_2:
            if h not in history:
                history.append(h)
        self.history = history + self.history

    """
    def blame(self):
        str = ''
        for line in self.lines:
            str += f'{line.history[-1].hex()} | {line.text}\n'
        print(str)
    """

    def standardize_file(self, text: str, binsha):
        tokens = CppCommentLexer().get_tokens_unprocessed(text)
        lines: list[Textline] = []
        create_new = True

        for token in tokens:
            token_type = token[1]
            # remove whitespace
            text_without_ws = "".join(token[2].split())

            if create_new:
                if token_type is Token.Text.Whitespace:
                    # we only have a newline
                    lines.append(Textline(LineCategory.EMPTY, '', binsha))
                elif not text_without_ws:
                    # we continue with the next token
                    continue
                elif token_type is Token.Text or token_type is Token.String or token_type is Token.String.Char:
                    # we have some non-whitespace code
                    lines.append(Textline(LineCategory.CODE, text_without_ws, binsha))
                    create_new = False
                elif token_type is Token.Comment.Singleline or token_type is Token.Comment.Multiline:
                    # we have a comment
                    lines.append(Textline(LineCategory.COMMENT, text_without_ws, binsha))
                    create_new = False
                else:
                    assert False, f'This code should be unreachable! We have type: {token_type}'
            else:
                if token_type is Token.Text.Whitespace:
                    # we found the newline
                    create_new = True
                    lines[-1].update_symbols_only()
                elif not text_without_ws:
                    # we continue with the next token
                    continue
                elif token_type is Token.Text or token_type is Token.String or token_type is Token.String.Char:
                    # we have some non-whitespace code
                    lines[-1].add_token(LineCategory.CODE, text_without_ws)
                elif token_type is Token.Comment.Singleline or token_type is Token.Comment.Multiline:
                    lines[-1].add_token(LineCategory.COMMENT, text_without_ws)
                else:
                    assert False, f'This code should be unreachable! We have type: {token_type}, {text}'

        if lines:
            lines[-1].update_symbols_only()
        return lines
