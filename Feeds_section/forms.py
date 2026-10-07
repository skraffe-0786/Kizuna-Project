from django import forms

from .models import Story, Reel, ReelComment


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class ReelForm(forms.ModelForm):
    class Meta:
        model = Reel
        fields = ['video', 'caption']
        widgets = {
            'video': forms.FileInput(attrs={'accept': 'video/*'}),
            'caption': forms.Textarea(attrs={
                'placeholder': 'Write a caption...',
                'rows': 2,
            }),
        }


class ReelCommentForm(forms.ModelForm):
    class Meta:
        model = ReelComment
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={
                'placeholder': 'Add a comment...',
            }),
        }
