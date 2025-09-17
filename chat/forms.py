from django import forms


class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder": "Your name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Your feedback..."}))


