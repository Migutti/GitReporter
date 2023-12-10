from .types import GitLineCategory as LineCategory
from .statistic_values import empty_value

class Textline:
    def __init__(self, token_type: LineCategory, text: str, binsha: bytes):
        self.types: list[LineCategory] = [token_type]
        self.content: list[str] = [text]
        self.history = [binsha]
        self.text = ''

    def add_text(self, text):
        self.text = text

    def get_type(self):
        if len(self.types) == 1:
            return self.types[0]
        else:
            return LineCategory.UNKNOWN

    def to_string(self):
        string = ''
        for c in self.content:
            string += c
        return string

    def __eq__(self, other):
        return self.to_string() == other.to_string()

    def __hash__(self):
        return hash(self.to_string())

    """
    def __repr__(self):
        return f"{self.text[:-1]:120s} | {repr(self.history)}"
    """

    def add_history(self, history):
        self.history = history + self.history

    """
    def __len__(self):
        return len(self.text)
    """

    """
    def to_chars(self):
        return [*self.text]
    """

    def length_wo_whitespace(self):
        return len([c for c in self.to_string() if not c.isspace()])

    def add_token(self, token_type: LineCategory, content: str):
        if self.types[-1] is LineCategory.CODE and token_type is LineCategory.CODE:
            self.content[-1] += content
        elif self.types[-1] is LineCategory.COMMENT and token_type is LineCategory.COMMENT:
            self.content[-1] += content
        else:
            self.types.append(token_type)
            self.content.append(content)

    def update_symbols_only(self):
        for i in range(len(self.types)):
            if self.types[i] is LineCategory.CODE:
                for character in self.content[i]:
                    if character not in "(){}[];:.,":
                        break
                else:
                    self.types[i] = LineCategory.SYMBOLS_ONLY

    @staticmethod
    def evaluate_lines(lines):
        result = empty_value()
        for line in lines:
            if len(line.types) == 1:
                result[line.types[0]] += 1
            else:
                result[LineCategory.UNKNOWN] += 1
        return result
