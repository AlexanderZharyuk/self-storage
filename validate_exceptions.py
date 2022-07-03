class NotFullName(Exception):

    def __str__(self):
        return 'Указано не полное имя'


class DigitsInName(Exception):

    def __str__(self):
        return 'В имени есть цифры'


class LetterInNumber(Exception):

    def __str__(self):
        return 'В номере есть буква'


class NumberLength(Exception):

    def __str__(self):
        return 'Слишком маленький или длинный номер'
