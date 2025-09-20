 
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import Post, Comment, PostRating, Project, UserProfile, Category

class PostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())
    
    class Meta:
        model = Post
        fields = [
            'title', 'category', 'excerpt', 'content', 
            'featured_image', 'tags', 'difficulty_level', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de l\'article'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Résumé de l\'article (300 caractères max)'
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Arduino, ESP32, Robotique... (séparés par des virgules)'
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['excerpt'].help_text = "Un court résumé qui apparaîtra dans la liste des articles"
        self.fields['tags'].help_text = "Mots-clés pour faciliter la recherche"
        
        # Style pour tous les champs
        for field in self.fields.values():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            field.widget.attrs.update({'class': 'form-control'})

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Votre commentaire...'
            })
        }

class RatingForm(forms.ModelForm):
    class Meta:
        model = PostRating
        fields = ['rating']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} étoile{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            )
        }

class ProjectForm(forms.ModelForm):
    technologies = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Python, Django, JavaScript, Arduino...'
        }),
        help_text="Listez les technologies utilisées, séparées par des virgules"
    )
    
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'project_type', 'status',
            'github_url', 'demo_url', 'documentation_url',
            'featured_image', 'technologies', 'start_date', 
            'end_date', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du projet'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Description détaillée du projet'
            }),
            'project_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username/repo'
            }),
            'demo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://demo.example.com'
            }),
            'documentation_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lien vers la documentation'
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar', 'website', 'github_url', 
            'linkedin_url', 'twitter_url', 'email_notifications'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Parlez-nous de vous...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://monsite.com'
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/username'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Sauvegarder les informations de l'utilisateur
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Créer le profil utilisateur
            UserProfile.objects.create(user=user)
        return user

class SearchForm(forms.Form):
    q = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher des articles, projets...',
            'autocomplete': 'off'
        })
    )

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la catégorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la catégorie'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-code (classe Font Awesome)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            })
        }

# Formulaire de contact
class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre email'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sujet du message'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Votre message...'
        })
    )
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError('Le message doit contenir au moins 10 caractères.')
        return message
    







 
 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre adresse email'
        }),
        label="Adresse email"
    )
    
    # Champs optionnels pour le profil
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Parlez-nous un peu de vous...',
            'rows': 3
        }),
        label="Biographie",
        max_length=500
    )
    
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-input',
            'placeholder': 'https://votre-site.com'
        }),
        label="Site web"
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "bio", "website")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des champs existants
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Choisissez un nom d\'utilisateur'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Créez un mot de passe sécurisé'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirmez votre mot de passe'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Créer le profil utilisateur avec les données supplémentaires
            UserProfile.objects.create(
                user=user,
                bio=self.cleaned_data.get('bio', ''),
                website=self.cleaned_data.get('website', '')
            )
        return user