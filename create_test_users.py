import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ox4_nails.settings')
django.setup()

from core.models import User

def create_user(username, email, password, user_type):
    if User.objects.filter(username=username).exists():
        print(f"User {username} already exists.")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.user_type = user_type
        user.save()
        print(f"Updated password and type for {username}.")
    else:
        user = User.objects.create_user(username=username, email=email, password=password)
        user.user_type = user_type
        user.save()
        print(f"Created user {username} ({user_type}).")

if __name__ == '__main__':
    print("Creating test users...")
    create_user('recepcionista', 'recepcao@ox4.com', 'ox4nails2024', 'receptionist')
    create_user('cliente1', 'cliente@email.com', 'ox4nails2024', 'client')
    print("Done! You can now log in.")
