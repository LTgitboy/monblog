 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate , logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.contrib.auth.models import User
 

from .models import (
    Post, Category, Comment, PostRating, Project, 
    UserProfile, PostStatus, DifficultyLevel
)
from .forms import (
    PostForm, CommentForm, RatingForm, ProjectForm, 
    UserProfileForm, CustomUserCreationForm
)



def is_admin(user):
    return user.is_staff or user.is_superuser


def home(request):
    """Vue d'accueil"""
    # Articles récents
    recent_posts = Post.objects.filter(
        status=PostStatus.PUBLISHED
    ).select_related('author', 'category').prefetch_related('tags')[:6]
    
    # Projets mis en avant
    featured_projects = Project.objects.filter(is_featured=True)[:3]
    
    # Catégories avec compteurs
    categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status=PostStatus.PUBLISHED))
    ).filter(post_count__gt=0)[:6]
    
    # Statistiques
    stats = {
        'total_posts': Post.objects.filter(status=PostStatus.PUBLISHED).count(),
        'total_projects': Project.objects.count(),
        'total_categories': categories.count(),
    }
    
    context = {
        'recent_posts': recent_posts,
        'featured_projects': featured_projects,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'blogapp/home.html', context)

def post_list(request):
    """Liste des articles avec filtres et recherche"""
    posts = Post.objects.filter(status=PostStatus.PUBLISHED).select_related(
        'author', 'category'
    ).prefetch_related('tags')
    
    # Filtres
    category_slug = request.GET.get('category')
    tag = request.GET.get('tag')
    difficulty = request.GET.get('difficulty')
    search = request.GET.get('search')
    
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    if tag:
        posts = posts.filter(tags__name__icontains=tag)
    
    if difficulty:
        posts = posts.filter(difficulty_level=difficulty)
    
    if search:
        posts = posts.filter(
            Q(title__icontains=search) |
            Q(excerpt__icontains=search) |
            Q(content__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Données pour les filtres
    categories = Category.objects.all()
    popular_tags = Post.tags.most_common()[:10]
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'popular_tags': popular_tags,
        'difficulty_choices': DifficultyLevel.choices,
        'current_category': category_slug,
        'current_tag': tag,
        'current_difficulty': difficulty,
        'current_search': search,
    }
    return render(request, 'blogapp/post_list.html', context)

def robotics_posts(request):
    """Page spéciale Robotique"""
    try:
        robotics_category = Category.objects.get(slug='robotique')
    except Category.DoesNotExist:
        # Retourner une page vide ou un message approprié
        context = {
            'category': None,
            'all_posts': [],
            'arduino_posts': [],
            'esp32_posts': [],
            'raspberry_posts': [],
            'robotics_projects': [],
            'error_message': 'Aucune catégorie Robotique trouvée'
        }
        return render(request, 'blogapp/robotics_posts.html', context)
    
    posts = Post.objects.filter(
        category=robotics_category,
        status=PostStatus.PUBLISHED
    ).select_related('author').prefetch_related('tags')
    
    # Sous-catégories par tags
    arduino_posts = posts.filter(tags__name__icontains='arduino')
    esp32_posts = posts.filter(tags__name__icontains='esp32')
    raspberry_posts = posts.filter(tags__name__icontains='raspberry')
    
    # Projets robotique
    robotics_projects = Project.objects.filter(
        project_type='robotics'
    ).order_by('-is_featured', '-created_at')
    
    context = {
        'category': robotics_category,
        'all_posts': posts,
        'arduino_posts': arduino_posts[:3],
        'esp32_posts': esp32_posts[:3],
        'raspberry_posts': raspberry_posts[:3],
        'robotics_projects': robotics_projects[:4],
    }
    return render(request, 'blogapp/robotics_posts.html', context)

def post_detail(request, slug):
    """Détail d'un article"""
    # Récupérer l'article même s'il n'est pas publié
    post = get_object_or_404(
        Post.objects.select_related('author', 'category').prefetch_related('tags'),
        slug=slug
    )
    
    # Vérifier si l'utilisateur peut voir l'article
    can_view = (
        post.status == PostStatus.PUBLISHED or  # Article publié
        (request.user.is_authenticated and request.user == post.author) or  # Auteur de l'article
        (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser))  # Admin/staff
    )
    
    if not can_view:
        raise Http404("Article non trouvé")
    
    # Si l'article est en attente et que l'utilisateur est l'auteur ou admin, afficher un message
    if post.status == PostStatus.PENDING:
        if request.user == post.author:
            messages.info(request, 'Votre article est en attente d\'approbation par l\'administrateur.')
        elif request.user.is_staff or request.user.is_superuser:
            messages.info(request, 'Cet article est en attente d\'approbation.')
    
    # Incrémenter les vues seulement si l'article est publié
    if post.status == PostStatus.PUBLISHED:
        post.increment_views()
    
    # Commentaires (seulement pour les articles publiés ou en attente d'approbation)
    if post.status == PostStatus.PUBLISHED:
        comments = post.comments.filter(
            is_approved=True,
            parent=None
        ).select_related('author').prefetch_related('replies')
    else:
        comments = []  # Pas de commentaires pour les articles non publiés
    
    # Note moyenne (seulement pour les articles publiés)
    if post.status == PostStatus.PUBLISHED:
        avg_rating = post.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        user_rating = None
        
        if request.user.is_authenticated:
            try:
                user_rating = post.ratings.get(user=request.user).rating
            except PostRating.DoesNotExist:
                pass
    else:
        avg_rating = None
        user_rating = None
    
    # Articles similaires (seulement pour les articles publiés)
    if post.status == PostStatus.PUBLISHED:
        similar_posts = Post.objects.filter(
            category=post.category,
            status=PostStatus.PUBLISHED
        ).exclude(id=post.id)[:3]
    else:
        similar_posts = []
    
    # Formulaires
    comment_form = CommentForm()
    rating_form = RatingForm()
    
    # Gestion des formulaires POST
    if request.method == 'POST':
        # Seuls les articles publiés peuvent recevoir des commentaires et notes
        if post.status != PostStatus.PUBLISHED:
            messages.error(request, 'Vous ne pouvez pas commenter ou noter un article en attente de publication.')
            return redirect('post_detail', slug=slug)
            
        if request.user.is_authenticated:
            if 'comment_submit' in request.POST:
                comment_form = CommentForm(request.POST)
                if comment_form.is_valid():
                    comment = comment_form.save(commit=False)
                    comment.post = post
                    comment.author = request.user
                    comment.save()
                    messages.success(request, 'Commentaire ajouté avec succès!')
                    return redirect('post_detail', slug=slug)
            
            elif 'rating_submit' in request.POST:
                rating_form = RatingForm(request.POST)
                if rating_form.is_valid():
                    rating, created = PostRating.objects.get_or_create(
                        post=post,
                        user=request.user,
                        defaults={'rating': rating_form.cleaned_data['rating']}
                    )
                    if not created:
                        rating.rating = rating_form.cleaned_data['rating']
                        rating.save()
                    messages.success(request, 'Note enregistrée!')
                    return redirect('post_detail', slug=slug)
        else:
            messages.error(request, 'Vous devez être connecté pour commenter ou noter.')
    
    context = {
        'post': post,
        'comments': comments,
        'similar_posts': similar_posts,
        'comment_form': comment_form,
        'rating_form': rating_form,
        'avg_rating': avg_rating,
        'user_rating': user_rating,
        'can_edit': request.user.is_authenticated and (request.user == post.author or request.user.is_staff or request.user.is_superuser),
    }
    return render(request, 'blogapp/post_detail.html', context)

@login_required
def create_post(request):
    """Création d'un nouvel article"""
    can_publish = request.user.has_perm('blogapp.can_publish_post') or is_admin(request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.submitted_by = request.user
            
            # Si l'utilisateur ne peut pas publier directement, mettre en statut "pending"
            if not can_publish:
                post.status = PostStatus.PENDING
                messages.success(request, 'Article soumis! Il sera publié après approbation.')
            else:
                post.status = PostStatus.PUBLISHED
                post.published_at = timezone.now()
                messages.success(request, 'Article créé et publié avec succès!')
            
            post.save()
            form.save_m2m()
            
            # Rediriger vers la page de détail de l'article
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm()
    
    return render(request, 'blogapp/post_form.html', {
        'form': form,
        'title': 'Nouvel Article',
        'can_publish': can_publish
    })

@login_required
def edit_post(request, slug):
    """Modification d'un article"""
    post = get_object_or_404(Post, slug=slug, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            # Créer une nouvelle version
            if post.status == PostStatus.PUBLISHED:
                post.version += 1
            form.save()
            messages.success(request, 'Article modifié avec succès!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)

    return render(request, 'blogapp/post_form.html', {
        'form': form,
        'post': post,
        'title': 'Modifier Article'
    })

def projects(request):
    """Liste des projets"""
    projects_list = Project.objects.all().order_by('-is_featured', '-created_at')
    
    # Filtres
    project_type = request.GET.get('type')
    status = request.GET.get('status')
    
    if project_type:
        projects_list = projects_list.filter(project_type=project_type)
    
    if status:
        projects_list = projects_list.filter(status=status)
    
    # Pagination
    paginator = Paginator(projects_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'project_types': Project.PROJECT_TYPES,
        'status_choices': Project.STATUS_CHOICES,
        'current_type': project_type,
        'current_status': status,
    }
    return render(request, 'blogapp/projects.html', context)

def project_detail(request, slug):
    """Détail d'un projet"""
    project = get_object_or_404(Project, slug=slug)
    
    # Projets similaires
    similar_projects = Project.objects.filter(
        project_type=project.project_type
    ).exclude(id=project.id)[:3]
    
    context = {
        'project': project,
        'similar_projects': similar_projects,
    }
    return render(request, 'blogapp/project_detail.html', context)

def category_posts(request, slug):
    """Articles d'une catégorie"""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(
        category=category,
        status=PostStatus.PUBLISHED
    ).select_related('author').prefetch_related('tags')
    
    # Pagination
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blogapp/category_posts.html', context)

@login_required
def profile(request):
    """Profil utilisateur"""
    if is_admin(request.user):
        return redirect('admin_profile')
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_posts = Post.objects.filter(author=request.user).order_by('-created_at')
    
    context = {
        'user_profile': user_profile,
        'user_posts': user_posts,
    }
    return render(request, 'blogapp/profile.html', context)

@login_required
def edit_profile(request):
    """Modification du profil"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil modifié avec succès!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'blogapp/edit_profile.html', {'form': form})

def register(request):
    """Inscription"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username}!')
            
            # Connexion automatique
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            if user:
                login(request, user)
                return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# Vues AJAX
@require_http_methods(["POST"])
@login_required
def add_comment_reply(request, comment_id):
    """Ajouter une réponse à un commentaire"""
    parent_comment = get_object_or_404(Comment, id=comment_id)
    
    if request.headers.get('content-type') == 'application/json':
        import json
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if content:
            reply = Comment.objects.create(
                post=parent_comment.post,
                parent=parent_comment,
                author=request.user,
                content=content
            )
            return JsonResponse({
                'success': True,
                'reply': {
                    'id': reply.id,
                    'author': reply.author.username,
                    'content': reply.content,
                    'created_at': reply.created_at.strftime('%d %B %Y à %H:%M')
                }
            })
    
    return JsonResponse({'success': False, 'error': 'Données invalides'})

@require_http_methods(["POST"])
@login_required
def toggle_like(request, post_id):
    """Like/Unlike un article"""
    post = get_object_or_404(Post, id=post_id)
    
    # Ici vous pourriez implémenter un système de likes
    # Pour simplifier, on utilise les ratings
    rating, created = PostRating.objects.get_or_create(
        post=post,
        user=request.user,
        defaults={'rating': 5}
    )
    
    if not created:
        rating.delete()
        liked = False
    else:
        liked = True
    
    likes_count = post.ratings.count()
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': likes_count
    })

def search(request):
    """Recherche globale"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if query and len(query) >= 3:
        # Recherche dans les posts
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query),
            status=PostStatus.PUBLISHED
        ).select_related('author', 'category')[:10]
        
        # Recherche dans les projets
        projects = Project.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        
        results = {
            'posts': posts,
            'projects': projects,
            'query': query
        }
    return render(request, 'blogapp/search_results.html', {
        'results': results,
        'query': query
    })

# Vue pour les erreurs 404
def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)

# Vue pour les erreurs 500
def custom_500(request):
    return render(request, 'errors/500.html', status=500)



def login_view(request):
    """Connexion utilisateur"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
        else:
            messages.error(request, 'Identifiant ou mot de passe incorrect.')
    else:
        form = AuthenticationForm()

    return render(request, 'blogapp/login.html', {'form': form})

def logout_view(request):
    """Déconnexion utilisateur"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')


def register(request):
    """Inscription avec validation améliorée"""
    if request.user.is_authenticated:
        messages.info(request, 'Vous êtes déjà connecté.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Créer automatiquement un profil utilisateur
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'bio': form.cleaned_data.get('bio', ''),
                    'website': form.cleaned_data.get('website', '')
                }
            )
            
            # Envoyer un email de bienvenue (optionnel)
            try:
                send_welcome_email(user, form.cleaned_data.get('email'))
            except Exception as e:
                # Ne pas échouer l'inscription si l'email échoue
                print(f"Erreur lors de l'envoi de l'email: {e}")
            
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé avec succès pour {username}! Bienvenue!')
            
            # Connexion automatique
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            if user:
                login(request, user)
                return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'blogapp/register.html', {'form': form})

def send_welcome_email(user, email):
    """Envoyer un email de bienvenue (à implémenter selon votre configuration email)"""
    # Cette fonction est optionnelle et dépend de votre configuration Django
    # Vous pouvez utiliser django.core.mail.send_mail ici
    pass




@login_required
def create_project(request):
    """Création d'un nouveau projet"""
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.submitted_by = request.user
            
            # Seul l'admin peut publier directement des projets
            if is_admin(request.user):
                messages.success(request, 'Projet créé avec succès!')
            else:
                project.is_approved = False
                messages.success(request, 'Projet soumis! Il sera publié après approbation.')
            
            project.save()
            return redirect('project_detail', slug=project.slug)
    else:
        form = ProjectForm()
    
    return render(request, 'blogapp/project_form.html', {
        'form': form,
        'title': 'Nouveau Projet',
        'is_admin': is_admin(request.user)
    })



@user_passes_test(is_admin)
@login_required
def approve_project(request, slug):
    """Approuver un projet soumis"""
    project = get_object_or_404(Project, slug=slug)
    
    if not project.is_approved:
        project.is_approved = True
        project.save()
        messages.success(request, f'Le projet "{project.title}" a été approuvé!')
    else:
        messages.info(request, f'Le projet "{project.title}" est déjà approuvé.')
    
    return redirect('project_detail', slug=slug)

# Vue pour approuver les articles (admin seulement)
@user_passes_test(is_admin)
@login_required
def approve_post(request, slug):
    """Approuver un article soumis"""
    post = get_object_or_404(Post, slug=slug)
    
    if post.status == PostStatus.PENDING:
        post.status = PostStatus.PUBLISHED
        post.published_at = timezone.now()
        post.save()
        messages.success(request, f'L\'article "{post.title}" a été publié!')
    elif post.status == PostStatus.PUBLISHED:
        messages.info(request, f'L\'article "{post.title}" est déjà publié.')
    else:
        messages.warning(request, f'L\'article "{post.title}" est un brouillon.')
    
    return redirect('post_detail', slug=slug)

# Vue pour la modération (admin seulement)
@user_passes_test(is_admin)
@login_required
@user_passes_test(is_admin)
@login_required
def moderation_dashboard(request):
    """Tableau de bord de modération"""
    # Vérification supplémentaire
    if not request.user.is_staff and not request.user.is_superuser:
        raise Http404("Page non trouvée")
    
    pending_posts = Post.objects.filter(status=PostStatus.PENDING)
    pending_projects = Project.objects.filter(is_approved=False)
    
    # Compter les éléments en attente
    pending_posts_count = pending_posts.count()
    pending_projects_count = pending_projects.count()
    total_pending = pending_posts_count + pending_projects_count
    
    context = {
        'pending_posts': pending_posts,
        'pending_projects': pending_projects,
        'pending_posts_count': pending_posts_count,
        'pending_projects_count': pending_projects_count,
        'total_pending': total_pending,
    }
    return render(request, 'blogapp/moderation_dashboard.html', context)





@user_passes_test(is_admin)
@login_required
def admin_profile(request):
    """Profil administrateur avec outils de gestion"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_posts = Post.objects.filter(author=request.user).order_by('-created_at')
    
    # Statistiques pour le tableau de bord
    stats = {
        'total_posts': Post.objects.filter(status=PostStatus.PUBLISHED).count(),
        'total_projects': Project.objects.filter(is_approved=True).count(),
        'total_categories': Category.objects.count(),
    }
    
    # Compter les éléments en attente
    pending_posts_count = Post.objects.filter(status=PostStatus.PENDING).count()
    total_users = User.objects.count()
    
    context = {
        'user_profile': user_profile,
        'user_posts': user_posts,
        'stats': stats,
        'pending_posts_count': pending_posts_count,
        'total_users': total_users,
    }
    return render(request, 'blogapp/admin_profile.html', context)






def arduino_detail(request):
    """Page détaillée Arduino"""
    arduino_posts = Post.objects.filter(
        tags__name__icontains='arduino',
        status=PostStatus.PUBLISHED
    ).select_related('author', 'category').prefetch_related('tags')[:6]
    
    context = {
        'platform': 'Arduino',
        'posts': arduino_posts,
        'tutorials_count': arduino_posts.count(),
    }
    return render(request, 'blogapp/platform_detail.html', context)

def esp32_detail(request):
    """Page détaillée ESP32"""
    esp32_posts = Post.objects.filter(
        tags__name__icontains='esp32',
        status=PostStatus.PUBLISHED
    ).select_related('author', 'category').prefetch_related('tags')[:6]
    
    context = {
        'platform': 'ESP32',
        'posts': esp32_posts,
        'tutorials_count': esp32_posts.count(),
    }
    return render(request, 'blogapp/platform_detail.html', context)

def raspberry_pi_detail(request):
    """Page détaillée Raspberry Pi"""
    raspberry_posts = Post.objects.filter(
        tags__name__icontains='raspberry',
        status=PostStatus.PUBLISHED
    ).select_related('author', 'category').prefetch_related('tags')[:6]
    
    context = {
        'platform': 'Raspberry Pi',
        'posts': raspberry_posts,
        'tutorials_count': raspberry_posts.count(),
    }
    return render(request, 'blogapp/platform_detail.html', context)