from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Count
from django.urls import path
from .models import (
    Country, City, Category, Toponym,
    Urbanonym, Agoronym, Choronym, Hydronym,
    Limnonim, Crenonym, Memorionim, NaturalObject
)


@admin.register(Toponym)
class ToponymAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'city', 'has_official_name', 'renamed_year', 'has_coords', 'has_polygon')
    list_filter = ('category', 'city', 'geometry_type', 'has_official_name')
    search_fields = ('name', 'id', 'description', 'historical_name', 'unofficial_names')
    list_editable = ('category', 'has_official_name')
    list_per_page = 50

    actions = ['bulk_change_category', 'bulk_clear_coords', 'bulk_add_to_city']

    fieldsets = (
        ('Идентификация', {'fields': ('id', 'name', 'category', 'city')}),
        ('Названия', {'fields': ('has_official_name', 'unofficial_names', 'historical_name', 'renamed_year')}),
        ('Геометрия', {'fields': ('geometry_type', 'geometry_coords', 'center_lat', 'center_lon')}),
        ('Описание', {'fields': ('description', 'extra_info')}),
    )

    def has_coords(self, obj):
        return obj.center_lat is not None

    has_coords.boolean = True
    has_coords.short_description = 'Координаты'

    def has_polygon(self, obj):
        return obj.geometry_type == 'Polygon'

    has_polygon.boolean = True
    has_polygon.short_description = 'Полигон'

    def get_search_results(self, request, queryset, search_term):
        """Расширенный поиск по официальным и неофициальным названиям"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:
            queryset |= self.model.objects.filter(unofficial_names__icontains=search_term)
        return queryset, use_distinct

    def bulk_change_category(self, request, queryset):
        if 'apply_category' in request.POST:
            new_category = request.POST.get('new_category')
            if new_category:
                updated = queryset.update(category_id=new_category)
                self.message_user(request, f'Обновлено {updated} топонимов', messages.SUCCESS)
                return HttpResponseRedirect(request.get_full_path())

        categories = Category.objects.all()
        context = {
            'title': 'Сменить категорию',
            'queryset': queryset,
            'categories': categories,
            'action': 'bulk_change_category',
        }
        return render(request, 'admin/bulk_change_form.html', context)

    bulk_change_category.short_description = "✏️ Сменить категорию у выбранных"

    def bulk_clear_coords(self, request, queryset):
        count = queryset.update(center_lat=None, center_lon=None, geometry_coords={}, geometry_type='Point')
        self.message_user(request, f'Очищены координаты у {count} топонимов', messages.WARNING)

    bulk_clear_coords.short_description = "🗑️ Очистить координаты у выбранных"

    def bulk_add_to_city(self, request, queryset):
        if 'apply_city' in request.POST:
            city_id = request.POST.get('city_id')
            if city_id:
                updated = queryset.update(city_id=city_id)
                self.message_user(request, f'Привязано {updated} топонимов к городу', messages.SUCCESS)
                return HttpResponseRedirect(request.get_full_path())

        cities = City.objects.all()
        context = {
            'title': 'Привязать к городу',
            'queryset': queryset,
            'cities': cities,
            'action': 'bulk_add_to_city',
        }
        return render(request, 'admin/bulk_change_form.html', context)

    bulk_add_to_city.short_description = "🏙️ Привязать к городу выбранные"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('stats-report/', self.admin_site.admin_view(self.stats_report_view), name='toponyms_stats_report'),
        ]
        return custom_urls + urls

    def stats_report_view(self, request):
        stats = []
        categories = Category.objects.all()

        for cat in categories:
            total = Toponym.objects.filter(category=cat).count()
            with_coords = Toponym.objects.filter(category=cat, center_lat__isnull=False).count()
            percent = round(with_coords / total * 100, 1) if total > 0 else 0
            row_class = 'low-percent' if percent < 30 else ''
            stats.append({
                'category_name': f"{cat.icon} {cat.name_ru}",
                'total': total,
                'with_coords': with_coords,
                'percent': percent,
                'row_class': row_class,
            })

        context = {
            'stats': stats,
            'title': 'Статистика геокодирования по категориям',
        }
        return render(request, 'admin/toponyms_stats_report.html', context)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_ru', 'name_en')
    search_fields = ('name_ru', 'name_en')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country', 'center_lat', 'center_lon')
    search_fields = ('name',)
    list_filter = ('country',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_ru', 'icon', 'order')
    search_fields = ('name_ru', 'code')


@admin.register(Urbanonym)
class UrbanonymAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'length_km')
    search_fields = ('toponym__name',)


@admin.register(Agoronym)
class AgoronymAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'square_m2')
    search_fields = ('toponym__name',)


@admin.register(Choronym)
class ChoronymAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'population')
    search_fields = ('toponym__name',)


@admin.register(Hydronym)
class HydronymAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'length_km')
    search_fields = ('toponym__name',)


@admin.register(Limnonim)
class LimnonimAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'area_km2')
    search_fields = ('toponym__name',)


@admin.register(Crenonym)
class CrenonymAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'flow_rate')
    search_fields = ('toponym__name',)


@admin.register(Memorionim)
class MemorionimAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'year_opened', 'architect')
    search_fields = ('toponym__name', 'architect')


@admin.register(NaturalObject)
class NaturalObjectAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'area_km2')
    search_fields = ('toponym__name',)