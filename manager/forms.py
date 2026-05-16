from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Project, Task, ProjectMember


class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Name')
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email'].lower()
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email'].lower()
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'description', 'due_date', 'priority', 'status', 'assigned_to')
        widgets = {'description': forms.Textarea(attrs={'rows': 4}), 'due_date': forms.DateInput(attrs={'type': 'date'})}


class MemberForm(forms.Form):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=ProjectMember.ROLE_CHOICES)


class StatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('status',)
