from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Usuários'

    def ready(self):
        """Cria usuário admin padrão se não existir"""
        
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        admin_email = 'agrodash303@gmail.com'
        
        # Verifica se já existe um usuário admin com esse email
        if not User.objects.filter(email=admin_email, is_superuser=True).exists():
            try:
                # Cria o usuário admin
                User.objects.create_superuser(
                    email=admin_email,
                    password='1234'
                )
                print(f'✓ Usuário admin criado com sucesso: {admin_email}')
            except Exception as e:
                print(f'Erro ao criar usuário admin: {e}')
