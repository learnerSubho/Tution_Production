from django.urls import path
from . import views
urlpatterns = [
    path('login/', views.student_login, name='student_login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.student_logout, name='student_logout'),
    
    path('study_materials/', views.study_materials, name='study_materials'),
    path('notes_api/',views.notes_api, name='notes_api'),
    
    path('salarycard/', views.salarycard, name='salarycard'),
    
    path('changepassword/', views.changepassword, name='changepassword'),
]