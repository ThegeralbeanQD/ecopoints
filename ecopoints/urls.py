from django.urls import path
from ecopoints import views

app_name = 'ecopoints'

urlpatterns = [
    path('', views.index, name='index'),
    path('insights/', views.insights, name='insights'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('categories/', views.categories, name='categories'),
    path('category/<slug:category_slug>/', views.show_category, name='show_category'),
    path('task/complete/<int:task_id>/', views.complete_task, name='complete_task'),
    path('like_category/<slug:category_slug>/', views.like_category, name='like_category'),
]
