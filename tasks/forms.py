from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Task


class StyledFormMixin:
    """Apply consistent UI styling to Django form widgets."""

    def _apply_styles(self):
        for field in self.fields.values():
            classes = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                base_class = 'form-check-input'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                base_class = 'form-select'
            else:
                base_class = 'form-control'

            field.widget.attrs['class'] = f'{base_class} {classes}'.strip()


class UserRegistrationForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()


class TaskForm(StyledFormMixin, forms.ModelForm):
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'status', 'priority', 'progress', 'due_date', 'is_pinned')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'progress': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

