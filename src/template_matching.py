ONE_NINE = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}


class TemplateMatching:

    def __init__(self):

        self.templates = ['########']

    def has_matching_template(self, wagon_num: str) -> bool:
        for template in self.templates:
            if self.does_match_template(template, wagon_num):
                return True
        return False

    def does_match_template(self, template: list, wagon_num: str) -> bool:
        wagon_num = wagon_num.upper()
        if not wagon_num:
            return False

        if len(template) != len(wagon_num):
            return False

        for i in range(len(template)):
            t = template[i]
            c = wagon_num[i]

            if not self.is_correct_char_template(t, c, i, wagon_num):
                return False

        return True

    def is_correct_char_template(self, t: str, c: str, ind: int,
                                 wagon_num: str) -> bool:

        if t == '#':
            return c.isdigit()

        if t == 'x':
            if wagon_num[ind - 1] == '0' and c in ONE_NINE:
                return True

        if t == 'n':
            return c in ONE_NINE

        return False


"""
    Template chars description
    # - any digit
    @ - any letter
    upper letters are same letter
    n - [1-9]
"""
