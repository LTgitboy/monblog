 
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Category, Post, Comment, PostRating, Project, UserProfile, PostStatus
)

# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Post, Category, Project, Comment, PostRating, UserProfile

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # Utilisez des champs simples ou des méthodes qui retournent des strings simples
    list_display = [
        'title',
        'author_username',
        'category_name', 
        'status_display',
        'created_short',
        'views_count'
    ]
    
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    
    def author_username(self, obj):
        return obj.author.username
    author_username.short_description = 'Auteur'
    
    def category_name(self, obj):
        return obj.category.name
    category_name.short_description = 'Catégorie'
    
    def status_display(self, obj):
        return obj.get_status_display()
    status_display.short_description = 'Statut'
    
    def created_short(self, obj):
        return obj.created_at.strftime('%d/%m/%Y')
    created_short.short_description = 'Créé le'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'project_type', 'status', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'project_type', 'status']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_username', 'post_title', 'short_content', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'created_at']
    
    def author_username(self, obj):
        return obj.author.username
    author_username.short_description = 'Auteur'
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Article'
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Contenu'

@admin.register(PostRating)
class PostRatingAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'user_username', 'rating', 'created_at']
    
    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Article'
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Utilisateur'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'website', 'created_at']
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Utilisateur'

# Personnalisation de l'interface admin
admin.site.site_header = "LT.gitboy - Administration"
admin.site.site_title = "LT.gitboy Admin"
admin.site.index_title = "Tableau de bord"





from django.contrib import admin
from django.contrib.auth.models import Permission
from .models import Project, Post, UserProfile

 
 

# Ajouter la gestion des permissions utilisateur
admin.site.register(Permission)