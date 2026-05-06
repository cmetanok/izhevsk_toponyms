import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'izh_toponyms_project.settings')
django.setup()

from toponyms.models import Country, City, ToponymCategory

# ============================================================
# 1. Добавляем страны
# ============================================================
print("🌍 Добавление стран...")

countries = [
    ('RU', 'Россия', 'Russia'),
    ('BY', 'Беларусь', 'Belarus'),
    ('KZ', 'Казахстан', 'Kazakhstan'),
]

for code, name_ru, name_en in countries:
    obj, created = Country.objects.update_or_create(
        code=code,
        defaults={'name_ru': name_ru, 'name_en': name_en}
    )
    print(f"  {'✅ Создана' if created else '🔄 Уже есть'} {name_ru} ({code})")

# ============================================================
# 2. Добавляем города
# ============================================================
print("\n🏙️ Добавление городов...")

cities = [
    ('IZH', 'Ижевск', 'RU', 56.85, 53.20, 'Столица Удмуртской Республики'),
]

for city_id, name, country_code, lat, lon, desc in cities:
    country = Country.objects.get(code=country_code)
    obj, created = City.objects.update_or_create(
        id=city_id,
        defaults={
            'name': name,
            'country': country,
            'center_lat': lat,
            'center_lon': lon,
            'description': desc
        }
    )
    print(f"  {'✅ Создан' if created else '🔄 Уже есть'} {name}")

# ============================================================
# 3. Добавляем категории топонимов
# ============================================================
print("\n📁 Добавление категорий топонимов...")

categories = [
    ('URB', 'URBAN', 'Урбанонимы', 'Urbanonyms', 'Улицы, площади, шоссе, переулки', '🏙️'),
    ('AGR', 'AGORA', 'Агоронимы', 'Agoronyms', 'Площади, рынки, базары', '🏛️'),
    ('CHR', 'CHORO', 'Хоронимы', 'Choronyms', 'Районы, микрорайоны, жилые массивы', '🏘️'),
    ('HYD', 'HYDRO', 'Гидронимы', 'Hydronyms', 'Реки, ручьи', '💧'),
    ('LIM', 'LIMNO', 'Лимнонимы', 'Limnonyms', 'Пруды, озёра', '🌊'),
    ('CRE', 'CRENO', 'Кренонимы', 'Crenonyms', 'Родники, ключи, источники', '💦'),
    ('MEM', 'MEMOR', 'Меморионимы', 'Memorionims', 'Памятные места, мысы, поляны', '📜'),
    ('NAT', 'NATURE', 'Природные объекты', 'Natural objects', 'Парки, леса, овраги', '🌳'),
]

for code, cat_type, name_ru, name_en, desc, icon in categories:
    obj, created = ToponymCategory.objects.update_or_create(
        code=code,
        defaults={
            'type': cat_type,
            'name_ru': name_ru,
            'name_en': name_en,
            'description': desc,
            'icon': icon
        }
    )
    print(f"  {'✅ Создана' if created else '🔄 Уже есть'} {name_ru} ({code})")

# ============================================================
# 4. Проверка результата
# ============================================================
print("\n" + "="*50)
print("📊 ИТОГИ ИНИЦИАЛИЗАЦИИ:")
print(f"   Стран: {Country.objects.count()}")
print(f"   Городов: {City.objects.count()}")
print(f"   Категорий: {ToponymCategory.objects.count()}")
print("="*50)
print("\n✅ Инициализация завершена!")