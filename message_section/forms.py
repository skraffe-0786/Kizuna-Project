from django import forms


class MessageForm(forms.Form):
    content = forms.CharField(
        max_length=1000,
        widget=forms.TextInput(attrs={
            'placeholder': 'Type a message...',
        }),
    )
