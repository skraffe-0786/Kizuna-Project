from django import forms

from .models import UserProfile, Highlight


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_pic', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'placeholder': 'Tell us about your anime interests...',
                'rows': 3,
            }),
            'profile_pic': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class HighlightForm(forms.ModelForm):
    class Meta:
        model = Highlight
        fields = ['name', 'cover']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Highlight name', 'maxlength': 50}),
            'cover': forms.FileInput(attrs={'accept': 'image/*'}),
        }
