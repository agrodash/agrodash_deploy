from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import TokenInscricao, Usuario, Propriedade, Lote, ProjecaoGanho, GastoNutricional
from .models import UsuarioManager


class TokenInscricaoAdminForm(forms.ModelForm):
    email_usuario = forms.EmailField(
        label='Email do Usuário',
        help_text='Digite o email do usuário. Se o usuário não existir, ele será criado automaticamente com uma senha aleatória.',
        required=True
    )
    
    class Meta:
        model = TokenInscricao
        fields = ['email_usuario', 'utilizado']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se está editando um registro existente, mostra o email do usuário
        if self.instance and self.instance.pk and self.instance.usuario:
            self.fields['email_usuario'].initial = self.instance.usuario.email
            self.fields['email_usuario'].widget.attrs['readonly'] = True
            self.fields['email_usuario'].help_text = 'Email do usuário (não pode ser alterado)'
    
    def save(self, commit=True):
        email = self.cleaned_data['email_usuario']
        
        # Busca ou cria o usuário
        try:
            usuario = Usuario.objects.get(email=email)
            # Se o usuário já existe e estamos criando um novo token, gera nova senha
            if not self.instance.pk:
                senha_aleatoria = UsuarioManager.generate_random_password()
                usuario.set_password(senha_aleatoria)
                usuario.save()
                self.instance.senha_gerada = senha_aleatoria
        except Usuario.DoesNotExist:
            # Cria novo usuário com senha aleatória
            senha_aleatoria = UsuarioManager.generate_random_password()
            usuario, _ = Usuario.objects.create_user_with_password(email=email, password=senha_aleatoria)
            self.instance.senha_gerada = senha_aleatoria
        
        self.instance.usuario = usuario
        
        if commit:
            self.instance.save()
        
        return self.instance
    
    def save_m2m(self):
        """
        Método necessário para compatibilidade com o Django admin.
        Não há campos many-to-many neste formulário, então este método é vazio.
        """
        pass


class PropriedadeForm(forms.ModelForm):
    class Meta:
        model = Propriedade
        fields = '__all__'
        exclude = ['usuario', 'data_criacao', 'data_atualizacao']
        widgets = {
            'proprietario': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'municipio_estado': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'proprio_ou_arrendamento': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'indice_pluviometrico': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 1200.50'}),
            'area_total_ha': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 500.00'}),
            'area_util_pastagem_ha': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 300.00'}),
            'quantidade_pastos': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'min': '1', 'placeholder': 'Ex: 10'}),
            'tamanho_medio_pastos': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 30.00'}),
            'faz_rotacionado': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'percentual_area_rotacionada': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'min': '0', 'max': '100', 'placeholder': '0-100'}),
            'faz_adubacao': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'faz_correcao_solo': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'rotina_correcao': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'possui_area_volumoso': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'tamanho_area_volumoso_ha': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 50.00'}),
            'faz_integracao_lavoura_pecuaria': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'quantidade_animais': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'min': '1', 'placeholder': 'Ex: 500'}),
            'sexo_animais': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'tipo_raca_animais': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'tipo_suplementacao': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'cria_recria_ou_engorda': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'quantidade_animais_lote_peso': forms.Textarea(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'rows': 3}),
            'compra_gado_produtor_ou_leilao': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'tipo_terminacao': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'taxa_desfrute': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 25.50'}),
            'idade_media_abate': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'min': '1', 'placeholder': 'Ex: 24'}),
            'plantas_frigorificas': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'quantidade_funcionarios': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'min': '0', 'placeholder': 'Ex: 5'}),
            'utiliza_software_gestao': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'qual_software_gestao': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'possui_balanca': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'frequencia_pesagem': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'utiliza_controle_individual': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'tipo_brinco_chip': forms.TextInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'}),
            'faz_confinamento': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'estatico_confinamento': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'min': '1', 'placeholder': 'Ex: 1000'}),
            'tem_fabrica_racao': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'possui_moinho': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'possui_vagao_forrageiro': forms.CheckboxInput(attrs={'class': 'size-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600'}),
            'capacidade_armazenagem_volumoso': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 5000.00'}),
            'capacidade_armazenagem_graos': forms.NumberInput(attrs={'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6', 'step': '0.01', 'min': '0', 'placeholder': 'Ex: 3000.00'}),
        }


class PerfilForm(forms.ModelForm):
    """Formulário para editar informações pessoais do usuário"""
    class Meta:
        model = Usuario
        fields = ['nome', 'avatar']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'id': 'first-name',
                'autocomplete': 'given-name'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'sr-only',
                'id': 'avatar-upload',
                'accept': 'image/*'
            }),
        }


class AlterarSenhaForm(forms.Form):
    """Formulário para alterar senha do usuário"""
    current_password = forms.CharField(
        label='Senha atual',
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
            'id': 'current-password',
            'autocomplete': 'current-password'
        }),
        required=True
    )
    new_password = forms.CharField(
        label='Nova senha',
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
            'id': 'new-password',
            'autocomplete': 'new-password'
        }),
        required=True,
        help_text='A senha deve conter pelo menos 8 caracteres.'
    )
    confirm_password = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={
            'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
            'id': 'confirm-password',
            'autocomplete': 'new-password'
        }),
        required=True
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError('A senha atual está incorreta.')
        return current_password

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        password_validation.validate_password(new_password, self.user)
        return new_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError({'confirm_password': 'As senhas não coincidem.'})

        return cleaned_data

    def save(self):
        """Altera a senha do usuário"""
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user


class LoteForm(forms.ModelForm):
    """Formulário para criar/editar lotes"""
    class Meta:
        model = Lote
        fields = ['nome', 'tipo', 'sexo', 'idade_meses', 'quantidade', 'peso_kg', 'peso_arroba', 'valor_compra']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'placeholder': 'Ex: Lote 01, Pasto da Mata, Curral 01'
            }),
            'tipo': forms.Select(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'
            }),
            'sexo': forms.Select(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'
            }),
            'idade_meses': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'min': '0',
                'placeholder': 'Ex: 10'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'min': '1',
                'placeholder': 'Ex: 200'
            }),
            'peso_kg': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ex: 210.00'
            }),
            'peso_arroba': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ex: 7.00'
            }),
            'valor_compra': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ex: 2870.00'
            }),
        }


class ProjecaoGanhoForm(forms.ModelForm):
    """Formulário para criar/editar projeções de ganho"""
    class Meta:
        model = ProjecaoGanho
        fields = ['lote', 'mes', 'ano', 'gmd_kg']
        widgets = {
            'lote': forms.Select(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'
            }),
            'mes': forms.Select(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'
            }),
            'ano': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'min': '2020',
                'max': '2100',
                'placeholder': 'Ex: 2024'
            }),
            'gmd_kg': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ex: 0.90'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        propriedade = kwargs.pop('propriedade', None)
        super().__init__(*args, **kwargs)
        if propriedade:
            self.fields['lote'].queryset = Lote.objects.filter(propriedade=propriedade)


class GastoNutricionalForm(forms.ModelForm):
    """Formulário para criar/editar gastos nutricionais"""
    class Meta:
        model = GastoNutricional
        fields = ['lote', 'mes', 'ano', 'gasto_diario']
        widgets = {
            'lote': forms.Select(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'
            }),
            'mes': forms.Select(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6'
            }),
            'ano': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'min': '2020',
                'max': '2100',
                'placeholder': 'Ex: 2024'
            }),
            'gasto_diario': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ex: 1.50'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        propriedade = kwargs.pop('propriedade', None)
        super().__init__(*args, **kwargs)
        if propriedade:
            self.fields['lote'].queryset = Lote.objects.filter(propriedade=propriedade)

