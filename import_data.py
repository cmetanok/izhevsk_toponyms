import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'izh_toponyms_project.settings')
django.setup()

import pandas as pd
from toponyms.models import (
    Country, City, ToponymCategory, Toponym,
    Urbanonym, Agoronym, Choronym, Hydronym,
    Limnonim, Crenonym, Memorionim, NaturalObject
)


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_city():
    """Получает город Ижевск (по умолчанию)"""
    return City.objects.get(id='IZH')


def get_category_by_old_code(old_code: str):
    """
    Преобразует старый код категории (U, A, H, G, L, K, M, N)
    в новый код (URB, AGR, CHR, HYD, LIM, CRE, MEM, NAT)
    """
    mapping = {
        'U': 'URB',  # Урбанонимы
        'A': 'AGR',  # Агоронимы
        'H': 'CHR',  # Хоронимы
        'G': 'HYD',  # Гидронимы
        'L': 'LIM',  # Лимнонимы
        'K': 'CRE',  # Кренонимы
        'M': 'MEM',  # Меморионимы
        'N': 'NAT',  # Природные объекты
    }
    new_code = mapping.get(old_code, 'URB')
    try:
        return ToponymCategory.objects.get(code=new_code)
    except ToponymCategory.DoesNotExist:
        print(f"  ⚠️ Категория {new_code} не найдена, использую URB")
        return ToponymCategory.objects.get(code='URB')


def extract_historical_name(description: str) -> str:
    """Извлекает историческое название из примечания"""
    if pd.isna(description) or description == 'nan':
        return ''
    desc_str = str(description)
    if 'историческое название' in desc_str.lower():
        parts = desc_str.split('историческое название')
        if len(parts) > 1:
            hist_part = parts[1].split(',')[0].strip()
            return hist_part
    return ''


def determine_old_category(top_id: str) -> str:
    """Определяет старый код категории по ID топонима (U-001 -> U)"""
    return top_id.split('-')[0]


# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ ИМПОРТА
# ============================================================

def import_toponyms():
    print("=" * 60)
    print("📖 ИМПОРТ ТОПОНИМОВ ИЖЕВСКА")
    print("=" * 60)

    # Проверка наличия файла
    if not os.path.exists('топонимы.xlsx'):
        print("❌ Файл 'топонимы.xlsx' не найден!")
        print(f"Текущая папка: {os.getcwd()}")
        return

    # Чтение Excel
    print("📖 Читаем Excel файл...")
    try:
        df = pd.read_excel('топонимы.xlsx', sheet_name='Лист1')
        print(f"✅ Загружено {len(df)} строк")
    except Exception as e:
        print(f"❌ Ошибка чтения: {e}")
        return

    # Получаем город Ижевск
    try:
        city = get_city()
        print(f"🏙️ Город: {city.name}")
    except City.DoesNotExist:
        print("❌ Город Ижевск не найден! Сначала запусти init_data.py")
        return

    # Счетчики
    total = 0
    errors = 0

    # Импорт
    print("\n💾 Импортируем топонимы...")
    print("-" * 60)

    for index, row in df.iterrows():
        top_id = str(row['ID']).strip()
        if pd.isna(top_id) or top_id == 'nan':
            continue

        try:
            # Основные данные
            name = str(row['Название']).strip()
            type_name = str(row['Тип']) if pd.notna(row['Тип']) else ''
            description = str(row['Примечание']) if pd.notna(row['Примечание']) else ''
            historical_name = extract_historical_name(description)

            # Определяем категорию (старый код -> новый)
            old_category = determine_old_category(top_id)
            category = get_category_by_old_code(old_category)

            # Создаём или обновляем топоним
            toponym, created = Toponym.objects.update_or_create(
                id=top_id,
                defaults={
                    'name': name,
                    'city': city,
                    'category': category,
                    'description': description,
                    'historical_name': historical_name,
                    'geometry_type': 'Point',
                    'geometry_coords': {'type': 'Point', 'coordinates': [0, 0]},
                }
            )

            # Создаём запись в специализированной таблице (если есть тип)
            if type_name:
                create_specialized_record(toponym, category, type_name, description)

            total += 1
            if total % 20 == 0:
                print(f"  Импортировано {total}...")

        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"  ❌ Ошибка в строке {index} (ID {top_id}): {e}")

    # Итоги
    print("-" * 60)
    print(f"\n📊 ИТОГИ ИМПОРТА:")
    print(f"   ✅ Импортировано: {total} топонимов")
    print(f"   ❌ Ошибок: {errors}")
    print(f"   📋 Всего в БД: {Toponym.objects.count()} топонимов")
    print("=" * 60)


def create_specialized_record(toponym, category, type_name, description):
    """Создаёт запись в специализированной таблице в зависимости от категории"""

    # Определяем тип по категории
    if category.code == 'URB':
        # Урбаноним (улица, шоссе, площадь)
        if 'шоссе' in type_name or 'тракт' in type_name:
            pass  # можно добавить специальную обработку
        Urbanonym.objects.update_or_create(
            toponym=toponym,
            defaults={'type_name': type_name}
        )

    elif category.code == 'AGR':
        # Агороним (площадь)
        Agoronym.objects.update_or_create(
            toponym=toponym,
            defaults={'type_name': type_name}
        )

    elif category.code == 'CHR':
        # Хороним (район)
        Choronym.objects.update_or_create(
            toponym=toponym,
            defaults={'type_name': type_name}
        )

    elif category.code == 'HYD':
        # Гидроним (река, ручей)
        Hydronym.objects.update_or_create(
            toponym=toponym,
            defaults={'type_name': type_name}
        )

    elif category.code == 'LIM':
        # Лимноним (пруд, озеро)
        Limnonim.objects.update_or_create(
            toponym=toponym,
            defaults={'type_name': type_name}
        )

    elif category.code == 'CRE':
        # Креноним (родник)
        Crenonym.objects.update_or_create(
            toponym=toponym,
            defaults={'type_name': type_name}
        )

    elif category.code == 'MEM':
        # Меморионим (памятное место)
        Memorionim.objects.update_or_create(
            toponym=toponym,
            defaults={'type_name': type_name, 'historical_event': description[:200]}
        )

    elif category.code == 'NAT':
        # Природный объект (парк, лес)
        NaturalObject.objects.update_or_create(
            toponym=toponym,
            defaults={'type_name': type_name}
        )


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == '__main__':
    import_toponyms()