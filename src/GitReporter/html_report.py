import html

class HTMLReport:
    head: str = """<!DOCTYPE html>
<html>
<head>
<style>
table {
  font-family: arial, sans-serif;
  border-collapse: collapse;
}

td, th {
  border: 1px solid #dddddd;
  text-align: left;
  padding: 8px;
}

tr:nth-child(even) {
  background-color: #dddddd;
}

.blank_row {
  height: 1em
}
</style>
</head>

<body>
<h1>Git Report (Version 0.1)</h1>
"""
    tail: str = """</body>
</html>
"""

    def __init__(self):
        self.head_string = self.head

    def color(self, idx):
        if idx == "":
            return ""
        if idx < 8:
            return ["#FF9999", "#CCFF99", "#99CCFF", "#FFCC99", "#CC99FF", "#99FFFF", "#FF99CC", "#FFFF99"][idx]
        return ""

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self.head_string + self.tail)

    def add_heading2(self, heading):
        self.head_string += f"<h2>{html.escape(heading)}</h2>\n"

    def add_heading3(self, heading):
        self.head_string += f"<h3>{html.escape(heading)}</h3>\n"

    def add_commit_table(self, table, split_to_files_at=-1):
        """
        each row contains:
          - name
          - ins, del, mod, com (each absolute, percentage)
          - merge-ins, -del, -mod, -com (each absolute, percentage)
        """
        if split_to_files_at == -1:
            split_to_files_at = len(table)

        self.head_string += "<table>\n"

        self.head_string += "  <tr>\n"
        for s in table[0]:
            self.head_string += f"    <th colspan='2'>{html.escape(s)}</th>\n"
        self.head_string += "  </tr>\n"

        for line in table[1:split_to_files_at]:
            self.head_string += "  <tr>\n"
            self.head_string += f"    <td style='background-color:{self.color(line[0])}'>{line[0]}</td>\n"
            self.head_string += f"    <td style='background-color:{self.color(line[0])}'>{html.escape(line[1])}</td>\n"
            for s in line[2:]:
                self.head_string += f"    <td><pre style='font-size:1.1em'>{html.escape(s)}</pre></td>\n"
            self.head_string += "  </tr>\n"

        if split_to_files_at == len(table):
            self.head_string += "</table>\n"
            return

        self.head_string += "  <tr class='blank_row'>\n  </tr>\n"

        for line in table[split_to_files_at:]:
            self.head_string += "  <tr>\n"
            self.head_string += f"    <td></td>\n"
            self.head_string += f"    <td><a href='./files/{line[1].replace('.', '_').replace('/', '_')}.html'>" \
                                f"{html.escape(line[1])}</a></td>\n"
            for s in line[2:]:
                self.head_string += f"    <td><pre style='font-size:1.1em'>{html.escape(s)}</pre></td>\n"
            self.head_string += "  </tr>\n"

        self.head_string += "</table>\n"

    def add_file(self, file):
        self.head_string += "<pre style='font-size:1.2em'><code>\n"

        for element in file[0][1:-1]:
            self.head_string += f"| {element:1s} "
        self.head_string += f"| Line | {file[0][-1]} " + 116 * " " + "|\n"
        self.head_string += (len(file[0]) * 4 + 125) * "-" + "|\n"

        for idx, line in enumerate(file[1:]):
            for element in line[1:-1]:
                self.head_string += f"| {element:1s} "

            output = line[-1][:120]
            if len(output) and output[-1] == '\r':
                output = output[:-1]
            output = html.escape(f'{output:120s}')

            self.head_string += f"| {idx + 1:4d} | <span style='background-color:{self.color(line[0])}'" \
                                f">{output}</span> |\n"

        self.head_string += "</code></pre>\n"
