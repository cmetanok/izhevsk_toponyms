import csv
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Q
from .models import Toponym, Category, Urbanonym, Hydronym, Choronym


def map_view(request):
    return render(request, 'toponyms/map.html')


def api_toponyms(request):
    toponyms = Toponym.objects.exclude(center_lat__isnull=True).exclude(center_lon__isnull=True)
    data = []
    for top in toponyms:
        data.append({
            'id': top.id,
            'name': top.name,
            'category': top.category.code if top.category else '',
            'category_name': top.category.name_ru if top.category else '',
            'description': top.description,
            'center_lat': top.center_lat,
            'center_lon': top.center_lon,
            'unofficial_names': top.unofficial_names or [],
            'has_official_name': top.has_official_name,
        })
    return JsonResponse(data, safe=False)


def toponym_detail(request, toponym_id):
    toponym = get_object_or_404(Toponym, id=toponym_id)
    context = {
        'toponym': toponym,
        'has_coords': toponym.center_lat and toponym.center_lon,
        'unofficial_names': ', '.join(toponym.unofficial_names) if toponym.unofficial_names else '',
    }
    return render(request, 'toponyms/detail.html', context)


def toponym_list(request):
    toponyms = Toponym.objects.all()

    # Поиск по официальному И неофициальному названию
    q = request.GET.get('q', '')
    if q:
        toponyms = toponyms.filter(
            Q(name__icontains=q) | Q(unofficial_names__icontains=q)
        )

    cat = request.GET.get('category', '')
    if cat:
        toponyms = toponyms.filter(category__code=cat)

    paginator = Paginator(toponyms, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all().order_by('name_ru')

    context = {
        'toponyms': page_obj,
        'page_obj': page_obj,
        'q': q,
        'selected_category': cat,
        'categories': categories,
        'total': paginator.count,
    }
    return render(request, 'toponyms/list.html', context)


def stats_view(request):
    total = Toponym.objects.count()
    with_coords = Toponym.objects.exclude(center_lat__isnull=True).exclude(center_lon__isnull=True).count()

    category_stats = Toponym.objects.values('category__name_ru').annotate(count=Count('id')).order_by('-count')

    context = {
        'total': total,
        'with_coords': with_coords,
        'without_coords': total - with_coords,
        'coords_percent': round(with_coords / total * 100, 1) if total > 0 else 0,
        'category_stats': category_stats,
        'historical_count': Toponym.objects.exclude(historical_name='').count(),
        'type_stats': [],
    }
    return render(request, 'toponyms/stats.html', context)


def export_toponyms(request):
    format_type = request.GET.get('format', 'csv')
    q = request.GET.get('q', '')
    cat = request.GET.get('category', '')

    toponyms = Toponym.objects.all()
    if q:
        toponyms = toponyms.filter(
            Q(name__icontains=q) | Q(unofficial_names__icontains=q)
        )
    if cat:
        toponyms = toponyms.filter(category__code=cat)

    if format_type == 'json':
        data = []
        for t in toponyms:
            data.append({
                'id': t.id,
                'name': t.name,
                'category': t.category.code if t.category else '',
                'category_name': t.category.name_ru if t.category else '',
                'description': t.description,
                'historical_name': t.historical_name,
                'renamed_year': t.renamed_year,
                'has_official_name': t.has_official_name,
                'unofficial_names': t.unofficial_names,
                'latitude': t.center_lat,
                'longitude': t.center_lon
            })
        response = HttpResponse(json.dumps(data, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder),
                                content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="toponyms.json"'
        return response
    else:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="toponyms.csv"'
        writer = csv.writer(response)
        writer.writerow(
            ['ID', 'Название', 'Категория', 'Неофициальные названия', 'Историческое название', 'Год переименования',
             'Примечание', 'Широта', 'Долгота'])
        for t in toponyms:
            writer.writerow([
                t.id,
                t.name,
                t.category.name_ru if t.category else '',
                ', '.join(t.unofficial_names) if t.unofficial_names else '',
                t.historical_name,
                t.renamed_year,
                t.description,
                t.center_lat,
                t.center_lon
            ])
        return response