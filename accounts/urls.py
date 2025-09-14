from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    
    # Routes CRUD pour les utilisateurs
    path('create_user', views.create_user, name='create_user'),
    path('update_user/<int:user_id>', views.update_user, name='update_user'),
    path('delete_user/<int:user_id>', views.delete_user, name='delete_user'),
    
    # Routes CRUD pour les voitures
    path('create_car', views.create_car, name='create_car'),
    path('update_car/<int:car_id>', views.update_car, name='update_car'),
    path('delete_car/<int:car_id>', views.delete_car, name='delete_car'),
    
    # Routes CRUD pour les demandes
    path('inquiry_detail/<int:inquiry_id>', views.inquiry_detail, name='inquiry_detail'),
    path('update_inquiry_status/<int:inquiry_id>', views.update_inquiry_status, name='update_inquiry_status'),
    path('delete_inquiry/<int:inquiry_id>', views.delete_inquiry, name='delete_inquiry'),
    path('generate_invoice/<int:inquiry_id>', views.generate_invoice, name='generate_invoice'),
]
