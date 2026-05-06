import csv
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Q
from .models import Toponym, ToponymCategory, Urbanonym, Hydronym, Choronym


def map_view(request):
    """Страница с картой"""
    return render(request, 'toponyms/map.html')


def api_toponyms(request):
    """API для карты - возвращает все топонимы с координатами"""
    toponyms = Toponym.objects.exclude(center_lat__isnull=True).exclude(center_lon__isnull=True)
    data = []
    for top in toponyms:
        # Получаем type_name из специализированной таблицы (если есть)
        type_name = ''
        if top.category.code == 'URB' and hasattr(top, 'urbanonym'):
            type_name = top.urbanonym.type_name
        elif top.category.code == 'HYD' and hasattr(top, 'hydronym'):
            type_name = top.hydronym.type_name
        elif top.category.code == 'CHR' and hasattr(top, 'choronym'):
            type_name = top.choronym.type_name
        elif top.category.code == 'AGR' and hasattr(top, 'agoronym'):
            type_name = top.agoronym.type_name
        elif top.category.code == 'LIM' and hasattr(top, 'limnonim'):
            type_name = top.limnonim.type_name
        elif top.category.code == 'CRE' and hasattr(top, 'crenonym'):
            type_name = top.crenonym.type_name
        elif top.category.code == 'MEM' and hasattr(top, 'memorionim'):
            type_name = top.memorionim.type_name
        elif top.category.code == 'NAT' and hasattr(top, 'natural_object'):
            type_name = top.natural_object.type_name

        data.append({
            'id': top.id,
            'name': top.name,
            'category': top.category.code,
            'category_name': top.category.name_ru,
            'type_name': type_name,
            'description': top.description,
            'center_lat': top.center_lat,
            'center_lon': top.center_lon,
        })
    return JsonResponse(data, safe=False)


def toponym_detail(request, toponym_id):
    """Детальная страница топонима"""
    toponym = get_object_or_404(Toponym, id=toponym_id)

    # Получаем type_name из специализированной таблицы
    type_name = ''
    extra_data = {}

    if toponym.category.code == 'URB' and hasattr(toponym, 'urbanonym'):
        type_name = toponym.urbanonym.type_name
        if toponym.urbanonym.length_km:
            extra_data['Длина'] = f"{toponym.urbanonym.length_km} км"
    elif toponym.category.code == 'HYD' and hasattr(toponym, 'hydronym'):
        type_name = toponym.hydronym.type_name
        if toponym.hydronym.length_km:
            extra_data['Длина'] = f"{toponym.hydronym.length_km} км"
    elif toponym.category.code == 'CHR' and hasattr(toponym, 'choronym'):
        type_name = toponym.choronym.type_name
        if toponym.choronym.population:
            extra_data['Население'] = f"{toponym.choronym.population} чел."
    elif toponym.category.code == 'AGR' and hasattr(toponym, 'agoronym'):
        type_name = toponym.agoronym.type_name
    elif toponym.category.code == 'LIM' and hasattr(toponym, 'limnonim'):
        type_name = toponym.limnonim.type_name
    elif toponym.category.code == 'CRE' and hasattr(toponym, 'crenonym'):
        type_name = toponym.crenonym.type_name
    elif toponym.category.code == 'MEM' and hasattr(toponym, 'memorionim'):
        type_name = toponym.memorionim.type_name
    elif toponym.category.code == 'NAT' and hasattr(toponym, 'natural_object'):
        type_name = toponym.natural_object.type_name

    context = {
        'toponym': toponym,
        'type_name': type_name,
        'extra_data': extra_data,
        'has_coords': toponym.center_lat and toponym.center_lon,
    }
    return render(request, 'toponyms/detail.html', context)


def toponym_list(request):
    """Список топонимов с поиском, фильтрацией и пагинацией"""
    toponyms = Toponym.objects.all()

    # Поиск по названию
    q = request.GET.get('q', '')
    if q:
        toponyms = toponyms.filter(name__icontains=q)

    # Фильтр по категории (по коду категории)
    cat = request.GET.get('category', '')
    if cat:
        toponyms = toponyms.filter(category__code=cat)

    # Сортировка
    sort = request.GET.get('sort', 'name')
    if sort == 'name':
        toponyms = toponyms.order_by('name')
    elif sort == '-name':
        toponyms = toponyms.order_by('-name')
    elif sort == 'category':
        toponyms = toponyms.order_by('category__name_ru')
    elif sort == '-category':
        toponyms = toponyms.order_by('-category__name_ru')
    elif sort == 'id':
        toponyms = toponyms.order_by('id')
    else:
        toponyms = toponyms.order_by('name')

    # Пагинация (25 объектов на страницу)
    paginator = Paginator(toponyms, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Категории для фильтра (из БД)
    categories = ToponymCategory.objects.all().order_by('name_ru')

    context = {
        'toponyms': page_obj,
        'page_obj': page_obj,
        'q': q,
        'selected_category': cat,
        'sort': sort,
        'categories': categories,
        'total': paginator.count,
    }
    return render(request, 'toponyms/list.html', context)


def api_toponyms(request):
    """API для карты - возвращает все топонимы с координатами и геометрией"""
    toponyms = Toponym.objects.exclude(center_lat__isnull=True).exclude(center_lon__isnull=True)
    data = []
    for top in toponyms:
        # Получаем type_name из специализированной таблицы
        type_name = ''
        if top.category.code == 'URB' and hasattr(top, 'urbanonym'):
            type_name = top.urbanonym.type_name
        elif top.category.code == 'HYD' and hasattr(top, 'hydronym'):
            type_name = top.hydronym.type_name
        # ... остальные категории

        item = {
            'id': top.id,
            'name': top.name,
            'category': top.category.code,
            'category_name': top.category.name_ru,
            'type_name': type_name,
            'description': top.description,
            'center_lat': top.center_lat,
            'center_lon': top.center_lon,
            'geometry_type': top.geometry_type,
            'geometry_coords': top.geometry_coords,
        }
        data.append(item)
    return JsonResponse(data, safe=False)

def stats_view(request):
    """Страница статистики"""
    total = Toponym.objects.count()
    with_coords = Toponym.objects.exclude(center_lat__isnull=True).exclude(center_lon__isnull=True).count()
    without_coords = total - with_coords

    # Статистика по категориям
    category_stats = Toponym.objects.values('category__name_ru', 'category__code').annotate(count=Count('id')).order_by(
        '-count')

    # Статистика по типам объектов (из специализированных таблиц)
    type_stats = []
    urban_count = Urbanonym.objects.count()
    if urban_count > 0:
        type_stats.append({'type_name': 'улица', 'count': urban_count})

    hydr_count = Hydronym.objects.count()
    if hydr_count > 0:
        type_stats.append({'type_name': 'река/ручей', 'count': hydr_count})

    chor_count = Choronym.objects.count()
    if chor_count > 0:
        type_stats.append({'type_name': 'район', 'count': chor_count})

    type_stats = sorted(type_stats, key=lambda x: -x['count'])[:10]

    # Топонимы с историческими названиями
    historical_count = Toponym.objects.exclude(historical_name='').count()

    context = {
        'total': total,
        'with_coords': with_coords,
        'without_coords': without_coords,
        'coords_percent': round(with_coords / total * 100, 1) if total > 0 else 0,
        'category_stats': category_stats,
        'type_stats': type_stats,
        'historical_count': historical_count,
    }
    return render(request, 'toponyms/stats.html', context)


def export_toponyms(request):
    """Экспорт топонимов в CSV или JSON"""
    format_type = request.GET.get('format', 'csv')
    q = request.GET.get('q', '')
    cat = request.GET.get('category', '')

    toponyms = Toponym.objects.all()
    if q:
        toponyms = toponyms.filter(name__icontains=q)
    if cat:
        toponyms = toponyms.filter(category__code=cat)

    if format_type == 'json':
        data = []
        for t in toponyms:
            data.append({
                'id': t.id,
                'name': t.name,
                'category': t.category.code,
                'category_name': t.category.name_ru,
                'description': t.description,
                'historical_name': t.historical_name,
                'latitude': t.center_lat,
                'longitude': t.center_lon
            })
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="toponyms.json"'
        return response

    else:  # csv
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="toponyms.csv"'
        writer = csv.writer(response)
        writer.writerow(
            ['ID', 'Название', 'Категория', 'Тип', 'Примечание', 'Историческое название', 'Широта', 'Долгота'])
        for t in toponyms:
            writer.writerow([
                t.id, t.name, t.category.name_ru,
                '',  # type_name пока оставляем пустым
                t.description, t.historical_name,
                t.center_lat, t.center_lon
            ])
        return response