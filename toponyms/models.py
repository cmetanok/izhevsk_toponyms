from django.db import models


class Category(models.Model):
    """Модель категорий топонимов (нормализация)"""
    code = models.CharField(max_length=10, primary_key=True, verbose_name='Код')
    name_ru = models.CharField(max_length=50, verbose_name='Название (рус.)')
    name_en = models.CharField(max_length=50, blank=True, verbose_name='Название (англ.)')
    description = models.TextField(blank=True, verbose_name='Описание')
    icon = models.CharField(max_length=50, blank=True, help_text='Emoji или CSS класс', verbose_name='Иконка')
    order = models.IntegerField(default=0, verbose_name='Порядок сортировки')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name_ru']

    def __str__(self):
        return f"{self.name_ru} ({self.code})"


class Country(models.Model):
    """Страна"""
    code = models.CharField(max_length=2, primary_key=True, verbose_name='Код страны (ISO)')
    name_ru = models.CharField(max_length=100, verbose_name='Название (рус.)')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='Название (англ.)')

    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'
        ordering = ['name_ru']

    def __str__(self):
        return self.name_ru


class City(models.Model):
    """Город"""
    id = models.CharField(max_length=10, primary_key=True, verbose_name='ID города')
    name = models.CharField(max_length=100, verbose_name='Название города')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='cities', verbose_name='Страна')
    center_lat = models.FloatField(null=True, blank=True, verbose_name='Широта центра')
    center_lon = models.FloatField(null=True, blank=True, verbose_name='Долгота центра')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.country.name_ru})"


class Toponym(models.Model):
    """Модель топонима (расширенная)"""

    GEOMETRY_TYPES = [
        ('Point', 'Точка'),
        ('LineString', 'Линия'),
        ('Polygon', 'Полигон'),
    ]

    # Основные поля
    id = models.CharField(max_length=20, primary_key=True, verbose_name='ID топонима')
    name = models.CharField(max_length=200, verbose_name='Название')

    # Географическая привязка
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='toponyms', verbose_name='Город')

    # Категоризация
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='toponyms', verbose_name='Категория')

    # Геометрия
    geometry_type = models.CharField(max_length=20, choices=GEOMETRY_TYPES, default='Point',
                                     verbose_name='Тип геометрии')
    geometry_coords = models.JSONField(default=dict, verbose_name='GeoJSON координаты')
    center_lat = models.FloatField(null=True, blank=True, verbose_name='Широта центра')
    center_lon = models.FloatField(null=True, blank=True, verbose_name='Долгота центра')

    # Дополнительная информация
    description = models.TextField(blank=True, verbose_name='Описание')
    historical_name = models.CharField(max_length=200, blank=True, verbose_name='Историческое название')
    renamed_year = models.IntegerField(null=True, blank=True, verbose_name='Год переименования')

    # НОВЫЕ ПОЛЯ ДЛЯ НЕОФИЦИАЛЬНЫХ НАЗВАНИЙ
    has_official_name = models.BooleanField(default=True, verbose_name='Имеет официальное название')
    unofficial_names = models.JSONField(default=list, blank=True, verbose_name='Неофициальные названия (список)')

    extra_info = models.JSONField(default=dict, blank=True, verbose_name='Дополнительные данные')

    class Meta:
        verbose_name = 'Топоним'
        verbose_name_plural = 'Топонимы'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['center_lat', 'center_lon']),
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name_ru}) - {self.city.name}"

    def get_all_search_names(self):
        """Возвращает список всех названий для поиска (официальное + неофициальные)"""
        names = [self.name]
        if self.unofficial_names:
            names.extend(self.unofficial_names)
        return names


# Специализированные таблицы (оставляем как есть)
class Urbanonym(models.Model):
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='urbanonym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (улица, площадь, шоссе...)')
    length_km = models.FloatField(null=True, blank=True, verbose_name='Длина (км)')

    class Meta:
        verbose_name = 'Урбаноним'
        verbose_name_plural = 'Урбанонимы'

    def __str__(self):
        return f"{self.type_name} {self.toponym.name}"


class Agoronym(models.Model):
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='agoronym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (площадь, рынок...)')
    square_m2 = models.FloatField(null=True, blank=True, verbose_name='Площадь (м²)')

    class Meta:
        verbose_name = 'Агороним'
        verbose_name_plural = 'Агоронимы'


class Choronym(models.Model):
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='choronym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (район, микрорайон...)')
    population = models.IntegerField(null=True, blank=True, verbose_name='Население')

    class Meta:
        verbose_name = 'Хороним'
        verbose_name_plural = 'Хоронимы'


class Hydronym(models.Model):
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='hydronym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (река, ручей...)')
    length_km = models.FloatField(null=True, blank=True, verbose_name='Длина (км)')

    class Meta:
        verbose_name = 'Гидроним'
        verbose_name_plural = 'Гидронимы'


class Limnonim(models.Model):
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='limnonim')
    type_name = models.CharField(max_length=50, verbose_name='Тип (пруд, озеро...)')
    area_km2 = models.FloatField(null=True, blank=True, verbose_name='Площадь (км²)')

    class Meta:
        verbose_name = 'Лимноним'
        verbose_name_plural = 'Лимнонимы'


class Crenonym(models.Model):
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='crenonym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (родник, ключ...)')
    flow_rate = models.FloatField(null=True, blank=True, verbose_name='Дебит (л/с)')

    class Meta:
        verbose_name = 'Креноним'
        verbose_name_plural = 'Кренонимы'


class Memorionim(models.Model):
    """Меморионим (памятники, памятные места, мемориалы)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='memorionim')
    type_name = models.CharField(max_length=50, verbose_name='Тип (памятник, мемориал, братская могила...)')
    historical_event = models.TextField(blank=True, verbose_name='Историческое событие')
    year_opened = models.IntegerField(null=True, blank=True, verbose_name='Год открытия')
    architect = models.CharField(max_length=200, blank=True, verbose_name='Автор/архитектор')

    class Meta:
        verbose_name = 'Меморионим'
        verbose_name_plural = 'Меморионимы'


class NaturalObject(models.Model):
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='natural_object')
    type_name = models.CharField(max_length=50, verbose_name='Тип (парк, лес, овраг...)')
    area_km2 = models.FloatField(null=True, blank=True, verbose_name='Площадь (км²)')

    class Meta:
        verbose_name = 'Природный объект'
        verbose_name_plural = 'Природные объекты'