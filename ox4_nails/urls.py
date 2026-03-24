from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    home, about, services, team, blog, blog_details, service_details, contact, 
    register, custom_login, profile, booking, dashboard, receptionist_dashboard, 
    client_dashboard, update_appointment_status, receptionist_login, 
    manage_categories, delete_category, manage_employees, inbox, settings_view,
    calendar_events, confirm_payment, financial_report, submit_review
)
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('gestao/login/', receptionist_login, name='receptionist_login'),
    path('', home, name='home'),
    path('sobre/', about, name='about'),
    path('servicos/', services, name='services'),
    path('servicos/detalhes/<int:service_id>/', service_details, name='service_details'),
    path('equipa/', team, name='team'),
    path('blog/', blog, name='blog'),
    path('blog/detalhes/', blog_details, name='blog_details'),
    path('contactos/', contact, name='contact'),
    path('registar/', register, name='register'),
    path('login/', custom_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('perfil/', profile, name='profile'),
    path('marcacao/', booking, name='booking'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/receptionist/', receptionist_dashboard, name='receptionist_dashboard'),
    path('dashboard/client/', client_dashboard, name='client_dashboard'),
    path('dashboard/categorias/', manage_categories, name='manage_categories'),
    path('dashboard/categorias/delete/<int:category_id>/', delete_category, name='delete_category'),
    path('dashboard/funcionarios/', manage_employees, name='manage_employees'),
    path('dashboard/mensagens/', inbox, name='inbox'),
    path('dashboard/configuracoes/', settings_view, name='settings'),
    path('dashboard/appointment/<int:appointment_id>/update/<str:status>/', update_appointment_status, name='update_appointment_status'),
    path('dashboard/calendar/events/', calendar_events, name='calendar_events'),
    path('dashboard/payment/<int:payment_id>/confirm/', confirm_payment, name='confirm_payment'),
    path('dashboard/financeiro/', financial_report, name='financial_report'),
    path('dashboard/appointment/<int:appointment_id>/avaliar/', submit_review, name='submit_review'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
