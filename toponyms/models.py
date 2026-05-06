from django.db import models


# ============================================================
# 1. ГЕОГРАФИЧЕСКАЯ ИЕРАРХИЯ
# ============================================================

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


# ============================================================
# 2. КАТЕГОРИИ ТОПОНИМОВ (НОРМАЛИЗАЦИЯ)
# ============================================================

class ToponymCategory(models.Model):
    """Категория топонима (урбанонимы, гидронимы, хоронимы и т.д.)"""
    CATEGORY_TYPES = [
        ('URBAN', 'Урбанонимы'),
        ('AGORA', 'Агоронимы'),
        ('CHORO', 'Хоронимы'),
        ('HYDRO', 'Гидронимы'),
        ('LIMNO', 'Лимнонимы'),
        ('CRENO', 'Кренонимы'),
        ('MEMOR', 'Меморионимы'),
        ('NATURE', 'Природные объекты'),
    ]

    code = models.CharField(max_length=10, primary_key=True, verbose_name='Код категории')
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES, verbose_name='Тип категории')
    name_ru = models.CharField(max_length=100, verbose_name='Название (рус.)')
    name_en = models.CharField(max_length=100, blank=True, verbose_name='Название (англ.)')
    description = models.TextField(blank=True, verbose_name='Описание')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка')

    class Meta:
        verbose_name = 'Категория топонима'
        verbose_name_plural = 'Категории топонимов'

    def __str__(self):
        return self.name_ru


# ============================================================
# 3. ОСНОВНАЯ ТАБЛИЦА ТОПОНИМОВ (ПОЛИМОРФНАЯ)
# ============================================================

class Toponym(models.Model):
    """Основная таблица топонимов (общие поля для всех типов)"""

    GEOMETRY_TYPES = [
        ('Point', 'Точка'),
        ('LineString', 'Линия'),
        ('Polygon', 'Полигон'),
    ]

    # Идентификация
    id = models.CharField(max_length=20, primary_key=True, verbose_name='ID топонима')
    name = models.CharField(max_length=200, verbose_name='Название')

    # Географическая привязка
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='toponyms', verbose_name='Город')

    # Категоризация
    category = models.ForeignKey(ToponymCategory, on_delete=models.PROTECT, related_name='toponyms',
                                 verbose_name='Категория')

    # Геометрия
    geometry_type = models.CharField(max_length=20, choices=GEOMETRY_TYPES, default='Point',
                                     verbose_name='Тип геометрии')
    geometry_coords = models.JSONField(default=dict, verbose_name='GeoJSON координаты')
    center_lat = models.FloatField(null=True, blank=True, verbose_name='Широта центра')
    center_lon = models.FloatField(null=True, blank=True, verbose_name='Долгота центра')

    # Дополнительная информация
    description = models.TextField(blank=True, verbose_name='Описание')
    historical_name = models.CharField(max_length=200, blank=True, verbose_name='Историческое название')
    extra_info = models.JSONField(default=dict, blank=True, verbose_name='Дополнительные данные')

    class Meta:
        verbose_name = 'Топоним'
        verbose_name_plural = 'Топонимы'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name_ru}) - {self.city.name}"


# ============================================================
# 4. СПЕЦИАЛИЗИРОВАННЫЕ ТАБЛИЦЫ (ДЛЯ КАЖДОГО ТИПА ТОПОНИМОВ)
# ============================================================

class Urbanonym(models.Model):
    """Урбаноним (улица, площадь, шоссе, переулок и т.д.)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='urbanonym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (улица, площадь, шоссе...)')
    length_km = models.FloatField(null=True, blank=True, verbose_name='Длина (км)')

    class Meta:
        verbose_name = 'Урбаноним'
        verbose_name_plural = 'Урбанонимы'

    def __str__(self):
        return f"{self.type_name} {self.toponym.name}"


class Agoronym(models.Model):
    """Агороним (площадь, рынок, базар)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='agoronym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (площадь, рынок...)')
    square_m2 = models.FloatField(null=True, blank=True, verbose_name='Площадь (м²)')

    class Meta:
        verbose_name = 'Агороним'
        verbose_name_plural = 'Агоронимы'


class Choronym(models.Model):
    """Хороним (район, микрорайон, жилой массив)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='choronym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (район, микрорайон...)')
    population = models.IntegerField(null=True, blank=True, verbose_name='Население')

    class Meta:
        verbose_name = 'Хороним'
        verbose_name_plural = 'Хоронимы'


class Hydronym(models.Model):
    """Гидроним (река, ручей)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='hydronym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (река, ручей...)')
    length_km = models.FloatField(null=True, blank=True, verbose_name='Длина (км)')

    class Meta:
        verbose_name = 'Гидроним'
        verbose_name_plural = 'Гидронимы'


class Limnonim(models.Model):
    """Лимноним (пруд, озеро)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='limnonim')
    type_name = models.CharField(max_length=50, verbose_name='Тип (пруд, озеро...)')
    area_km2 = models.FloatField(null=True, blank=True, verbose_name='Площадь (км²)')

    class Meta:
        verbose_name = 'Лимноним'
        verbose_name_plural = 'Лимнонимы'


class Crenonym(models.Model):
    """Креноним (родник, ключ, источник)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='crenonym')
    type_name = models.CharField(max_length=50, verbose_name='Тип (родник, ключ...)')
    flow_rate = models.FloatField(null=True, blank=True, verbose_name='Дебит (л/с)')

    class Meta:
        verbose_name = 'Креноним'
        verbose_name_plural = 'Кренонимы'


class Memorionim(models.Model):
    """Меморионим (памятные места, части пруда, мысы)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='memorionim')
    type_name = models.CharField(max_length=50, verbose_name='Тип (мыс, поляна, часть...)')
    historical_event = models.TextField(blank=True, verbose_name='Историческое событие')

    class Meta:
        verbose_name = 'Меморионим'
        verbose_name_plural = 'Меморионимы'


class NaturalObject(models.Model):
    """Природный объект (парк, лес, овраг)"""
    toponym = models.OneToOneField(Toponym, on_delete=models.CASCADE, primary_key=True, related_name='natural_object')
    type_name = models.CharField(max_length=50, verbose_name='Тип (парк, лес, овраг...)')
    area_km2 = models.FloatField(null=True, blank=True, verbose_name='Площадь (км²)')

    class Meta:
        verbose_name = 'Природный объект'
        verbose_name_plural = 'Природные объекты'