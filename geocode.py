# geocode.py - обновлённая версия для новой структуры БД

import os
import sys
import django
import requests
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'izh_toponyms_project.settings')
django.setup()

from toponyms.models import Toponym, Urbanonym, Hydronym, Choronym


def get_type_name(toponym):
    """
    Получает type_name из специализированной таблицы в зависимости от категории
    """
    try:
        if toponym.category.code == 'URB' and hasattr(toponym, 'urbanonym'):
            return toponym.urbanonym.type_name
        elif toponym.category.code == 'HYD' and hasattr(toponym, 'hydronym'):
            return toponym.hydronym.type_name
        elif toponym.category.code == 'CHR' and hasattr(toponym, 'choronym'):
            return toponym.choronym.type_name
        elif toponym.category.code == 'AGR' and hasattr(toponym, 'agoronym'):
            return toponym.agoronym.type_name
        elif toponym.category.code == 'LIM' and hasattr(toponym, 'limnonim'):
            return toponym.limnonim.type_name
        elif toponym.category.code == 'CRE' and hasattr(toponym, 'crenonym'):
            return toponym.crenonym.type_name
        elif toponym.category.code == 'MEM' and hasattr(toponym, 'memorionim'):
            return toponym.memorionim.type_name
        elif toponym.category.code == 'NAT' and hasattr(toponym, 'natural_object'):
            return toponym.natural_object.type_name
    except:
        pass
    return ''


def geocode_osm(address):
    """Геокодинг через OpenStreetMap (бесплатно, без ключа)"""
    url = "https://nominatim.openstreetmap.org/search"

    # Улучшаем адрес для лучшего поиска
    full_address = f"{address}, Ижевск, Удмуртия, Россия"

    params = {
        'q': full_address,
        'format': 'json',
        'limit': 1,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
        return None, None
    except Exception as e:
        return None, None


def update_coordinates():
    """Обновляет координаты для всех топонимов"""
    toponyms = Toponym.objects.all()
    total = toponyms.count()
    print(f"\n📊 Найдено топонимов: {total}")
    print("=" * 50)

    updated = 0
    not_found = 0
    skipped = 0

    for i, top in enumerate(toponyms, 1):
        # Пропускаем, если координаты уже есть
        if top.center_lat and top.center_lon:
            skipped += 1
            print(f"[{i}/{total}] ⏭️ {top.name} - уже есть координаты")
            continue

        # Формируем поисковый запрос
        search = top.name
        type_name = get_type_name(top)
        if type_name and type_name != 'nan':
            search += f" {type_name}"

        print(f"[{i}/{total}] 🔍 {search[:50]}...", end=" ")

        lat, lon = geocode_osm(search)

        if lat and lon:
            top.center_lat = lat
            top.center_lon = lon
            top.geometry_coords = {
                'type': 'Point',
                'coordinates': [lon, lat]
            }
            top.save()
            updated += 1
            print(f"✅ ({lat:.4f}, {lon:.4f})")
        else:
            not_found += 1
            print(f"❌")

        # Пауза для соблюдения лимитов
        time.sleep(1)

    print("\n" + "=" * 50)
    print(f"📊 Результаты:")
    print(f"   ✅ Найдено: {updated}")
    print(f"   ❌ Не найдено: {not_found}")
    print(f"   ⏭️ Уже были: {skipped}")
    print(f"   📋 Всего: {total}")
    print("=" * 50)


if __name__ == '__main__':
    print("\n🗺️ ГЕОКОДИРОВАНИЕ ЧЕРЕЗ OPENSTREETMAP")
    print("(бесплатно, без ключа)")
    update_coordinates()
    print("\n✨ Готово!")