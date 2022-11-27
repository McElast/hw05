from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CreationForm(UserCreationForm):
    """
    Создание формы нового пользовтеля
    Атрибуты:
    first_name - имя
    first_name - фамилия
    username - имя пользователя
    email-емаил.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'first_name', 'username', 'email')
