from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Review, TVShowReview, SeasonReview, EpisodeReview

class MovieSearchForm(forms.Form):
    """Form for searching movies on TMDB"""
    query = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for a movie...'
        })
    )

class ReviewForm(forms.ModelForm):
    """Form for creating and editing reviews"""
    class Meta:
        model = Review
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review here...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control form-range',
                'type': 'range',
                'min': 1,
                'max': 10,
                'step': 1,
                'oninput': 'this.nextElementSibling.value = this.value',
                'style': 'width: 100%;'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.fields['rating'].label = 'Rating (1-10)'
        self.fields['rating'].help_text = 'Slide to select a rating between 1 and 10'
        self.fields['rating'].widget.attrs['id'] = 'rating-range'
        # Добавляем скрытое поле для отображения текущего значения
        self.fields['rating'].widget = forms.TextInput(attrs={
            'type': 'range',
            'class': 'form-range',
            'min': 1,
            'max': 10,
            'step': 1,
            'value': self.initial.get('rating', 5) if self.initial else 5,
            'id': 'rating-range',
            'oninput': 'document.getElementById("rating-value").value = this.value'
        })

class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        """Validate that the email is unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email
    
    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

# Forms for TV Shows
class TVShowSearchForm(forms.Form):
    """Form for searching TV shows on TMDB"""
    query = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for a TV show...'
        })
    )

class TVShowReviewForm(forms.ModelForm):
    """Form for creating and editing TV show reviews"""
    class Meta:
        model = TVShowReview
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review here...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            })
        }
    
    def __init__(self, *args, **kwargs):
        super(TVShowReviewForm, self).__init__(*args, **kwargs)
        self.fields['rating'].label = 'Rating (1-10)'
        self.fields['rating'].help_text = 'Slide to select a rating between 1 and 10'
        self.fields['rating'].widget.attrs['id'] = 'tvshow-rating-range'
        # Добавляем скрытое поле для отображения текущего значения
        self.fields['rating'].widget = forms.TextInput(attrs={
            'type': 'range',
            'class': 'form-range',
            'min': 1,
            'max': 10,
            'step': 1,
            'value': self.initial.get('rating', 5) if self.initial else 5,
            'id': 'tvshow-rating-range',
            'oninput': 'document.getElementById("tvshow-rating-value").value = this.value'
        })

class SeasonReviewForm(forms.ModelForm):
    """Form for creating and editing TV show season reviews"""
    class Meta:
        model = SeasonReview
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review of this season here...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            })
        }
    
    def __init__(self, *args, **kwargs):
        super(SeasonReviewForm, self).__init__(*args, **kwargs)
        self.fields['rating'].label = 'Rating (1-10)'
        self.fields['rating'].help_text = 'Slide to select a rating between 1 and 10'
        self.fields['rating'].widget.attrs['id'] = 'season-rating-range'
        # Добавляем скрытое поле для отображения текущего значения
        self.fields['rating'].widget = forms.TextInput(attrs={
            'type': 'range',
            'class': 'form-range',
            'min': 1,
            'max': 10,
            'step': 1,
            'value': self.initial.get('rating', 5) if self.initial else 5,
            'id': 'season-rating-range',
            'oninput': 'document.getElementById("season-rating-value").value = this.value'
        })

class EpisodeReviewForm(forms.ModelForm):
    """Form for creating and editing TV show episode reviews"""
    class Meta:
        model = EpisodeReview
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review of this episode here...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            })
        }
    
    def __init__(self, *args, **kwargs):
        super(EpisodeReviewForm, self).__init__(*args, **kwargs)
        self.fields['rating'].label = 'Rating (1-10)'
        self.fields['rating'].help_text = 'Slide to select a rating between 1 and 10' 
        self.fields['rating'].widget.attrs['id'] = 'episode-rating-range'
        # Добавляем скрытое поле для отображения текущего значения
        self.fields['rating'].widget = forms.TextInput(attrs={
            'type': 'range',
            'class': 'form-range',
            'min': 1,
            'max': 10,
            'step': 1,
            'value': self.initial.get('rating', 5) if self.initial else 5,
            'id': 'episode-rating-range',
            'oninput': 'document.getElementById("episode-rating-value").value = this.value'
        }) 