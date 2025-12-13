from django.urls import path
from . import views
urlpatterns = [
    path('loginpage/', views.loginpage, name='loginpage'),
    path('login_to/',views.login_to,name='login_to'),
    path('logout_view/',views.logout_view,name='logout_view'),
    path('ChangePassword/', views.ChangePassword, name='ChangePassword'),
    path('otpverify/',views.otpverify,name='otpverify'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('StudentManagment/', views.StudentManagment, name='StudentManagment'),
    path('get_batches/<int:class_id>/',views.get_batches,name='get_batches'),
    
    path('AddClasses/', views.AddClasses, name='AddClasses'),
    path('EditClass/<int:class_id>/',views.EditClass,name='EditClass'),
    path('DeleteClass/<int:class_id>/',views.DeleteClass,name='DeleteClass'),
    
    path('AddBatchs/',views.AddBatchs,name='AddBatchs'),
    path('EditBatch/<int:batch_id>',views.EditBatch,name='EditBatch'),
    path('DeleteBatch/<int:batch_id>',views.DeleteBatch,name='DeleteBatch'),
    
    path('AddStudent/', views.AddStudent, name='AddStudent'),
    path('DeleteStudent/<int:student_id>/', views.DeleteStudent, name='DeleteStudent'),
    path('EditStudent/<int:student_id>/',views.EditStudent,name='EditStudent'),
    
    path('PromoteStudent/', views.PromoteStudent, name='PromoteStudent'),
    path('promote/<int:id>/',views.promote,name='promote'),
    
    path('Fees/', views.Fees, name='Fees'),
    path('RecordPayment/<int:student_id>/', views.RecordPayment, name='RecordPayment'),
    path('transactions/<int:student_id>',views.transactions,name='transactions'),
    path('salarycard/<int:student_id>/',views.salarycard,name='salarycard'),
    
    path('Notes/', views.Notes, name='Notes'),
    path('materials_api/',views.materials_api,name='materials_api'),
    path('OnlineClass/', views.OnlineClass, name='OnlineClass'),
    path('Expenditure/', views.Expenditure, name='Expenditure'),
    
    path('AddNotice/', views.AddNotice, name='AddNotice'),
    path('EditNotice/<int:notice_id>',views.EditNotice,name='EditNotice'),
    path('DeleteNotice/<int:notice_id>/',views.DeleteNotice,name='DeleteNotice'),

    path('grid_routine/', views.grid_routine, name='grid_routine'),
    
    path('Done/', views.Done, name='Done'),
    path('name_and_logo_modifier_for_easy_access/',views.name_and_logo_modifier_for_easy_access,name='name_and_logo_modifier_for_easy_access'),
    path('subhojit/',views.subhojit,name='subhojit')
]