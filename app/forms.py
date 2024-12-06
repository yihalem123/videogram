from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import User, Video, Comment

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise forms.ValidationError("Invalid credentials")
        if user.is_banned:
            raise forms.ValidationError("Your account is banned!")
        self.user = user
        return cleaned_data

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username',)

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('title', 'description', 'video_file', 'video_type', 'category')

    def clean(self):
        cleaned_data = super().clean()
        video_file = cleaned_data.get('video_file')
        video_type = cleaned_data.get('video_type')

        if video_file:
            size = video_file.size
            if video_type == 'free':
                if size > 512 * 1024:
                    raise forms.ValidationError("Free videos cannot exceed 0.5MB.")
            else:
                if size > 500 * 1024 * 1024:
                    raise forms.ValidationError("Premium videos cannot exceed 500MB.")
        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

class SearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search...'}))
