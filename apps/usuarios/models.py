from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import secrets
import string


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            # Gera senha aleatória se não fornecida
            password = self.generate_random_password()
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user_with_password(self, email, password=None, **extra_fields):
        """
        Cria um usuário e retorna uma tupla (user, password).
        Use este método quando precisar da senha gerada.
        """
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            # Gera senha aleatória se não fornecida
            password = self.generate_random_password()
            user.set_password(password)
        user.save(using=self._db)
        return user, password

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

    @staticmethod
    def generate_random_password(length=12):
        """Gera uma senha aleatória"""
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        return password


class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name='Email')
    nome = models.CharField(max_length=150, blank=True, verbose_name='Nome')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Avatar')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    is_staff = models.BooleanField(default=False, verbose_name='É staff')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Data de cadastro')

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.nome or self.email

    def get_short_name(self):
        return self.nome or self.email.split('@')[0]


class TokenInscricao(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_inscricao',
        verbose_name='Usuário',
        null=True,
        blank=True
    )
    senha_gerada = models.CharField(max_length=128, verbose_name='Senha Gerada', blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação', db_index=True)
    utilizado = models.BooleanField(default=False, verbose_name='Utilizado', db_index=True)

    class Meta:
        verbose_name = 'Token de Inscrição'
        verbose_name_plural = 'Tokens de Inscrição'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['data_criacao'], name='token_insc_data_criacao_idx'),
            models.Index(fields=['utilizado'], name='token_insc_utilizado_idx'),
            models.Index(fields=['usuario', 'utilizado'], name='token_insc_user_util_idx'),
        ]

    def __str__(self):
        return f"Token para {self.usuario.email} - {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"


class Propriedade(models.Model):
    """Modelo para armazenar informações básicas da propriedade rural"""
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='propriedade',
        verbose_name='Usuário'
    )
    
    # DADOS BÁSICOS/INICIAIS
    proprietario = models.CharField(max_length=255, blank=True, verbose_name='Proprietário')
    municipio_estado = models.CharField(max_length=255, blank=True, verbose_name='Município/Estado')
    proprio_ou_arrendamento = models.CharField(max_length=50, blank=True, verbose_name='Próprio ou Arrendamento')
    indice_pluviometrico = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Índice Pluviométrico'
    )
    area_total_ha = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Área total em há'
    )
    area_util_pastagem_ha = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Área útil de pastagem em há'
    )
    
    # ÁREA
    quantidade_pastos = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1)],
        verbose_name='Quantidade de Pastos'
    )
    tamanho_medio_pastos = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Tamanho médio dos pastos'
    )
    faz_rotacionado = models.BooleanField(default=False, verbose_name='Faz rotacionado')
    percentual_area_rotacionada = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Em quantos % da área'
    )
    faz_adubacao = models.BooleanField(default=False, verbose_name='Faz Adubação')
    faz_correcao_solo = models.BooleanField(default=False, verbose_name='Faz Correção de solo')
    rotina_correcao = models.CharField(max_length=255, blank=True, verbose_name='Com qual rotina')
    possui_area_volumoso = models.BooleanField(default=False, verbose_name='Possui área destinada a produção de volumoso')
    tamanho_area_volumoso_ha = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Qual o tamanho (ha)'
    )
    faz_integracao_lavoura_pecuaria = models.BooleanField(default=False, verbose_name='Faz integração Lavoura Pecuária')
    
    # PRODUÇÃO
    quantidade_animais = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1)],
        verbose_name='Quantidade de Animais'
    )
    sexo_animais = models.CharField(max_length=100, blank=True, verbose_name='Sexo dos Animais')
    tipo_raca_animais = models.CharField(max_length=255, blank=True, verbose_name='Tipo/raça dos Animais')
    tipo_suplementacao = models.CharField(max_length=255, blank=True, verbose_name='Tipo de Suplementação')
    cria_recria_ou_engorda = models.CharField(max_length=100, blank=True, verbose_name='Faz cria, recria ou engorda')
    quantidade_animais_lote_peso = models.CharField(max_length=255, blank=True, verbose_name='Quantidade de Animais por lote e Peso')
    compra_gado_produtor_ou_leilao = models.CharField(max_length=100, blank=True, verbose_name='Compra de gado de produtor ou Leilão')
    tipo_terminacao = models.CharField(max_length=100, blank=True, verbose_name='Tipo de Terminação à pasto/TIP/confinamento')
    taxa_desfrute = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Taxa de Desfrute/Quantidade de Animais Vendidos/ano'
    )
    idade_media_abate = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1)],
        verbose_name='Idade média de abate'
    )
    plantas_frigorificas = models.CharField(max_length=255, blank=True, verbose_name='Plantas frigoríficas mais utilizadas')
    
    # GESTÃO
    quantidade_funcionarios = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(0)],
        verbose_name='Quantidade de funcionários'
    )
    utiliza_software_gestao = models.BooleanField(default=False, verbose_name='Utiliza algum software de gestão')
    qual_software_gestao = models.CharField(max_length=255, blank=True, verbose_name='Qual software de gestão')
    possui_balanca = models.BooleanField(default=False, verbose_name='Possui Balança')
    frequencia_pesagem = models.CharField(max_length=100, blank=True, verbose_name='Frequência de pesagem')
    utiliza_controle_individual = models.BooleanField(default=False, verbose_name='Utiliza controle individual Brinco/chip')
    tipo_brinco_chip = models.CharField(max_length=100, blank=True, verbose_name='Brinco/chip')
    
    # TERMINAÇÃO
    faz_confinamento = models.BooleanField(default=False, verbose_name='Faz confinamento')
    estatico_confinamento = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1)],
        verbose_name='Qual o estático'
    )
    tem_fabrica_racao = models.BooleanField(default=False, verbose_name='Tem fábrica de Ração')
    possui_moinho = models.BooleanField(default=False, verbose_name='Possui Moinho')
    possui_vagao_forrageiro = models.BooleanField(default=False, verbose_name='Possui Vagão Forrageiro')
    capacidade_armazenagem_volumoso = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Capacidade de armazenagem de volumoso galpão/silo'
    )
    capacidade_armazenagem_graos = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Capacidade de armazenagem de grãos galpão/silo'
    )
    ultimo_rendimento_carcaca = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name='Último Rendimento de Carcaça (%)'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação', db_index=True)
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Propriedade'
        verbose_name_plural = 'Propriedades'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['data_criacao'], name='propriedade_data_criacao_idx'),
            models.Index(fields=['usuario'], name='propriedade_usuario_idx'),
        ]
    
    def __str__(self):
        return f"Propriedade de {self.usuario.email}"
    
    def informacoes_preenchidas(self):
        """Verifica se pelo menos os campos básicos foram preenchidos"""
        return bool(self.proprietario and self.municipio_estado)


class Lote(models.Model):
    """Modelo para armazenar informações dos lotes de animais"""
    TIPO_CHOICES = [
        ('lote', 'Lote'),
        ('pasto', 'Pasto'),
        ('curral', 'Curral'),
    ]
    
    SEXO_CHOICES = [
        ('M', 'Macho'),
        ('F', 'Fêmea'),
    ]
    
    propriedade = models.ForeignKey(
        Propriedade,
        on_delete=models.CASCADE,
        related_name='lotes',
        verbose_name='Propriedade'
    )
    
    nome = models.CharField(max_length=255, verbose_name='Nome/Identificação')
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='lote',
        verbose_name='Tipo'
    )
    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        verbose_name='Sexo'
    )
    idade_meses = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='Idade (meses)'
    )
    quantidade = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Quantidade de Animais'
    )
    peso_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Peso (kg)'
    )
    peso_arroba = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Peso (@)'
    )
    valor_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Valor de Compra/Aquisição'
    )
    ultimo_gmd_usado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Último GMD Usado (kg/dia)'
    )
    ultimo_valor_arroba = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Último Valor da @ (R$)'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['propriedade'], name='lote_propriedade_idx'),
            models.Index(fields=['nome'], name='lote_nome_idx'),
            models.Index(fields=['propriedade', 'nome'], name='lote_propriedade_nome_idx'),
        ]
    
    def __str__(self):
        return f"{self.nome} - {self.get_tipo_display()}"


class ProjecaoGanho(models.Model):
    """Modelo para armazenar a projeção de ganho médio diário (GMD) por mês"""
    MES_CHOICES = [
        (1, 'Janeiro'),
        (2, 'Fevereiro'),
        (3, 'Março'),
        (4, 'Abril'),
        (5, 'Maio'),
        (6, 'Junho'),
        (7, 'Julho'),
        (8, 'Agosto'),
        (9, 'Setembro'),
        (10, 'Outubro'),
        (11, 'Novembro'),
        (12, 'Dezembro'),
    ]
    
    lote = models.ForeignKey(
        Lote,
        on_delete=models.CASCADE,
        related_name='projecoes_ganho',
        verbose_name='Lote'
    )
    mes = models.IntegerField(
        choices=MES_CHOICES,
        verbose_name='Mês',
        db_index=True
    )
    ano = models.IntegerField(verbose_name='Ano', db_index=True)
    gmd_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='GMD (kg)'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Projeção de Ganho'
        verbose_name_plural = 'Projeções de Ganho'
        ordering = ['ano', 'mes']
        unique_together = ['lote', 'mes', 'ano']
        indexes = [
            models.Index(fields=['lote', 'ano', 'mes'], name='proj_ganho_lote_ano_mes_idx'),
            models.Index(fields=['ano', 'mes'], name='proj_ganho_ano_mes_idx'),
            models.Index(fields=['lote', 'ano'], name='proj_ganho_lote_ano_idx'),
        ]
    
    def __str__(self):
        return f"{self.lote.nome} - {self.get_mes_display()}/{self.ano} - GMD: {self.gmd_kg} kg"


class GastoNutricional(models.Model):
    """Modelo para armazenar o gasto nutricional diário por lote e mês"""
    MES_CHOICES = [
        (1, 'Janeiro'),
        (2, 'Fevereiro'),
        (3, 'Março'),
        (4, 'Abril'),
        (5, 'Maio'),
        (6, 'Junho'),
        (7, 'Julho'),
        (8, 'Agosto'),
        (9, 'Setembro'),
        (10, 'Outubro'),
        (11, 'Novembro'),
        (12, 'Dezembro'),
    ]
    
    lote = models.ForeignKey(
        Lote,
        on_delete=models.CASCADE,
        related_name='gastos_nutricionais',
        verbose_name='Lote'
    )
    mes = models.IntegerField(
        choices=MES_CHOICES,
        verbose_name='Mês',
        db_index=True
    )
    ano = models.IntegerField(verbose_name='Ano', db_index=True)
    gasto_diario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Gasto Diário (R$/dia)'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Gasto Nutricional'
        verbose_name_plural = 'Gastos Nutricionais'
        ordering = ['ano', 'mes']
        unique_together = ['lote', 'mes', 'ano']
        indexes = [
            models.Index(fields=['lote', 'ano', 'mes'], name='gasto_nutr_lote_ano_mes_idx'),
            models.Index(fields=['ano', 'mes'], name='gasto_nutr_ano_mes_idx'),
            models.Index(fields=['lote', 'ano'], name='gasto_nutr_lote_ano_idx'),
        ]
    
    def __str__(self):
        return f"{self.lote.nome} - {self.get_mes_display()}/{self.ano} - R$ {self.gasto_diario}/dia"
    
    def calcular_gasto_mensal(self):
        """Calcula o gasto mensal baseado no gasto diário e dias do mês"""
        from calendar import monthrange
        dias_mes = monthrange(self.ano, self.mes)[1]
        return self.gasto_diario * Decimal(dias_mes)


class CustoFixo(models.Model):
    """Modelo para armazenar custos fixos por mês"""
    MES_CHOICES = [
        (1, 'Janeiro'),
        (2, 'Fevereiro'),
        (3, 'Março'),
        (4, 'Abril'),
        (5, 'Maio'),
        (6, 'Junho'),
        (7, 'Julho'),
        (8, 'Agosto'),
        (9, 'Setembro'),
        (10, 'Outubro'),
        (11, 'Novembro'),
        (12, 'Dezembro'),
    ]
    
    TIPO_CHOICES = [
        ('arrendamento', 'Arrendamento'),
        ('amortizacao', 'Amortização'),
        ('prolabore', 'Prólabore'),
        ('manutencao', 'Manutenção'),
        ('combustivel', 'Combustível'),
        ('mao_de_obra', 'Mão de Obra'),
        ('servicos_tecnicos', 'Serviços Técnicos'),
        ('supermercado', 'Supermercado'),
        ('itr', 'ITR'),
        ('fretes', 'Fretes'),
        ('energia', 'Energia'),
        ('tele_internet', 'Tele/Internet'),
        ('contador', 'Contador'),
    ]
    
    propriedade = models.ForeignKey(
        Propriedade,
        on_delete=models.CASCADE,
        related_name='custos_fixos',
        verbose_name='Propriedade'
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Custo'
    )
    mes = models.IntegerField(
        choices=MES_CHOICES,
        verbose_name='Mês',
        db_index=True
    )
    ano = models.IntegerField(verbose_name='Ano', db_index=True)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Valor (R$)'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Custo Fixo'
        verbose_name_plural = 'Custos Fixos'
        ordering = ['ano', 'mes', 'tipo']
        unique_together = ['propriedade', 'tipo', 'mes', 'ano']
        indexes = [
            models.Index(fields=['propriedade', 'ano', 'mes'], name='custo_fixo_prop_ano_mes_idx'),
            models.Index(fields=['ano', 'mes'], name='custo_fixo_ano_mes_idx'),
            models.Index(fields=['propriedade', 'ano'], name='custo_fixo_prop_ano_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.get_mes_display()}/{self.ano} - R$ {self.valor}"


class Receita(models.Model):
    """Modelo para armazenar receitas por tipo e mês"""
    MES_CHOICES = [
        (1, 'Janeiro'),
        (2, 'Fevereiro'),
        (3, 'Março'),
        (4, 'Abril'),
        (5, 'Maio'),
        (6, 'Junho'),
        (7, 'Julho'),
        (8, 'Agosto'),
        (9, 'Setembro'),
        (10, 'Outubro'),
        (11, 'Novembro'),
        (12, 'Dezembro'),
    ]
    
    TIPO_CHOICES = [
        ('venda_vacas', 'Venda de Vacas'),
        ('venda_bois', 'Venda de Bois'),
        ('venda_novilhas', 'Vendas de Novilhas'),
        ('venda_bezerras', 'Venda de Bezerras'),
        ('venda_bezerros', 'Venda de Bezerros'),
        ('venda_garrote', 'Venda de Garrote'),
        ('venda_silagem', 'Venda de Silagem'),
    ]
    
    propriedade = models.ForeignKey(
        Propriedade,
        on_delete=models.CASCADE,
        related_name='receitas',
        verbose_name='Propriedade'
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Receita'
    )
    mes = models.IntegerField(
        choices=MES_CHOICES,
        verbose_name='Mês',
        db_index=True
    )
    ano = models.IntegerField(verbose_name='Ano', db_index=True)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Valor (R$)'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Receita'
        verbose_name_plural = 'Receitas'
        ordering = ['ano', 'mes', 'tipo']
        unique_together = ['propriedade', 'tipo', 'mes', 'ano']
        indexes = [
            models.Index(fields=['propriedade', 'ano', 'mes'], name='receita_prop_ano_mes_idx'),
            models.Index(fields=['ano', 'mes'], name='receita_ano_mes_idx'),
            models.Index(fields=['propriedade', 'ano'], name='receita_prop_ano_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.get_mes_display()}/{self.ano} - R$ {self.valor}"


class Mortalidade(models.Model):
    """Modelo para armazenar a mortalidade por lote e mês"""
    MES_CHOICES = [
        (1, 'Janeiro'),
        (2, 'Fevereiro'),
        (3, 'Março'),
        (4, 'Abril'),
        (5, 'Maio'),
        (6, 'Junho'),
        (7, 'Julho'),
        (8, 'Agosto'),
        (9, 'Setembro'),
        (10, 'Outubro'),
        (11, 'Novembro'),
        (12, 'Dezembro'),
    ]
    
    lote = models.ForeignKey(
        Lote,
        on_delete=models.CASCADE,
        related_name='mortalidades',
        verbose_name='Lote'
    )
    mes = models.IntegerField(
        choices=MES_CHOICES,
        verbose_name='Mês',
        db_index=True
    )
    ano = models.IntegerField(verbose_name='Ano', db_index=True)
    percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name='Mortalidade (%)'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Mortalidade'
        verbose_name_plural = 'Mortalidades'
        ordering = ['ano', 'mes']
        unique_together = ['lote', 'mes', 'ano']
        indexes = [
            models.Index(fields=['lote', 'ano', 'mes'], name='mortalidade_lote_ano_mes_idx'),
            models.Index(fields=['ano', 'mes'], name='mortalidade_ano_mes_idx'),
            models.Index(fields=['lote', 'ano'], name='mortalidade_lote_ano_idx'),
        ]
    
    def __str__(self):
        return f"{self.lote.nome} - {self.get_mes_display()}/{self.ano} - {self.percentual}%"


class PeriodoPersonalizado(models.Model):
    """Modelo para armazenar período personalizado por lote e mês"""
    MES_CHOICES = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
        (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro'),
    ]
    
    lote = models.ForeignKey(
        Lote,
        on_delete=models.CASCADE,
        related_name='periodos_personalizados',
        verbose_name='Lote'
    )
    mes = models.IntegerField(
        choices=MES_CHOICES,
        verbose_name='Mês',
        db_index=True
    )
    ano = models.IntegerField(verbose_name='Ano', db_index=True)
    periodo_dias = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='Período (dias)'
    )
    
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Período Personalizado'
        verbose_name_plural = 'Períodos Personalizados'
        ordering = ['ano', 'mes']
        unique_together = ['lote', 'mes', 'ano']
        indexes = [
            models.Index(fields=['lote', 'ano', 'mes'], name='periodo_pers_lote_ano_mes_idx'),
        ]
    
    def __str__(self):
        return f"{self.lote.nome} - {self.get_mes_display()}/{self.ano} - {self.periodo_dias} dias"
