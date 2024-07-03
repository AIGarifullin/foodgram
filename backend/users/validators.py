import re

from django.core.exceptions import ValidationError


def validate_username(value):
    regex = r'^[\w.@+-]+\Z'
    if re.search(regex, value) is None:
        invalid_characters = set(re.findall(r'[^\w.@+-]', value))
        raise ValidationError(
            (
                f'Недопустимые символы {invalid_characters} в имени '
                'пользователя. Оно может содержать только буквы, '
                'цифры и знаки @/./+/-/_.'
            ),
        )

    if value.lower() == 'me':
        raise ValidationError('Недопустимое имя пользователя.')
    return value
