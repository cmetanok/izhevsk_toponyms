from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .models import (
    Country, City, ToponymCategory, Toponym,
    Urbanonym, Agoronym, Choronym, Hydronym,
    Limnonim, Crenonym, Memorionim, NaturalObject
)


# ============================================================
# АДМИНКА ДЛЯ ТОПОНИМОВ (с Bulk-действиями)
# ============================================================

@admin.register(Toponym)
class ToponymAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'city', 'has_coords', 'has_polygon')
    list_filter = ('category', 'city', 'geometry_type')
    search_fields = ('name', 'id', 'description', 'historical_name')
    list_editable = ('category',)
    list_per_page = 50

    actions = ['bulk_change_category', 'bulk_clear_coords', 'bulk_add_to_city']

    fieldsets = (
        ('Идентификация', {'fields': ('id', 'name', 'category', 'city')}),
        ('Геометрия', {'fields': ('geometry_type', 'geometry_coords', 'center_lat', 'center_lon')}),
        ('Описание', {'fields': ('description', 'historical_name', 'extra_info')}),
    )

    def has_coords(self, obj):
        return obj.center_lat is not None

    has_coords.boolean = True
    has_coords.short_description = 'Координаты'

    def has_polygon(self, obj):
        return obj.geometry_type == 'Polygon'

    has_polygon.boolean = True
    has_polygon.short_description = 'Полигон'

    # BULK ACTIONS
    def bulk_change_category(self, request, queryset):
        if 'apply_category' in request.POST:
            new_category = request.POST.get('new_category')
            if new_category:
                updated = queryset.update(category_id=new_category)
                self.message_user(request, f'Обновлено {updated} топонимов', messages.SUCCESS)
                return HttpResponseRedirect(request.get_full_path())

        categories = ToponymCategory.objects.all()
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


# ============================================================
# АДМИНКА ДЛЯ ОСТАЛЬНЫХ МОДЕЛЕЙ
# ============================================================

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_ru', 'name_en')
    search_fields = ('name_ru', 'name_en')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country', 'center_lat', 'center_lon')
    search_fields = ('name',)
    list_filter = ('country',)


@admin.register(ToponymCategory)
class ToponymCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_ru', 'icon')
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
    list_display = ('toponym', 'type_name', 'historical_event')
    search_fields = ('toponym__name',)


@admin.register(NaturalObject)
class NaturalObjectAdmin(admin.ModelAdmin):
    list_display = ('toponym', 'type_name', 'area_km2')
    search_fields = ('toponym__name',)