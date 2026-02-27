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
            appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            appointment = Appointment.objects.create(
                client=request.user,
                service=service,
                professional=professional,
                date_time=appointment_datetime,
                notes=notes,
                status='pending'
            )
            return redirect('profile') # Redirect to profile to see the appointment

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
    """View to update appointment status."""
    if not request.user.is_receptionist and not request.user.is_admin:
        return redirect('home')
        
    from .models import Appointment
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if status in ['confirmed', 'canceled', 'completed', 'no_show']:
        appointment.status = status
        appointment.save()
        
    return redirect('receptionist_dashboard')

@login_required(login_url='login')
def client_dashboard(request):
    """Dashboard for Clients (Profile + History)."""
    appointments = request.user.appointments.all().order_by('-date_time')
    return render(request, 'dashboard/client.html', {'appointments': appointments})


