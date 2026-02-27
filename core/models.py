from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('client', 'Cliente'),
        ('receptionist', 'Recepcionista'),
        ('admin', 'Administrador'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")

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

class Professional(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    bio = models.TextField(blank=True, verbose_name="Biografia")
    photo = models.ImageField(upload_to='professionals/', blank=True, null=True, verbose_name="Foto")
    services = models.ManyToManyField(Service, related_name='professionals', verbose_name="Serviços que realiza")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'

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
        ('multicaixa', 'Multicaixa'),
        ('online', 'Online'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
    )

    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment', verbose_name="Marcação")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash', verbose_name="Método")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    import django.utils.timezone
    created_at = models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return f"Pagamento {self.id} - {self.appointment}"

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'

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
