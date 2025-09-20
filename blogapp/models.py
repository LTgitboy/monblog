 
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField
from taggit.managers import TaggableManager
from PIL import Image
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


# Créer les permissions personnalisées
def create_custom_permissions(sender, **kwargs):
    content_type = ContentType.objects.get_for_model(Project)
    
    Permission.objects.get_or_create(
        codename='can_publish_project',
        name='Peut publier des projets',
        content_type=content_type,
    )
    
    Permission.objects.get_or_create(
        codename='can_publish_post',
        name='Peut publier des articles',
        content_type=content_type,
    )

# Connecter le signal
from django.db.models.signals import post_migrate
post_migrate.connect(create_custom_permissions)



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, verbose_name="Description")
    icon = models.CharField(max_length=50, default='fas fa-folder', verbose_name="Icône")
    color = models.CharField(max_length=7, default='#2563eb', verbose_name="Couleur")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_posts', kwargs={'slug': self.slug})

class PostStatus(models.TextChoices):
    DRAFT = 'draft', 'Brouillon'
    PENDING = 'pending', 'En attente'
    PUBLISHED = 'published', 'Publié'

class DifficultyLevel(models.TextChoices):
    BEGINNER = 'beginner', 'Débutant'
    INTERMEDIATE = 'intermediate', 'Intermédiaire'
    ADVANCED = 'advanced', 'Avancé'
    EXPERT = 'expert', 'Expert'

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    
    # Contenu
    excerpt = models.TextField(max_length=300, verbose_name="Extrait")
    content = RichTextUploadingField(verbose_name="Contenu")
    
    # Métadonnées
    featured_image = models.ImageField(
        upload_to='posts/images/', 
        blank=True, 
        null=True,
        verbose_name="Image mise en avant"
    )
    tags = TaggableManager(verbose_name="Tags")
    difficulty_level = models.CharField(
        max_length=12,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER,
        verbose_name="Niveau de difficulté"
    )

    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='submitted_posts',
        null=True,
        blank=True
    )
    
    # Statut et dates
    status = models.CharField(
        max_length=10,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
        verbose_name="Statut"
    )
    
    # Statistiques
    views_count = models.PositiveIntegerField(default=0, verbose_name="Vues")
    reading_time = models.PositiveIntegerField(default=5, verbose_name="Temps de lecture (min)")
    
    # Versioning
    version = models.PositiveIntegerField(default=1, verbose_name="Version")
    previous_version = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Version précédente"
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Publié le")
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Calculer le temps de lecture
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)
        
        # Optimiser l'image
        super().save(*args, **kwargs)
        if self.featured_image:
            img = Image.open(self.featured_image.path)
            if img.height > 600 or img.width > 800:
                img.thumbnail((800, 600))
                img.save(self.featured_image.path)
    
    def __str__(self):
        return "{} ({})".format(self.title, self.get_status_display())
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'slug': self.slug})
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def get_next_post(self):
        return Post.objects.filter(
            created_at__gt=self.created_at,
            status=PostStatus.PUBLISHED
        ).order_by('created_at').first()
    
    def get_previous_post(self):
        return Post.objects.filter(
            created_at__lt=self.created_at,
            status=PostStatus.PUBLISHED
        ).order_by('-created_at').first()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Commentaire")
    is_approved = models.BooleanField(default=True, verbose_name="Approuvé")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']
    
    def __str__(self):
        return "Comment by {} on {}".format(
            self.author.username, 
            self.post.title
        )
    
    def get_replies(self):
        return self.replies.filter(is_approved=True)

class PostRating(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'user')
        verbose_name = "Note"
        verbose_name_plural = "Notes"
    
    def __str__(self):
        return f'{self.user.username} - {self.post.title} - {self.rating}★'

class Project(models.Model):
    PROJECT_TYPES = [
        ('web', 'Développement Web'),
        ('robotics', 'Robotique'),
        ('iot', 'Internet des Objets'),
        ('ai', 'Intelligence Artificielle'),
        ('mobile', 'Application Mobile'),
        ('desktop', 'Application Desktop'),
        ('other', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('planning', 'En planification'),
        ('development', 'En développement'),
        ('testing', 'En test'),
        ('completed', 'Terminé'),
        ('maintenance', 'En maintenance'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(verbose_name="Description")
    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPES,
        default='web',
        verbose_name="Type de projet"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning',
        verbose_name="Statut"
    )
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé")
    
    # Liens et ressources
    github_url = models.URLField(blank=True, verbose_name="Lien GitHub")
    demo_url = models.URLField(blank=True, verbose_name="Lien démo")
    documentation_url = models.URLField(blank=True, verbose_name="Documentation")
    
    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='submitted_projects',
        null=True,
        blank=True
    )

    # Images
    featured_image = models.ImageField(
        upload_to='projects/images/',
        blank=True,
        null=True,
        verbose_name="Image principale"
    )
    
    # Technologies utilisées
    technologies = models.CharField(
        max_length=500,
        help_text="Séparez les technologies par des virgules",
        verbose_name="Technologies utilisées"
    )
    
    # Métadonnées
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    is_featured = models.BooleanField(default=False, verbose_name="Projet mis en avant")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['-is_featured', '-created_at']
        permissions = [
            ("can_publish_project", "Peut publier des projets"),
            ("can_publish_post", "Peut publier des articles"),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'slug': self.slug})
    
    def get_technologies_list(self):
        return [tech.strip() for tech in self.technologies.split(',') if tech.strip()]
    








class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True, verbose_name="Biographie")
    avatar = models.ImageField(
        upload_to='avatars/',
        default='avatars/default.jpg',
        verbose_name="Photo de profil"
    )
    website = models.URLField(blank=True, verbose_name="Site web")
    github_url = models.URLField(blank=True, verbose_name="GitHub")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn")
    twitter_url = models.URLField(blank=True, verbose_name="Twitter")
    
    # Préférences
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications par email"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
    
    def __str__(self):
        return f'Profil de {self.user.username}'