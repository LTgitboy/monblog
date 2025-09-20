from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('blog/', views.post_list, name='post_list'),
    path('projets/', views.projects, name='projects'),
    path('robotique/', views.robotics_posts, name='robotics_posts'),
    path('recherche/', views.search, name='search'),
    
    # Articles
    path('blog/nouveau/', views.create_post, name='create_post'),
    path('blog/<slug:slug>/', views.post_detail, name='post_detail'),
    path('blog/<slug:slug>/modifier/', views.edit_post, name='edit_post'),
    path('categorie/<slug:slug>/', views.category_posts, name='category_posts'),
    
    # Projets
    path('projet/<slug:slug>/', views.project_detail, name='project_detail'),
    
    # Profil utilisateur
    path('profil/', views.profile, name='profile'),
    path('profil/modifier/', views.edit_profile, name='edit_profile'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('admin-profile/', views.admin_profile, name='admin_profile'),    
    # AJAX endpoints
    path('ajax/comment/<int:comment_id>/reply/', views.add_comment_reply, name='add_comment_reply'),
    path('ajax/post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),


    path('projects/create/', views.create_project, name='create_project'),
    path('projects/', views.projects, name='projects'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),



    

 
    path('moderation/', views.moderation_dashboard, name='moderation_dashboard'),
    path('projects/<slug:slug>/approve/', views.approve_project, name='approve_project'),
    path('posts/<slug:slug>/approve/', views.approve_post, name='approve_post'),

    



    path('robotique/arduino/', views.arduino_detail, name='arduino_detail'),
    path('robotique/esp32/', views.esp32_detail, name='esp32_detail'),
    path('robotique/raspberry-pi/', views.raspberry_pi_detail, name='raspberry_pi_detail'),
]
 