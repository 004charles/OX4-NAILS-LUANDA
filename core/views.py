from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ReceptionistAppointmentForm
from .models import Service, Professional, Category, Message, Appointment

def home(request):
    services = Service.objects.filter(is_active=True)[:6] # Show top 6 on home
    return render(request, 'index.html', {'services': services})

def about(request):
    return render(request, 'about.html')

def services(request):
    services = Service.objects.filter(is_active=True)
    return render(request, 'services.html', {'services': services})

def service_details(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    popular_services = Service.objects.filter(is_active=True).exclude(id=service_id)[:5]
    return render(request, 'service_details.html', {'service': service, 'popular_services': popular_services})

def team(request):
    professionals = Professional.objects.filter(is_active=True)
    return render(request, 'team.html', {'professionals': professionals})

def blog(request):
    return render(request, 'blog.html')

def blog_details(request):
    return render(request, 'blog_details.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and subject and message:
            Message.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, 'A sua mensagem foi enviada com sucesso!')
            return redirect('contact')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')
            
    return render(request, 'contact.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})

def receptionist_login(request):
    """Separate login view for Receptionist/Management."""
    if request.user.is_authenticated:
        return redirect('receptionist_dashboard')

    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_receptionist or user.is_admin:
                login(request, user)
                return redirect('receptionist_dashboard')
            else:
                # If a regular client tries to login here, reject or redirect
                messages.error(request, "Acesso restrito a funcionários.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'dashboard/login_receptionist.html', {'form': form})

from django.utils.text import slugify

@login_required(login_url='receptionist_login')
def manage_categories(request):
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            slug = slugify(name)
            if Category.objects.filter(slug=slug).exists():
                messages.error(request, 'Já existe uma categoria com esse nome.')
            else:
                Category.objects.create(name=name, slug=slug)
                messages.success(request, 'Categoria criada com sucesso.')
        return redirect('manage_categories')
    
    categories = Category.objects.all()
    return render(request, 'dashboard/categories.html', {'categories': categories})

@login_required(login_url='receptionist_login')
def delete_category(request, category_id):
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home')
    
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    messages.success(request, 'Categoria removida.')
    return redirect('manage_categories')

@login_required(login_url='receptionist_login')
def manage_employees(request):
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Professional.objects.create(name=name)
            messages.success(request, 'Funcionário adicionado.')
        return redirect('manage_employees')
    
    employees = Professional.objects.all()
    return render(request, 'dashboard/employees.html', {'employees': employees})

@login_required(login_url='receptionist_login')
def inbox(request):
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home')
    
    msgs = Message.objects.all().order_by('-created_at')
    return render(request, 'dashboard/inbox.html', {'messages': msgs})

@login_required(login_url='receptionist_login')
def settings_view(request):
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home')
    return render(request, 'dashboard/settings.html')

@login_required(login_url='login')
def profile(request):
    return redirect('dashboard')

@login_required(login_url='login')
def booking(request):
    from datetime import datetime, date
    from .models import Service, Professional, Appointment
    
    if request.method == 'POST':
        service_id = request.POST.get('service')
        professional_id = request.POST.get('professional')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        notes = request.POST.get('notes')
        
        # Basic validation and creation logic
        if service_id and date_str and time_str:
            service = Service.objects.get(id=service_id)
            professional = None
            if professional_id:
                professional = Professional.objects.get(id=professional_id)
            
            # Combine date and time
            try:
                appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                
                # Check for past date
                from django.utils import timezone
                if appointment_datetime < datetime.now():
                    messages.error(request, "Não pode marcar para uma data ou hora no passado.")
                    return redirect('booking')

                # Check availability if professional is selected
                if professional:
                    available, error_msg = professional.is_available(appointment_datetime, service.duration_minutes)
                    if not available:
                        messages.error(request, error_msg)
                        return redirect('booking')
                
                appointment = Appointment.objects.create(
                    client=request.user,
                    service=service,
                    professional=professional,
                    date_time=appointment_datetime,
                    notes=notes,
                    status='pending'
                )
                
                # --- Notification Trigger ---
                from .utils import send_notification
                send_notification(
                    appointment, 
                    'whatsapp', 
                    f"Olá {request.user.first_name}! A sua marcação para {service.name} no dia {appointment_datetime.strftime('%d/%m às %H:%M')} foi recebida e está aguardando confirmação."
                )

                messages.success(request, 'Agendamento realizado com sucesso! Aguarde a confirmação.')
                return redirect('client_dashboard')
            except ValueError:
                messages.error(request, "Formato de data ou hora inválido.")

    services = Service.objects.filter(is_active=True)
    professionals = Professional.objects.filter(is_active=True)
    today_date = date.today().strftime('%Y-%m-%d')
    

    return render(request, 'booking.html', {
        'services': services, 
        'professionals': professionals,
        'today_date': today_date
    })

# --- Management System Views ---

@login_required(login_url='login')
def dashboard(request):
    """Redirects to the specific dashboard based on user role."""
    if request.user.is_admin:
        return redirect('/admin/') # Django Admin for now, or build custom
    elif request.user.is_receptionist:
        return redirect('receptionist_dashboard')
    else:
        return redirect('client_dashboard')

@login_required(login_url='login')
def receptionist_dashboard(request):
    """Dashboard for Receptionists to manage appointments."""
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home') # unauthorized access
        
    from .models import Appointment
    from .forms import ReceptionistAppointmentForm
    from django.utils import timezone
    from datetime import datetime, timedelta

    # Handle filters
    date_str = request.GET.get('date')
    if date_str:
        filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        filter_date = timezone.now().date()

    # Handle Manual Booking (POST)
    if request.method == 'POST' and 'create_appointment' in request.POST:
        form = ReceptionistAppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('receptionist_dashboard')
    else:
        form = ReceptionistAppointmentForm()

    # Stats (Always for Today)
    today = timezone.now().date()
    appointments_today_count = Appointment.objects.filter(date_time__date=today).count()
    pending_appointments_count = Appointment.objects.filter(status='pending').count()
    
    # List (Filtered by selected date)
    appointments = Appointment.objects.filter(date_time__date=filter_date).order_by('date_time')
    
    return render(request, 'dashboard/receptionist.html', {
        'appointments': appointments,
        'appointments_today_count': appointments_today_count,
        'pending_appointments_count': pending_appointments_count,
        'filter_date': filter_date,
        'form': form
    })

@login_required(login_url='login')
def update_appointment_status(request, appointment_id, status):
    """View to update appointment status, with business logic for completion."""
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home')
        
    from .models import Appointment, Payment
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if status in ['confirmed', 'canceled', 'completed', 'no_show']:
        appointment.status = status
        appointment.save()
        
        # --- Audit Log ---
        from .utils import log_activity
        log_activity(request.user, f"Status Update: {status}", f"Appointment #{appointment.id} updated to {status}", request)
        
        # --- Notification Trigger ---
        from .utils import send_notification
        messages_mapping = {
            'confirmed': f"Olá {appointment.client.first_name}! A sua marcação para {appointment.service.name} foi CONFIRMADA para {appointment.date_time.strftime('%d/%m às %H:%M')}.",
            'canceled': f"Olá {appointment.client.first_name}. Informamos que a sua marcação para {appointment.service.name} foi CANCELADA. Contacte-nos para mais informações.",
            'completed': f"Olá {appointment.client.first_name}! Esperamos que tenha gostado do seu serviço de {appointment.service.name}. A sua fatura foi gerada e aguardamos o pagamento no salão.",
        }
        
        if status in messages_mapping:
            send_notification(appointment, 'whatsapp', messages_mapping[status])
        
        # Business Logic for Completion
        if status == 'completed':
            # Create a pending payment if it doesn't exist
            if not hasattr(appointment, 'payment'):
                Payment.objects.create(
                    appointment=appointment,
                    amount=appointment.service.price,
                    status='pending'
                )
            
            # --- Automatic Stock Deduction ---
            from .models import StockMovement, ServiceProduct
            required_products = ServiceProduct.objects.filter(service=appointment.service)
            
            for sp in required_products:
                product = sp.product
                # Create movement (exit)
                StockMovement.objects.create(
                    product=product,
                    movement_type='out_service',
                    quantity=sp.quantity,
                    appointment=appointment,
                    notes=f"Consumo automático p/ serviço: {appointment.service.name}"
                )
                
                # Check for low stock alert
                if product.stock_quantity <= product.min_stock_alert:
                    messages.warning(request, f"ALERTA: Stock de {product.name} está baixo ({product.stock_quantity} restantes).")
            
            # --- Loyalty Points ---
            from .models import LoyaltyPoints
            points_to_add = int(appointment.service.price / 1000) # 1 point per 1000kz
            if points_to_add > 0:
                loyalty, created = LoyaltyPoints.objects.get_or_create(client=appointment.client)
                loyalty.points += points_to_add
                loyalty.save()
                messages.info(request, f"O cliente ganhou {points_to_add} pontos de fidelidade!")
            
            messages.success(request, f"Agendamento de {appointment.client.first_name} concluído. Pagamento e baixa de stock processados.")
        
    return redirect('receptionist_dashboard')

@login_required(login_url='login')
def calendar_events(request):
    """View to return appointment events for FullCalendar."""
    from django.http import JsonResponse
    from datetime import timedelta
    from .models import Appointment
    
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    appointments = Appointment.objects.filter(
        status__in=['pending', 'confirmed', 'completed']
    )
    
    if start and end:
        appointments = appointments.filter(date_time__range=[start, end])
        
    events = []
    for app in appointments:
        color = '#ffc107' # pending
        if app.status == 'confirmed': color = '#28a745'
        elif app.status == 'completed': color = '#007bff'
        
        events.append({
            'id': app.id,
            'title': f"{app.client.first_name or app.client.username} - {app.service.name}",
            'start': app.date_time.isoformat(),
            'end': (app.date_time + timedelta(minutes=app.service.duration_minutes)).isoformat(),
            'color': color,
            'extendedProps': {
                'professional': app.professional.name if app.professional else 'N/A',
                'status': app.get_status_display()
            }
        })
        
    return JsonResponse(events, safe=False)

@login_required(login_url='login')
def submit_review(request, appointment_id):
    """View for clients to review their appointments."""
    from .models import Appointment, Review
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)
    
    if appointment.status != 'completed':
        messages.error(request, "Apenas pode avaliar serviços já concluídos.")
        return redirect('client_dashboard')
        
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        Review.objects.update_or_create(
            appointment=appointment,
            defaults={'rating': rating, 'comment': comment}
        )
        
        # --- Audit Log ---
        from .utils import log_activity
        log_activity(request.user, "Review Submitted", f"Review for Appointment #{appointment.id}", request)
        
        messages.success(request, "Obrigado pela sua avaliação!")
        return redirect('client_dashboard')
        
    return render(request, 'dashboard/submit_review.html', {'appointment': appointment})

@login_required(login_url='login')
def client_dashboard(request):
    """Dashboard for Clients (Profile + History + Loyalty)."""
    from .models import LoyaltyPoints
    appointments = request.user.appointments.all().order_by('-date_time')
    loyalty = LoyaltyPoints.objects.filter(client=request.user).first()
    return render(request, 'dashboard/client.html', {
        'appointments': appointments,
        'loyalty_points': loyalty.points if loyalty else 0
    })
@login_required(login_url='login')
def confirm_payment(request, payment_id):
    """Marks a payment as paid and handles receipts."""
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home')
        
    payment = get_object_or_404(Payment, id=payment_id)
    payment.status = 'paid'
    payment.save()
    
    # --- Audit Log ---
    from .utils import log_activity
    log_activity(request.user, "Payment Confirmed", f"Payment #{payment.id} marked as paid", request)
    
    messages.success(request, f"Pagamento de {payment.amount}kz confirmado.")
    return redirect('receptionist_dashboard')

@login_required(login_url='login')
def financial_report(request):
    """Managerial report with Chart.js data."""
    if not request.user.is_admin:
        return redirect('home')
        
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncDate
    from .models import Payment
    
    # Financial aggregate
    total_revenue = Payment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    total_commission = Payment.objects.filter(status='paid').aggregate(Sum('professional_commission'))['professional_commission__sum'] or 0
    net_profit = total_revenue - total_commission
    
    # Chart data: Revenue by Date
    daily_revenue = Payment.objects.filter(status='paid').annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    labels = [d['date'].strftime('%Y-%m-%d') for d in daily_revenue]
    values = [float(d['total']) for d in daily_revenue]
    
    return render(request, 'dashboard/financial_report.html', {
        'total_revenue': total_revenue,
        'total_commission': total_commission,
        'net_profit': net_profit,
        'chart_labels': labels,
        'chart_values': values
    })
