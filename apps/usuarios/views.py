from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from .models import Propriedade, Lote, ProjecaoGanho, GastoNutricional, CustoFixo, Receita, Mortalidade
from .forms import PropriedadeForm, PerfilForm, AlterarSenhaForm, LoteForm, ProjecaoGanhoForm, GastoNutricionalForm


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        # Verifica se as informações básicas foram preenchidas
        try:
            propriedade = Propriedade.objects.get(usuario=request.user)
            if propriedade.informacoes_preenchidas():
                return redirect('home')
            else:
                messages.warning(request, 'Por favor, complete o cadastro das informações básicas da propriedade.')
                return redirect('preencher_informacoes')
        except (Propriedade.DoesNotExist, TypeError, ValueError):
            messages.warning(request, 'Por favor, complete o cadastro das informações básicas da propriedade.')
            return redirect('preencher_informacoes')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.get_full_name()}!')
            # Verifica se as informações básicas foram preenchidas
            try:
                propriedade = Propriedade.objects.get(usuario=user)
                if propriedade.informacoes_preenchidas():
                    next_url = request.GET.get('next', 'home')
                    return redirect(next_url)
                else:
                    messages.warning(request, 'Por favor, complete o cadastro das informações básicas da propriedade.')
                    return redirect('preencher_informacoes')
            except (Propriedade.DoesNotExist, TypeError, ValueError):
                messages.warning(request, 'Por favor, complete o cadastro das informações básicas da propriedade.')
                return redirect('preencher_informacoes')
        else:
            messages.error(request, 'Email ou senha incorretos.')
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('login')


@login_required
def settings_view(request):
    """View para a página de configurações com abas de conta e propriedade"""
    perfil_form = PerfilForm(instance=request.user)
    senha_form = AlterarSenhaForm(user=request.user)
    
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        propriedade = None
    
    propriedade_form = PropriedadeForm(instance=propriedade)
    
    # Processa formulário de perfil
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            perfil_form = PerfilForm(request.POST, request.FILES, instance=request.user)
            if perfil_form.is_valid():
                perfil_form.save()
                messages.success(request, 'Perfil atualizado com sucesso!')
                return redirect('preencher_informacoes')
        
        elif 'change_password' in request.POST:
            senha_form = AlterarSenhaForm(user=request.user, data=request.POST)
            if senha_form.is_valid():
                senha_form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('preencher_informacoes')
        
        elif 'save_propriedade' in request.POST:
            propriedade_form = PropriedadeForm(request.POST, instance=propriedade)
            if propriedade_form.is_valid():
                propriedade = propriedade_form.save(commit=False)
                propriedade.usuario = request.user
                propriedade.save()
                messages.success(request, 'Informações da propriedade salvas com sucesso!')
                return redirect('preencher_informacoes')
    
    return render(request, 'settings.html', {
        'perfil_form': perfil_form,
        'senha_form': senha_form,
        'form': propriedade_form,
        'user': request.user
    })


@login_required
def preencher_informacoes_view(request):
    """View para preencher ou editar informações básicas da propriedade"""
    return settings_view(request)


@login_required
def lotes_view(request):
    """View para gerenciar lotes e projeções"""
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        propriedade = None
        messages.warning(request, 'É necessário cadastrar a propriedade primeiro.')
        return redirect('preencher_informacoes')
    
    # Busca lotes da propriedade
    lotes = Lote.objects.filter(propriedade=propriedade).order_by('nome')
    
    lote_form = LoteForm()
    projecao_form = ProjecaoGanhoForm(propriedade=propriedade)
    
    # Processa formulários
    if request.method == 'POST':
        if 'save_lote' in request.POST:
            lote_form = LoteForm(request.POST)
            if lote_form.is_valid():
                lote = lote_form.save(commit=False)
                lote.propriedade = propriedade
                lote.save()
                messages.success(request, f'Lote "{lote.nome}" cadastrado com sucesso!')
                return redirect('lotes')
        
        elif 'save_projecao' in request.POST:
            projecao_form = ProjecaoGanhoForm(request.POST, propriedade=propriedade)
            if projecao_form.is_valid():
                projecao_form.save()
                messages.success(request, 'Projeção de ganho salva com sucesso!')
                return redirect('lotes')
    
    return render(request, 'lotes.html', {
        'lote_form': lote_form,
        'projecao_form': projecao_form,
        'lotes': lotes,
        'user': request.user
    })


@login_required
def deletar_lote(request, lote_id):
    """View para deletar um lote"""
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
        lote = get_object_or_404(Lote, id=lote_id, propriedade=propriedade)
        nome_lote = lote.nome
        lote.delete()
        messages.success(request, f'Lote "{nome_lote}" deletado com sucesso!')
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        messages.error(request, 'Propriedade não encontrada.')
    except Exception as e:
        messages.error(request, f'Erro ao deletar lote: {str(e)}')
    
    return redirect('lotes')


@login_required
def deletar_projecao(request, projecao_id):
    """View para deletar uma projeção de ganho"""
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
        projecao = get_object_or_404(ProjecaoGanho, id=projecao_id, lote__propriedade=propriedade)
        projecao.delete()
        messages.success(request, 'Projeção de ganho deletada com sucesso!')
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        messages.error(request, 'Propriedade não encontrada.')
    except Exception as e:
        messages.error(request, f'Erro ao deletar projeção: {str(e)}')
    
    return redirect('lotes')


@login_required
def lotes_dashboard_view(request):
    """View para exibir dashboard com projeções de peso dos lotes"""
    from calendar import monthrange
    from decimal import Decimal
    import json
    
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        propriedade = None
        messages.warning(request, 'É necessário cadastrar a propriedade primeiro.')
        return redirect('preencher_informacoes')
    
    # Busca lotes da propriedade com projeções
    lotes = Lote.objects.filter(propriedade=propriedade).prefetch_related('projecoes_ganho').order_by('nome')
    
    # Dados para o gráfico e lista
    projecoes_dados = []
    cores_lotes = [
        '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
        '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
    ]
    
    # Para cada lote, calcular projeções
    for idx, lote in enumerate(lotes):
        if not lote.projecoes_ganho.exists():
            continue
            
        cor = cores_lotes[idx % len(cores_lotes)]
        projecoes_lote = lote.projecoes_ganho.all().order_by('ano', 'mes')
        
        # Peso inicial do lote
        peso_atual = Decimal(str(lote.peso_kg))
        peso_inicial = peso_atual
        
        # Agrupar projeções por ano
        projecoes_por_ano = {}
        for projecao in projecoes_lote:
            if projecao.ano not in projecoes_por_ano:
                projecoes_por_ano[projecao.ano] = []
            projecoes_por_ano[projecao.ano].append(projecao)
        
        # Calcular projeções para cada ano
        dados_lote = {
            'lote_id': lote.id,
            'lote_nome': lote.nome,
            'cor': cor,
            'peso_inicial': float(peso_inicial),
            'projecoes': []
        }
        
        for ano, projecoes in sorted(projecoes_por_ano.items()):
            peso_acumulado = peso_inicial
            
            for projecao in sorted(projecoes, key=lambda x: x.mes):
                # Calcular dias do mês
                dias_mes = monthrange(ano, projecao.mes)[1]
                
                # Calcular ganho do mês: GMD * dias
                ganho_mes = Decimal(str(projecao.gmd_kg)) * Decimal(dias_mes)
                
                # Peso projetado = peso acumulado + ganho do mês
                peso_projetado = peso_acumulado + ganho_mes
                
                dados_lote['projecoes'].append({
                    'ano': ano,
                    'mes': projecao.mes,
                    'mes_nome': projecao.get_mes_display(),
                    'gmd': float(projecao.gmd_kg),
                    'dias_mes': dias_mes,
                    'ganho_mes': float(ganho_mes),
                    'peso_projetado': float(peso_projetado),
                    'peso_arroba_projetado': float(peso_projetado / Decimal('15'))
                })
                
                peso_acumulado = peso_projetado
        
        if dados_lote['projecoes']:
            projecoes_dados.append(dados_lote)
    
    # Preparar dados para Chart.js
    chart_data = {
        'labels': [],
        'datasets': []
    }
    
    # Coletar todos os meses/anos únicos
    meses_unicos = set()
    for lote_data in projecoes_dados:
        for proj in lote_data['projecoes']:
            meses_unicos.add((proj['ano'], proj['mes'], proj['mes_nome']))
    
    # Ordenar meses
    meses_ordenados = sorted(meses_unicos, key=lambda x: (x[0], x[1]))
    chart_data['labels'] = [f"{mes[2]}/{mes[0]}" for mes in meses_ordenados]
    
    # Criar dataset para cada lote
    for lote_data in projecoes_dados:
        dados_peso = []
        for mes_ord in meses_ordenados:
            # Encontrar projeção correspondente
            projecao_encontrada = None
            for proj in lote_data['projecoes']:
                if proj['ano'] == mes_ord[0] and proj['mes'] == mes_ord[1]:
                    projecao_encontrada = proj
                    break
            
            if projecao_encontrada:
                dados_peso.append(projecao_encontrada['peso_projetado'])
            else:
                # Se não houver projeção, usar None para não conectar no gráfico
                dados_peso.append(None)
        
        chart_data['datasets'].append({
            'label': lote_data['lote_nome'],
            'data': dados_peso,
            'borderColor': lote_data['cor'],
            'backgroundColor': lote_data['cor'] + '20',
            'tension': 0.4,
            'fill': False
        })
    
    return render(request, 'lotes_dashboard.html', {
        'lotes': lotes,
        'projecoes_dados': projecoes_dados,
        'chart_data_json': json.dumps(chart_data),
        'user': request.user
    })


@login_required
def home_view(request):
    # Verifica se as informações básicas foram preenchidas
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
        if not propriedade.informacoes_preenchidas():
            messages.warning(request, 'Por favor, complete o cadastro das informações básicas da propriedade.')
            return redirect('preencher_informacoes')
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        messages.warning(request, 'Por favor, complete o cadastro das informações básicas da propriedade.')
        return redirect('preencher_informacoes')
    
    return render(request, 'home.html', {'user': request.user})


@login_required
def nutricional_view(request):
    """View para gerenciar gastos nutricionais"""
    from datetime import datetime
    from decimal import Decimal
    
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        propriedade = None
        messages.warning(request, 'É necessário cadastrar a propriedade primeiro.')
        return redirect('preencher_informacoes')
    
    # Busca lotes da propriedade
    lotes = Lote.objects.filter(propriedade=propriedade).order_by('nome')
    
    # Ano e lote para exibição (padrão: ano atual)
    ano_atual = datetime.now().year
    ano = int(request.GET.get('ano', ano_atual))
    lote_id = request.GET.get('lote', None)
    lote_selecionado = None
    
    if lote_id:
        try:
            lote_selecionado = Lote.objects.get(id=int(lote_id), propriedade=propriedade)
        except (Lote.DoesNotExist, ValueError, TypeError):
            lote_selecionado = None
    
    # Processa formulário de múltiplos gastos
    if request.method == 'POST' and 'salvar_gastos' in request.POST:
        ano_post = int(request.POST.get('ano', ano_atual))
        lote_id_post = request.POST.get('lote_id', None)
        gastos_salvos = 0
        
        if lote_id_post:
            try:
                lote_post = Lote.objects.get(id=int(lote_id_post), propriedade=propriedade)
                for mes_num in range(1, 13):  # Janeiro a Dezembro
                    campo_key = f'gasto_mes_{mes_num}'
                    if campo_key in request.POST:
                        valor_str = request.POST[campo_key].strip()
                        if valor_str:
                            try:
                                gasto_diario = Decimal(valor_str)
                                if gasto_diario >= 0:
                                    gasto_nutricional, created = GastoNutricional.objects.update_or_create(
                                        lote=lote_post,
                                        mes=mes_num,
                                        ano=ano_post,
                                        defaults={'gasto_diario': gasto_diario}
                                    )
                                    gastos_salvos += 1
                            except (ValueError, TypeError, Exception):
                                pass
            except (Lote.DoesNotExist, ValueError, TypeError):
                pass
        
        if gastos_salvos > 0:
            messages.success(request, f'{gastos_salvos} gasto(s) nutricional(is) salvo(s) com sucesso!')
        else:
            messages.warning(request, 'Nenhum gasto nutricional foi salvo. Verifique os valores informados.')
        
        redirect_url = f'{request.path}?ano={ano_post}'
        if lote_id_post:
            redirect_url += f'&lote={lote_id_post}'
        return redirect(redirect_url)
    
    # Buscar gastos existentes para o lote e ano selecionados
    gastos_existentes = {}
    if lote_selecionado:
        for gasto in lote_selecionado.gastos_nutricionais.filter(ano=ano):
            gastos_existentes[gasto.mes] = float(gasto.gasto_diario)
    
    # Meses do ano
    meses_nomes = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    meses_lista = list(range(1, 13))
    anos_lista = list(range(2020, 2030))
    
    return render(request, 'nutricional.html', {
        'lotes': lotes,
        'ano': ano,
        'ano_atual': ano_atual,
        'lote_selecionado': lote_selecionado,
        'anos_lista': anos_lista,
        'meses_lista': meses_lista,
        'meses_nomes': meses_nomes,
        'gastos_existentes': gastos_existentes,
        'user': request.user
    })


@login_required
def deletar_gasto_nutricional(request, gasto_id):
    """View para deletar um gasto nutricional"""
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
        gasto = get_object_or_404(GastoNutricional, id=gasto_id, lote__propriedade=propriedade)
        gasto.delete()
        messages.success(request, 'Gasto nutricional deletado com sucesso!')
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        messages.error(request, 'Propriedade não encontrada.')
    except Exception as e:
        messages.error(request, f'Erro ao deletar gasto nutricional: {str(e)}')
    
    return redirect('nutricional')


@login_required
def nutricional_dashboard_view(request):
    """View para exibir dashboard com gastos nutricionais"""
    from calendar import monthrange
    from decimal import Decimal
    import json
    
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        propriedade = None
        messages.warning(request, 'É necessário cadastrar a propriedade primeiro.')
        return redirect('preencher_informacoes')
    
    # Busca lotes da propriedade com gastos nutricionais
    lotes = Lote.objects.filter(propriedade=propriedade).prefetch_related('gastos_nutricionais').order_by('nome')
    
    # Dados para o gráfico e lista
    gastos_dados = []
    cores_lotes = [
        '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
        '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
    ]
    
    # Para cada lote, calcular gastos
    for idx, lote in enumerate(lotes):
        if not lote.gastos_nutricionais.exists():
            continue
            
        cor = cores_lotes[idx % len(cores_lotes)]
        gastos_lote = lote.gastos_nutricionais.all().order_by('ano', 'mes')
        
        # Agrupar gastos por ano
        gastos_por_ano = {}
        for gasto in gastos_lote:
            if gasto.ano not in gastos_por_ano:
                gastos_por_ano[gasto.ano] = []
            gastos_por_ano[gasto.ano].append(gasto)
        
        # Calcular gastos para cada ano
        dados_lote = {
            'lote_id': lote.id,
            'lote_nome': lote.nome,
            'cor': cor,
            'gastos': []
        }
        
        for ano, gastos in sorted(gastos_por_ano.items()):
            for gasto in sorted(gastos, key=lambda x: x.mes):
                # Calcular dias do mês
                dias_mes = monthrange(ano, gasto.mes)[1]
                
                # Calcular gasto mensal por animal: gasto_diario * dias
                gasto_mensal = Decimal(str(gasto.gasto_diario)) * Decimal(dias_mes)
                
                # Calcular gasto total do lote: gasto_mensal * quantidade de animais
                quantidade_animais = Decimal(str(lote.quantidade))
                gasto_total_lote = gasto_mensal * quantidade_animais
                
                dados_lote['gastos'].append({
                    'ano': ano,
                    'mes': gasto.mes,
                    'mes_nome': gasto.get_mes_display(),
                    'gasto_diario': float(gasto.gasto_diario),
                    'dias_mes': dias_mes,
                    'gasto_mensal': float(gasto_mensal),
                    'quantidade_animais': int(lote.quantidade),
                    'gasto_total_lote': float(gasto_total_lote)
                })
        
        if dados_lote['gastos']:
            gastos_dados.append(dados_lote)
    
    # Preparar dados para Chart.js - Gasto por Animal
    chart_data_por_animal = {
        'labels': [],
        'datasets': []
    }
    
    # Preparar dados para Chart.js - Gasto Total por Lote
    chart_data_por_lote = {
        'labels': [],
        'datasets': []
    }
    
    # Coletar todos os meses/anos únicos
    meses_unicos = set()
    for lote_data in gastos_dados:
        for gasto in lote_data['gastos']:
            meses_unicos.add((gasto['ano'], gasto['mes'], gasto['mes_nome']))
    
    # Ordenar meses
    meses_ordenados = sorted(meses_unicos, key=lambda x: (x[0], x[1]))
    labels_meses = [f"{mes[2]}/{mes[0]}" for mes in meses_ordenados]
    chart_data_por_animal['labels'] = labels_meses
    chart_data_por_lote['labels'] = labels_meses
    
    # Calcular totais mensais
    totais_mensais = {}
    for mes_ord in meses_ordenados:
        totais_mensais[mes_ord] = Decimal('0')
    
    # Criar dataset para cada lote - Gasto por Animal
    for lote_data in gastos_dados:
        dados_gasto_animal = []
        dados_gasto_lote = []
        for mes_ord in meses_ordenados:
            # Encontrar gasto correspondente
            gasto_encontrado = None
            for gasto in lote_data['gastos']:
                if gasto['ano'] == mes_ord[0] and gasto['mes'] == mes_ord[1]:
                    gasto_encontrado = gasto
                    break
            
            if gasto_encontrado:
                dados_gasto_animal.append(gasto_encontrado['gasto_mensal'])
                dados_gasto_lote.append(gasto_encontrado['gasto_total_lote'])
                # Somar ao total mensal
                totais_mensais[mes_ord] += Decimal(str(gasto_encontrado['gasto_total_lote']))
            else:
                dados_gasto_animal.append(None)
                dados_gasto_lote.append(None)
        
        chart_data_por_animal['datasets'].append({
            'label': lote_data['lote_nome'],
            'data': dados_gasto_animal,
            'borderColor': lote_data['cor'],
            'backgroundColor': lote_data['cor'] + '20',
            'tension': 0.4,
            'fill': False
        })
        
        chart_data_por_lote['datasets'].append({
            'label': lote_data['lote_nome'],
            'data': dados_gasto_lote,
            'borderColor': lote_data['cor'],
            'backgroundColor': lote_data['cor'] + '20',
            'tension': 0.4,
            'fill': False
        })
    
    # Adicionar linha de TOTAL ao gráfico por lote
    dados_total = []
    for mes_ord in meses_ordenados:
        dados_total.append(float(totais_mensais[mes_ord]))
    
    chart_data_por_lote['datasets'].append({
        'label': 'TOTAL',
        'data': dados_total,
        'borderColor': '#000000',
        'backgroundColor': '#00000020',
        'tension': 0.4,
        'fill': False,
        'borderWidth': 3,
        'borderDash': [5, 5]
    })
    
    # Preparar dados para tabela de gastos por lote (meses como colunas)
    tabela_gastos_por_lote = []
    for lote_data in gastos_dados:
        linha_lote = {
            'lote_nome': lote_data['lote_nome'],
            'gastos_por_mes': {}
        }
        for gasto in lote_data['gastos']:
            chave_mes = f"{gasto['mes_nome']}/{gasto['ano']}"
            linha_lote['gastos_por_mes'][chave_mes] = gasto['gasto_total_lote']
        tabela_gastos_por_lote.append(linha_lote)
    
    # Criar lista de meses ordenados para as colunas
    meses_colunas = [f"{mes[2]}/{mes[0]}" for mes in meses_ordenados]
    
    return render(request, 'nutricional_dashboard.html', {
        'lotes': lotes,
        'gastos_dados': gastos_dados,
        'chart_data_por_animal_json': json.dumps(chart_data_por_animal),
        'chart_data_por_lote_json': json.dumps(chart_data_por_lote),
        'totais_mensais': {f"{mes[2]}/{mes[0]}": float(totais_mensais[mes]) for mes in meses_ordenados},
        'tabela_gastos_por_lote': tabela_gastos_por_lote,
        'meses_colunas': meses_colunas,
        'user': request.user
    })


@login_required
def faturamento_view(request):
    """View para exibir planilha de faturamento com ganho de peso e evolução"""
    from calendar import monthrange
    from decimal import Decimal
    import json
    
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        propriedade = None
        messages.warning(request, 'É necessário cadastrar a propriedade primeiro.')
        return redirect('preencher_informacoes')
    
    # Busca lotes da propriedade com projeções
    lotes = Lote.objects.filter(propriedade=propriedade).prefetch_related('projecoes_ganho').order_by('nome')
    
    # Processa formulário de GMD
    gmd_por_lote = {}
    if request.method == 'POST' and 'calcular_faturamento' in request.POST:
        # Capturar aba ativa do POST
        active_tab = request.POST.get('active_tab', 'gmd')
        for lote in lotes:
            gmd_key = f'gmd_lote_{lote.id}'
            if gmd_key in request.POST:
                gmd_str = request.POST[gmd_key].strip()
                # Verificar se o valor não está vazio
                if gmd_str:
                    try:
                        gmd_value = Decimal(gmd_str)
                        if gmd_value > 0:
                            gmd_por_lote[lote.id] = gmd_value
                            # Salvar o último GMD usado no lote
                            lote.ultimo_gmd_usado = gmd_value
                            lote.save(update_fields=['ultimo_gmd_usado', 'data_atualizacao'])
                    except (ValueError, TypeError, Exception):
                        # Ignorar valores inválidos
                        pass
        # Redirecionar para manter a aba ativa
        from django.urls import reverse
        redirect_url = reverse('faturamento')
        redirect_url += f'?tab={active_tab}'
        return redirect(redirect_url)
    
    # Processa formulário de Rendimento de Carcaça
    rendimento_percentual = None
    if request.method == 'POST' and 'calcular_rendimento' in request.POST:
        # Capturar aba ativa do POST
        active_tab = request.POST.get('active_tab', 'rendimento')
        if 'rendimento_carcaca' in request.POST:
            rendimento_str = request.POST['rendimento_carcaca'].strip()
            # Verificar se o valor não está vazio
            if rendimento_str:
                try:
                    rendimento_value = Decimal(rendimento_str)
                    if 0 < rendimento_value <= 100:
                        rendimento_percentual = rendimento_value
                        # Salvar o último rendimento usado na propriedade
                        propriedade.ultimo_rendimento_carcaca = rendimento_percentual
                        propriedade.save(update_fields=['ultimo_rendimento_carcaca', 'data_atualizacao'])
                except (ValueError, TypeError, Exception):
                    # Ignorar valores inválidos
                    pass
        # Redirecionar para manter a aba ativa
        from django.urls import reverse
        redirect_url = reverse('faturamento')
        redirect_url += f'?tab={active_tab}'
        return redirect(redirect_url)
    else:
        # Usar o último rendimento salvo se existir
        if propriedade.ultimo_rendimento_carcaca:
            rendimento_percentual = propriedade.ultimo_rendimento_carcaca
    
    # Processa formulário de Valor da @
    valor_arroba_por_lote = {}
    if request.method == 'POST' and 'calcular_faturamento_valor' in request.POST:
        # Capturar aba ativa do POST
        active_tab = request.POST.get('active_tab', 'faturamento')
        for lote in lotes:
            valor_key = f'valor_arroba_lote_{lote.id}'
            if valor_key in request.POST:
                valor_str = request.POST[valor_key].strip()
                # Verificar se o valor não está vazio
                if valor_str:
                    try:
                        valor_arroba = Decimal(valor_str)
                        if valor_arroba > 0:
                            valor_arroba_por_lote[lote.id] = valor_arroba
                            # Salvar o último valor da @ usado no lote
                            lote.ultimo_valor_arroba = valor_arroba
                            lote.save(update_fields=['ultimo_valor_arroba', 'data_atualizacao'])
                    except (ValueError, TypeError, Exception):
                        # Ignorar valores inválidos
                        pass
        # Redirecionar para manter a aba ativa
        from django.urls import reverse
        redirect_url = reverse('faturamento')
        redirect_url += f'?tab={active_tab}'
        return redirect(redirect_url)
    
    # Capturar aba ativa do GET (para requisições normais)
    active_tab = request.GET.get('tab', 'gmd')
    
    # Se não houver GMD preenchido no POST, buscar os valores salvos do banco
    if len(gmd_por_lote) == 0:
        # Recarregar lotes do banco para garantir valores atualizados
        lotes = Lote.objects.filter(propriedade=propriedade).prefetch_related('projecoes_ganho').order_by('nome')
        # Buscar GMDs salvos dos lotes
        for lote in lotes:
            if lote.ultimo_gmd_usado:
                gmd_por_lote[lote.id] = lote.ultimo_gmd_usado
    
    # Se não houver GMD preenchido, usar os GMDs das projeções existentes
    usar_gmd_projecoes = len(gmd_por_lote) == 0
    
    # Coletar todos os meses/anos únicos de todas as projeções
    meses_unicos = set()
    for lote in lotes:
        for projecao in lote.projecoes_ganho.all():
            meses_unicos.add((projecao.ano, projecao.mes, projecao.get_mes_display()))
    
    # Ordenar meses
    meses_ordenados = sorted(meses_unicos, key=lambda x: (x[0], x[1]))
    
    # Preparar dados para as tabelas
    tabela_ganho = []  # Ganho de peso por mês (GMD * dias)
    tabela_evolucao = []  # Evolução do peso (peso inicial + ganhos acumulados)
    
    # Abreviações dos meses
    meses_abrev = {
        'Janeiro': 'Jan', 'Fevereiro': 'Fev', 'Março': 'Mar', 'Abril': 'Abr',
        'Maio': 'Mai', 'Junho': 'Jun', 'Julho': 'Jul', 'Agosto': 'Ago',
        'Setembro': 'Set', 'Outubro': 'Out', 'Novembro': 'Nov', 'Dezembro': 'Dez'
    }
    
    # Dados para gráficos
    chart_data_evolucao = {
        'labels': [],
        'datasets': []
    }
    chart_data_ganho = {
        'labels': [],
        'datasets': []
    }
    cores_lotes = [
        '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
        '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
    ]
    
    gmd_usado = None  # Para exibir o GMD usado na tabela
    
    for idx, lote in enumerate(lotes):
        if not lote.projecoes_ganho.exists():
            continue
        
        peso_inicial = Decimal(str(lote.peso_kg))
        
        # Determinar GMD a usar
        if usar_gmd_projecoes:
            # Usar o primeiro GMD encontrado nas projeções (ou média)
            projecoes_lote = lote.projecoes_ganho.all().order_by('ano', 'mes')
            if projecoes_lote.exists():
                # Usar o GMD da primeira projeção como referência
                gmd_usado = Decimal(str(projecoes_lote.first().gmd_kg))
            else:
                continue
        else:
            # Usar GMD preenchido no formulário
            if lote.id in gmd_por_lote:
                gmd_usado = gmd_por_lote[lote.id]
            else:
                # Se não houver GMD para este lote, usar das projeções
                projecoes_lote = lote.projecoes_ganho.all().order_by('ano', 'mes')
                if projecoes_lote.exists():
                    gmd_usado = Decimal(str(projecoes_lote.first().gmd_kg))
                else:
                    continue
        
        # Dados para a linha do lote - Ganho de Peso
        linha_ganho = {
            'lote_nome': lote.nome,
            'peso_entrada': float(peso_inicial),
            'ganhos_por_mes': {}
        }
        
        # Dados para a linha do lote - Evolução do Peso
        linha_evolucao = {
            'lote_nome': lote.nome,
            'peso_entrada': float(peso_inicial),
            'pesos_por_mes': {}
        }
        
        # Agrupar projeções por ano
        projecoes_por_ano = {}
        for projecao in lote.projecoes_ganho.all().order_by('ano', 'mes'):
            if projecao.ano not in projecoes_por_ano:
                projecoes_por_ano[projecao.ano] = []
            projecoes_por_ano[projecao.ano].append(projecao)
        
        # Calcular ganhos e evolução
        peso_acumulado = peso_inicial
        
        for ano, projecoes in sorted(projecoes_por_ano.items()):
            for projecao in sorted(projecoes, key=lambda x: x.mes):
                # Calcular dias do mês
                dias_mes = monthrange(ano, projecao.mes)[1]
                
                # Calcular ganho do mês: GMD * dias (usar GMD preenchido ou da projeção)
                if usar_gmd_projecoes:
                    gmd_mes = Decimal(str(projecao.gmd_kg))
                else:
                    gmd_mes = gmd_usado
                
                ganho_mes = gmd_mes * Decimal(dias_mes)
                
                # Peso acumulado = peso anterior + ganho do mês
                peso_acumulado = peso_acumulado + ganho_mes
                
                # Chave para identificar o mês
                chave_mes = (ano, projecao.mes)
                
                # Armazenar ganho do mês
                linha_ganho['ganhos_por_mes'][chave_mes] = float(ganho_mes)
                
                # Armazenar peso acumulado
                linha_evolucao['pesos_por_mes'][chave_mes] = float(peso_acumulado)
        
        tabela_ganho.append(linha_ganho)
        tabela_evolucao.append(linha_evolucao)
    
    # Preparar dados dos gráficos após processar todos os lotes
    # Criar labels únicos baseados em todos os meses ordenados
    if meses_ordenados:
        labels_meses = [f"{mes[2]}/{mes[0]}" for mes in meses_ordenados]
        chart_data_evolucao['labels'] = labels_meses
        chart_data_ganho['labels'] = labels_meses
        
        # Para cada lote, criar dados dos gráficos
        for idx, (linha_ganho, linha_evolucao) in enumerate(zip(tabela_ganho, tabela_evolucao)):
            dados_peso_grafico = []
            dados_ganho_grafico = []
            
            for mes_ord in meses_ordenados:
                chave_mes = (mes_ord[0], mes_ord[1])
                
                # Dados de evolução (peso acumulado)
                if chave_mes in linha_evolucao['pesos_por_mes']:
                    dados_peso_grafico.append(linha_evolucao['pesos_por_mes'][chave_mes])
                else:
                    dados_peso_grafico.append(None)
                
                # Dados de ganho mensal
                if chave_mes in linha_ganho['ganhos_por_mes']:
                    dados_ganho_grafico.append(linha_ganho['ganhos_por_mes'][chave_mes])
                else:
                    dados_ganho_grafico.append(None)
            
            if dados_peso_grafico:
                cor = cores_lotes[idx % len(cores_lotes)]
                chart_data_evolucao['datasets'].append({
                    'label': linha_evolucao['lote_nome'],
                    'data': dados_peso_grafico,
                    'borderColor': cor,
                    'backgroundColor': cor + '20',
                    'tension': 0.4,
                    'fill': False
                })
            
            if dados_ganho_grafico:
                cor = cores_lotes[idx % len(cores_lotes)]
                chart_data_ganho['datasets'].append({
                    'label': linha_ganho['lote_nome'],
                    'data': dados_ganho_grafico,
                    'borderColor': cor,
                    'backgroundColor': cor + '20',
                    'tension': 0.4,
                    'fill': False
                })
    
    # Preparar dados dos meses para o template
    meses_dados = []
    for mes_ord in meses_ordenados:
        ano, mes_num, mes_nome = mes_ord
        dias_mes = monthrange(ano, mes_num)[1]
        meses_dados.append({
            'ano': ano,
            'mes': mes_num,
            'mes_nome': mes_nome,
            'mes_abrev': meses_abrev.get(mes_nome, mes_nome[:3]),
            'dias': dias_mes,
            'chave': (ano, mes_num)
        })
    
    # GMD usado (primeiro valor encontrado ou do formulário)
    gmd_display = None
    if gmd_por_lote:
        gmd_display = float(list(gmd_por_lote.values())[0])
    elif tabela_ganho:
        # Pegar o primeiro GMD calculado
        primeiro_lote = lotes.filter(projecoes_ganho__isnull=False).first()
        if primeiro_lote:
            primeira_projecao = primeiro_lote.projecoes_ganho.all().order_by('ano', 'mes').first()
            if primeira_projecao:
                gmd_display = float(primeira_projecao.gmd_kg)
    
    # Preparar GMDs salvos para pré-preencher o formulário
    gmd_salvos = {}
    for lote in lotes:
        if lote.ultimo_gmd_usado:
            gmd_salvos[lote.id] = float(lote.ultimo_gmd_usado)
    
    # Calcular rendimento de carcaça
    tabela_rendimento = []
    # Criar um dicionário para mapear nome do lote para o objeto Lote
    lotes_dict = {lote.nome: lote for lote in lotes}
    
    if rendimento_percentual and tabela_evolucao:
        for linha_evolucao in tabela_evolucao:
            # Pegar o último peso (último mês da evolução)
            if linha_evolucao['pesos_por_mes']:
                # Ordenar as chaves (ano, mês) para pegar o último
                chaves_ordenadas = sorted(linha_evolucao['pesos_por_mes'].keys(), key=lambda x: (x[0], x[1]))
                if chaves_ordenadas:
                    ultima_chave = chaves_ordenadas[-1]
                    peso_final = Decimal(str(linha_evolucao['pesos_por_mes'][ultima_chave]))
                    
                    # Calcular rendimento em arrobas: 
                    # 1. Calcular peso da carcaça: peso_final * (rendimento_percentual / 100)
                    # 2. Converter para arrobas: peso_carcaca / 15
                    peso_carcaca = peso_final * (rendimento_percentual / Decimal('100'))
                    rendimento_carcaca = peso_carcaca / Decimal('15')
                    
                    # Buscar o lote correspondente para pegar a quantidade
                    lote_obj = lotes_dict.get(linha_evolucao['lote_nome'])
                    quantidade_animais = lote_obj.quantidade if lote_obj else 0
                    
                    # Calcular total: quantidade * rendimento_carcaca
                    total_rendimento = Decimal(str(quantidade_animais)) * rendimento_carcaca
                    
                    tabela_rendimento.append({
                        'lote_nome': linha_evolucao['lote_nome'],
                        'lote_id': lote_obj.id if lote_obj else None,
                        'peso_final': float(peso_final),
                        'rendimento_carcaca': float(rendimento_carcaca),
                        'quantidade_animais': quantidade_animais,
                        'total_rendimento': float(total_rendimento)
                    })
    
    # Calcular faturamento
    tabela_faturamento = []
    valor_arroba_salvos = {}
    
    if tabela_rendimento:
        for linha_rendimento in tabela_rendimento:
            lote_id = linha_rendimento.get('lote_id')
            if lote_id:
                # Buscar valor da @ (do formulário ou salvo)
                valor_arroba = None
                if lote_id in valor_arroba_por_lote:
                    valor_arroba = valor_arroba_por_lote[lote_id]
                else:
                    # Usar valor salvo se existir
                    lote_obj = lotes_dict.get(linha_rendimento['lote_nome'])
                    if lote_obj and lote_obj.ultimo_valor_arroba:
                        valor_arroba = lote_obj.ultimo_valor_arroba
                
                if valor_arroba:
                    # Calcular faturamento: valor_arroba * total_rendimento
                    faturamento = Decimal(str(valor_arroba)) * Decimal(str(linha_rendimento['total_rendimento']))
                    
                    tabela_faturamento.append({
                        'lote_nome': linha_rendimento['lote_nome'],
                        'lote_id': lote_id,
                        'valor_arroba': float(valor_arroba),
                        'faturamento': float(faturamento)
                    })
                
                # Preparar valores salvos para pré-preencher formulário
                lote_obj = lotes_dict.get(linha_rendimento['lote_nome'])
                if lote_obj and lote_obj.ultimo_valor_arroba:
                    valor_arroba_salvos[lote_id] = float(lote_obj.ultimo_valor_arroba)
    
    return render(request, 'faturamento.html', {
        'lotes': lotes,
        'tabela_ganho': tabela_ganho,
        'tabela_evolucao': tabela_evolucao,
        'meses_dados': meses_dados,
        'gmd_display': gmd_display,
        'gmd_salvos': gmd_salvos,
        'rendimento_percentual': float(rendimento_percentual) if rendimento_percentual else None,
        'tabela_rendimento': tabela_rendimento,
        'tabela_faturamento': tabela_faturamento,
        'valor_arroba_salvos': valor_arroba_salvos,
        'chart_data_evolucao_json': json.dumps(chart_data_evolucao),
        'chart_data_ganho_json': json.dumps(chart_data_ganho),
        'active_tab': active_tab,
        'user': request.user
    })


@login_required
def fluxo_caixa_view(request):
    """View para exibir e gerenciar o fluxo de caixa"""
    from calendar import monthrange
    from decimal import Decimal
    from datetime import datetime
    
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        propriedade = None
        messages.warning(request, 'É necessário cadastrar a propriedade primeiro.')
        return redirect('preencher_informacoes')
    
    # Processar formulários de custos fixos e receitas
    if request.method == 'POST':
        # Processar custos fixos
        if 'salvar_custos_fixos' in request.POST:
            ano = int(request.POST.get('ano', datetime.now().year))
            for tipo in CustoFixo.TIPO_CHOICES:
                tipo_key = tipo[0]
                for mes_num in range(1, 13):
                    campo_key = f'custo_fixo_{tipo_key}_{mes_num}'
                    if campo_key in request.POST:
                        valor_str = request.POST[campo_key].strip()
                        if valor_str:
                            try:
                                valor = Decimal(valor_str)
                                if valor >= 0:
                                    custo_fixo, created = CustoFixo.objects.update_or_create(
                                        propriedade=propriedade,
                                        tipo=tipo_key,
                                        mes=mes_num,
                                        ano=ano,
                                        defaults={'valor': valor}
                                    )
                            except (ValueError, TypeError, Exception):
                                pass
        
        # Processar receitas
        if 'salvar_receitas' in request.POST:
            ano = int(request.POST.get('ano', datetime.now().year))
            for tipo in Receita.TIPO_CHOICES:
                tipo_key = tipo[0]
                for mes_num in range(1, 13):
                    campo_key = f'receita_{tipo_key}_{mes_num}'
                    if campo_key in request.POST:
                        valor_str = request.POST[campo_key].strip()
                        if valor_str:
                            try:
                                valor = Decimal(valor_str)
                                if valor >= 0:
                                    receita, created = Receita.objects.update_or_create(
                                        propriedade=propriedade,
                                        tipo=tipo_key,
                                        mes=mes_num,
                                        ano=ano,
                                        defaults={'valor': valor}
                                    )
                            except (ValueError, TypeError, Exception):
                                pass
        
        messages.success(request, 'Dados salvos com sucesso!')
        return redirect('fluxo_caixa')
    
    # Ano para exibição (padrão: ano atual)
    ano_atual = datetime.now().year
    ano = int(request.GET.get('ano', ano_atual))
    
    # Buscar lotes para calcular investimentos
    lotes = Lote.objects.filter(propriedade=propriedade)
    investimento_animais = sum(lote.valor_compra for lote in lotes if lote.valor_compra)
    
    # Buscar dados nutricionais (totais mensais)
    gastos_nutricionais = GastoNutricional.objects.filter(
        lote__propriedade=propriedade,
        ano=ano
    ).select_related('lote')
    
    # Calcular totais mensais de alimentação
    alimentacao_mensal = {}
    for mes_num in range(1, 13):
        total_mes = Decimal('0')
        for gasto in gastos_nutricionais.filter(mes=mes_num):
            dias_mes = monthrange(ano, mes_num)[1]
            gasto_mensal = gasto.gasto_diario * Decimal(dias_mes)
            gasto_total_lote = gasto_mensal * Decimal(str(gasto.lote.quantidade))
            total_mes += gasto_total_lote
        alimentacao_mensal[mes_num] = float(total_mes)
    
    # Buscar receitas cadastradas
    receitas_cadastradas = Receita.objects.filter(propriedade=propriedade, ano=ano)
    receitas_por_mes = {}
    for mes_num in range(1, 13):
        receitas_por_mes[mes_num] = {}
        for tipo in Receita.TIPO_CHOICES:
            receita = receitas_cadastradas.filter(mes=mes_num, tipo=tipo[0]).first()
            receitas_por_mes[mes_num][tipo[0]] = float(receita.valor) if receita else 0.0
    
    # Calcular total de receitas por mês
    total_receitas_mensal = {}
    for mes_num in range(1, 13):
        total = sum(receitas_por_mes[mes_num].values())
        total_receitas_mensal[mes_num] = total
    
    # Buscar custos fixos
    custos_fixos_cadastrados = CustoFixo.objects.filter(propriedade=propriedade, ano=ano)
    custos_fixos_por_mes = {}
    for mes_num in range(1, 13):
        custos_fixos_por_mes[mes_num] = {}
        total_custo_fixo = Decimal('0')
        for tipo in CustoFixo.TIPO_CHOICES:
            custo = custos_fixos_cadastrados.filter(mes=mes_num, tipo=tipo[0]).first()
            valor = float(custo.valor) if custo else 0.0
            custos_fixos_por_mes[mes_num][tipo[0]] = valor
            total_custo_fixo += Decimal(str(valor))
        custos_fixos_por_mes[mes_num]['total'] = float(total_custo_fixo)
    
    # Calcular custos variáveis
    custos_variaveis_por_mes = {}
    for mes_num in range(1, 13):
        alimentacao = Decimal(str(alimentacao_mensal.get(mes_num, 0)))
        sanitario_med = alimentacao * Decimal('0.01')  # 1% da alimentação
        receita_mes = Decimal(str(total_receitas_mensal.get(mes_num, 0)))
        servicos_outros = receita_mes * Decimal('0.01')  # 1% da receita
        impostos = receita_mes * Decimal('0.015')  # 1.5% da receita
        
        total_variavel = alimentacao + sanitario_med + servicos_outros + impostos
        
        custos_variaveis_por_mes[mes_num] = {
            'alimentacao': float(alimentacao),
            'sanitario_med': float(sanitario_med),
            'servicos_outros': float(servicos_outros),
            'impostos': float(impostos),
            'total': float(total_variavel)
        }
    
    # Calcular fluxo de caixa livre e acumulado
    fluxo_livre = {}
    fluxo_acum = Decimal('0')
    fluxo_acumulado = {}
    
    # Investimento inicial (coluna 0)
    fluxo_acum = Decimal(str(investimento_animais)) * Decimal('-1')
    fluxo_acumulado[0] = float(fluxo_acum)
    
    # Para cada mês
    for mes_num in range(1, 13):
        receitas = Decimal(str(total_receitas_mensal.get(mes_num, 0)))
        custos_fixos = Decimal(str(custos_fixos_por_mes[mes_num].get('total', 0)))
        custos_variaveis = Decimal(str(custos_variaveis_por_mes[mes_num].get('total', 0)))
        
        # Fluxo livre = Receitas - Custos Fixos - Custos Variáveis
        fluxo_livre_mes = receitas - custos_fixos - custos_variaveis
        fluxo_livre[mes_num] = float(fluxo_livre_mes)
        
        # Fluxo acumulado
        fluxo_acum += fluxo_livre_mes
        fluxo_acumulado[mes_num] = float(fluxo_acum)
    
    # Preparar dados para o template
    meses_abrev = {
        1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
        7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'
    }
    
    meses_nomes = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    # Lista de meses para o template
    meses_lista = list(range(1, 12))  # 1 a 11 (janeiro a novembro)
    anos_lista = list(range(2024, 2029))  # 2024 a 2028
    
    # Calcular resumo anual
    total_custos_fixos = Decimal('0')
    total_custos_variaveis = Decimal('0')
    total_faturamento = Decimal('0')
    
    for mes_num in range(1, 12):  # Janeiro a Novembro
        total_custos_fixos += Decimal(str(custos_fixos_por_mes[mes_num].get('total', 0)))
        total_custos_variaveis += Decimal(str(custos_variaveis_por_mes[mes_num].get('total', 0)))
        total_faturamento += Decimal(str(total_receitas_mensal.get(mes_num, 0)))
    
    # Calcular valores do resumo
    investimentos_total = Decimal(str(investimento_animais))
    desembolso = investimentos_total + total_custos_fixos + total_custos_variaveis
    resultado = total_faturamento - desembolso
    
    # Calcular percentuais
    rentabilidade = (resultado / investimentos_total * Decimal('100')) if investimentos_total > 0 else Decimal('0')
    lucratividade = (resultado / total_faturamento * Decimal('100')) if total_faturamento > 0 else Decimal('0')
    
    resumo = {
        'investimentos': float(investimentos_total),
        'custos_fixos': float(total_custos_fixos),
        'custos_variaveis': float(total_custos_variaveis),
        'desembolso': float(desembolso),
        'faturamento': float(total_faturamento),
        'resultado': float(resultado),
        'rentabilidade': float(rentabilidade),
        'lucratividade': float(lucratividade)
    }
    
    return render(request, 'fluxo_caixa.html', {
        'propriedade': propriedade,
        'ano': ano,
        'ano_atual': ano_atual,
        'anos_lista': anos_lista,
        'meses_lista': meses_lista,
        'investimento_animais': float(investimento_animais),
        'alimentacao_mensal': alimentacao_mensal,
        'receitas_por_mes': receitas_por_mes,
        'total_receitas_mensal': total_receitas_mensal,
        'custos_fixos_por_mes': custos_fixos_por_mes,
        'custos_variaveis_por_mes': custos_variaveis_por_mes,
        'fluxo_livre': fluxo_livre,
        'fluxo_acumulado': fluxo_acumulado,
        'meses_abrev': meses_abrev,
        'meses_nomes': meses_nomes,
        'tipos_custo_fixo': CustoFixo.TIPO_CHOICES,
        'tipos_receita': Receita.TIPO_CHOICES,
        'resumo': resumo,
        'user': request.user
    })


@login_required
def ponto_equilibrio_view(request):
    """View para exibir e calcular o ponto de equilíbrio por lote e mês"""
    from calendar import monthrange
    from decimal import Decimal
    from datetime import datetime
    
    try:
        propriedade = Propriedade.objects.get(usuario=request.user)
    except (Propriedade.DoesNotExist, TypeError, ValueError):
        propriedade = None
        messages.warning(request, 'É necessário cadastrar a propriedade primeiro.')
        return redirect('preencher_informacoes')
    
    # Processar formulário de mortalidade
    if request.method == 'POST' and 'salvar_mortalidade' in request.POST:
        ano = int(request.POST.get('ano', datetime.now().year))
        for lote in Lote.objects.filter(propriedade=propriedade):
            for mes_num in range(1, 12):  # Janeiro a Novembro
                campo_key = f'mortalidade_lote_{lote.id}_mes_{mes_num}'
                if campo_key in request.POST:
                    valor_str = request.POST[campo_key].strip()
                    if valor_str:
                        try:
                            percentual = Decimal(valor_str)
                            if 0 <= percentual <= 100:
                                mortalidade, created = Mortalidade.objects.update_or_create(
                                    lote=lote,
                                    mes=mes_num,
                                    ano=ano,
                                    defaults={'percentual': percentual}
                                )
                        except (ValueError, TypeError, Exception):
                            pass
        messages.success(request, 'Mortalidade salva com sucesso!')
        return redirect('ponto_equilibrio')
    
    # Ano para exibição
    ano_atual = datetime.now().year
    ano = int(request.GET.get('ano', ano_atual))
    
    # Buscar lotes com projeções
    lotes = Lote.objects.filter(propriedade=propriedade).prefetch_related(
        'projecoes_ganho', 'gastos_nutricionais', 'mortalidades'
    ).order_by('nome')
    
    # Buscar rendimento da propriedade
    rendimento_percentual = propriedade.ultimo_rendimento_carcaca or Decimal('50')
    
    # Preparar dados para cada lote
    dados_lotes = []
    
    for lote in lotes:
        if not lote.projecoes_ganho.exists():
            continue
        
        # Dados do lote
        lote_data = {
            'lote_id': lote.id,
            'lote_nome': lote.nome,
            'quantidade': lote.quantidade,
            'meses': {}
        }
        
        # Peso inicial
        peso_inicial = Decimal(str(lote.peso_kg))
        peso_entrada_arroba = Decimal(str(lote.peso_arroba))
        
        # Investimento inicial em animais
        investimento_animais_inicial = Decimal(str(lote.valor_compra))
        
        # Agrupar projeções por ano
        projecoes_por_ano = {}
        for projecao in lote.projecoes_ganho.filter(ano=ano).order_by('mes'):
            if projecao.ano not in projecoes_por_ano:
                projecoes_por_ano[projecao.ano] = []
            projecoes_por_ano[projecao.ano].append(projecao)
        
        # Calcular dados por mês
        peso_atual = peso_inicial
        peso_entrada_arroba_atual = peso_entrada_arroba
        
        # Investimento em alimentação acumulado
        investimento_alimentacao_acumulado = Decimal('0')
        
        for mes_num in range(1, 12):  # Janeiro a Novembro
            # Buscar projeção para este mês
            projecao = None
            for proj in lote.projecoes_ganho.filter(ano=ano, mes=mes_num):
                projecao = proj
                break
            
            if not projecao:
                continue
            
            # Calcular dias do mês
            dias_mes = monthrange(ano, mes_num)[1]
            
            # Peso de entrada (kg e @)
            peso_entrada_kg = peso_atual
            peso_entrada_arroba = peso_entrada_arroba_atual
            
            # Ganho do mês
            ganho_mes = Decimal(str(projecao.gmd_kg)) * Decimal(dias_mes)
            
            # Peso de saída
            peso_saida_kg = peso_atual + ganho_mes
            
            # Buscar gasto nutricional do mês
            gasto_nutricional = None
            for gasto in lote.gastos_nutricionais.filter(ano=ano, mes=mes_num):
                gasto_nutricional = gasto
                break
            
            # Calcular investimento em alimentação do mês
            investimento_alimentacao_mes = Decimal('0')
            if gasto_nutricional:
                gasto_mensal = gasto_nutricional.gasto_diario * Decimal(dias_mes)
                investimento_alimentacao_mes = gasto_mensal * Decimal(str(lote.quantidade))
                # Acumular investimento em alimentação
                investimento_alimentacao_acumulado += investimento_alimentacao_mes
            
            # Investimento total (animais inicial + alimentação acumulada)
            investimento_total = investimento_animais_inicial + investimento_alimentacao_acumulado
            
            # Calcular rendimento em @ por animal
            peso_carcaca = peso_saida_kg * (rendimento_percentual / Decimal('100'))
            rendimento_arroba_por_animal = peso_carcaca / Decimal('15')
            
            # Buscar mortalidade
            mortalidade_percentual = Decimal('0')
            for mort in lote.mortalidades.filter(ano=ano, mes=mes_num):
                mortalidade_percentual = mort.percentual
                break
            
            # Calcular quantidade de animais considerando mortalidade
            quantidade_sobreviventes = Decimal(str(lote.quantidade)) * (Decimal('1') - mortalidade_percentual / Decimal('100'))
            
            # Total de @ (considerando mortalidade)
            total_arroba = quantidade_sobreviventes * rendimento_arroba_por_animal
            
            # Ponto de equilíbrio
            ponto_equilibrio = Decimal('0')
            if total_arroba > 0:
                ponto_equilibrio = investimento_total / total_arroba
            
            # Armazenar dados do mês
            lote_data['meses'][mes_num] = {
                'peso_entrada_kg': float(peso_entrada_kg),
                'peso_entrada_arroba': float(peso_entrada_arroba),
                'peso_saida_kg': float(peso_saida_kg),
                'ganho_peso_dia': float(projecao.gmd_kg),
                'custo_diaria': float(gasto_nutricional.gasto_diario) if gasto_nutricional else 0.0,
                'investimento_animais': float(investimento_animais_inicial),
                'investimento_alimentacao': float(investimento_alimentacao_acumulado),
                'investimento_total': float(investimento_total),
                'rendimento_arroba_por_animal': float(rendimento_arroba_por_animal),
                'mortalidade_percentual': float(mortalidade_percentual),
                'quantidade_sobreviventes': float(quantidade_sobreviventes),
                'total_arroba': float(total_arroba),
                'ponto_equilibrio': float(ponto_equilibrio),
                'dias_mes': dias_mes
            }
            
            # Atualizar para próximo mês
            peso_atual = peso_saida_kg
            peso_entrada_arroba_atual = peso_saida_kg / Decimal('15')
            # Investimento em animais acumula (mantém o mesmo valor inicial por enquanto)
            # Na prática, poderia considerar valorização do animal
        
        if lote_data['meses']:
            dados_lotes.append(lote_data)
    
    # Meses abreviados
    meses_abrev = {
        1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
        7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov'
    }
    
    meses_nomes = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro'
    }
    
    meses_lista = list(range(1, 12))
    anos_lista = list(range(2024, 2029))
    
    return render(request, 'ponto_equilibrio.html', {
        'propriedade': propriedade,
        'ano': ano,
        'ano_atual': ano_atual,
        'anos_lista': anos_lista,
        'meses_lista': meses_lista,
        'meses_abrev': meses_abrev,
        'meses_nomes': meses_nomes,
        'dados_lotes': dados_lotes,
        'rendimento_percentual': float(rendimento_percentual),
        'user': request.user
    })
