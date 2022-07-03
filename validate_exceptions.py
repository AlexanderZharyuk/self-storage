class NotFullName(Exception):

    def __str__(self):
        return 'Указано не полное имя'


class DigitsInName(Exception):

    def __str__(self):
        return 'В имени есть цифры'


class LetterInNumber(Exception):

    def __str__(self):
        return 'В номере есть буква'


class NumberLengthTooLong(Exception):

    def __str__(self):
        return 'Слишком длинный номер'


class NumberLengthTooShort(Exception):

    def __str__(self):
        return 'Слишком короткий номер'


class NotCorrectStartNumber(Exception):

    def __str__(self):
        return 'Номер начинается не с +7'
