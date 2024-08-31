from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('loginn/', views.loginn, name='loginn'),
    path('logout/', views.logout, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),
    path('forgotpassword/', views.forgotpassword, name='forgotpassword'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name='resetpassword_validate'),
    path('resetpassword/', views.resetpassword, name='resetpassword'),

    path('user_wallet/', views.user_wallet, name='user_wallet'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('track_order/<str:order_id>/', views.track_order, name='track_order'),
    path('change_password/', views.change_password, name='change_password'),

    path('edit_address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete_address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('add_address/', views.add_address, name='add_address'),
    path('return_order/<str:order_number>/', views.return_order, name='return_order'),
    
    path('invoice/<int:order_id>/', views.invoice, name='invoice'),
    path('generate_invoice_pdf/<int:order_number>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    ]