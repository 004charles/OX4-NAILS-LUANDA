from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('client', 'Cliente'),
        ('receptionist', 'Recepcionista'),
        ('admin', 'Administrador'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    preferences = models.TextField(blank=True, verbose_name="Preferências")
    internal_notes = models.TextField(blank=True, verbose_name="Notas Internas")

    @property
    def is_client(self):
        return self.user_type == 'client'

    @property
    def is_receptionist(self):
        return self.user_type == 'receptionist'

    @property
    def is_admin(self):
        return self.user_type == 'admin' or self.is_superuser

    class Meta:
        verbose_name = 'Utilizador'
        verbose_name_plural = 'Utilizadores'

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='services', verbose_name="Categoria")
    name = models.CharField(max_length=100, verbose_name="Nome")
    description = models.TextField(blank=True, verbose_name="Descrição")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    duration_minutes = models.PositiveIntegerField(verbose_name="Duração (minutos)", default=60)
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name="Imagem")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'

class ServiceProduct(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='required_products')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, verbose_name="Quantidade Consumida")

    def __str__(self):
        return f"{self.quantity}x {self.product.name} p/ {self.service.name}"

class Professional(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    bio = models.TextField(blank=True, verbose_name="Biografia")
    photo = models.ImageField(upload_to='professionals/', blank=True, null=True, verbose_name="Foto")
    services = models.ManyToManyField(Service, related_name='professionals', verbose_name="Serviços que realiza")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Taxa de Comissão (%)")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return self.name

    def is_available(self, date_time, duration_minutes):
        from datetime import timedelta
        # 1. Check working hours
        day_of_week = date_time.weekday()
        working_hour = self.working_hours.filter(day=day_of_week).first()
        
        if not working_hour or working_hour.is_off:
            return False, "O profissional não trabalha neste dia."
            
        start_time = working_hour.start_time
        end_time = working_hour.end_time
        target_time = date_time.time()
        target_end_time = (date_time + timedelta(minutes=duration_minutes)).time()
        
        if target_time < start_time or target_end_time > end_time:
            return False, "O horário selecionado está fora do horário de trabalho do profissional."
            
        # 2. Check for conflicts with other appointments
        appointment_end = date_time + timedelta(minutes=duration_minutes)
        conflicts = self.appointment_set.filter(
            status__in=['pending', 'confirmed'],
            date_time__lt=appointment_end,
            date_time__gt=date_time - timedelta(hours=4) # Optimization: only check nearby
        )
        
        for conflict in conflicts:
            conflict_start = conflict.date_time
            conflict_end = conflict_start + timedelta(minutes=conflict.service.duration_minutes)
            
            # Simple overlap check: (StartA < EndB) and (EndA > StartB)
            if date_time < conflict_end and appointment_end > conflict_start:
                return False, "Já existe um agendamento para este profissional neste horário."
                
        return True, ""

    class Meta:
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'

class WorkingHour(models.Model):
    DAY_CHOICES = (
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    )
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='working_hours')
    day = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_off = models.BooleanField(default=False, verbose_name="Folga")

    class Meta:
        unique_together = ('professional', 'day')
        verbose_name = 'Horário de Trabalho'
        verbose_name_plural = 'Horários de Trabalho'

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('canceled', 'Cancelado'),
        ('completed', 'Concluído'),
        ('no_show', 'Não Compareceu'),
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', verbose_name="Cliente")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Serviço")
    professional = models.ForeignKey(Professional, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Profissional")
    date_time = models.DateTimeField(verbose_name="Data e Hora")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} - {self.service.name} - {self.date_time}"

    class Meta:
        verbose_name = 'Marcação'
        verbose_name_plural = 'Marcações'

class Payment(models.Model):
    METHOD_CHOICES = (
        ('cash', 'Dinheiro'),
        ('transfer', 'Transferência Bancária'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
    )

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment', verbose_name="Marcação")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    professional_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Comissão do Profissional")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash', verbose_name="Método")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.professional_commission and self.appointment.professional:
            rate = self.appointment.professional.commission_rate
            self.professional_commission = (self.amount * rate) / 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pagamento {self.id} - {self.appointment}"

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'

class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    category = models.CharField(max_length=100, blank=True, verbose_name="Categoria")
    supplier = models.CharField(max_length=100, blank=True, verbose_name="Fornecedor")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Custo")
    stock_quantity = models.IntegerField(default=0, verbose_name="Quantidade em Stock")
    min_stock_alert = models.IntegerField(default=5, verbose_name="Alerta Stock Baixo")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Data de Validade")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

class StockMovement(models.Model):
    TYPE_CHOICES = (
        ('in', 'Entrada'),
        ('out_service', 'Saída (Serviço)'),
        ('out_manual', 'Saída Manual'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.IntegerField()
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.movement_type == 'in':
            self.product.stock_quantity += self.quantity
        else:
            self.product.stock_quantity -= self.quantity
        self.product.save()
        super().save(*args, **kwargs)

class Review(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], verbose_name="Avaliação")
    comment = models.TextField(blank=True, verbose_name="Comentário")
    created_at = models.DateTimeField(auto_now_add=True)

class LoyaltyPoints(models.Model):
    client = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

class Message(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=200, verbose_name="Assunto")
    message = models.TextField(verbose_name="Mensagem")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name="Lida")

    def __str__(self):
        return f"{self.subject} - {self.name}"

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['-created_at']

class Notification(models.Model):
    TYPE_CHOICES = (
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('sms', 'SMS'),
    )
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')

    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Atividade'
        verbose_name_plural = 'Logs de Atividade'
        ordering = ['-created_at']
