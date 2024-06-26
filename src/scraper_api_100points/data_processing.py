import pandas as pd
import os
import csv


def save_to_csv(data, csv_filename):
    os.makedirs('data/output', exist_ok=True)
    csv_path = f'data/output/{csv_filename}'
    with open(csv_path, 'w', newline='') as csv_file:
        fieldnames = data[0].keys()
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames,  delimiter=';')

        csv_writer.writeheader()
        csv_writer.writerows(data)


def process_data(raw_data):
    # Создание DataFrame из исходных данных
    df = pd.DataFrame(raw_data)

    # Группировка данных по 'email', 'lesson', 'level' и агрегация оценок
    df_grouped = df.groupby(['user_email', 'lesson', 'level']).agg({'test_score': 'max'}).reset_index()
    # Заполнение пропущенных уровней
    all_levels = ['легкий', 'средний', 'сложный']  # Уровни сложности
    df_filled = df_grouped.pivot_table(index=['user_email', 'lesson'], columns='level', values='test_score', fill_value='0').reset_index()

    # Преобразование DataFrame обратно в список словарей
    result_data = df_filled.to_dict('records')

    return result_data

def process_and_save_data(raw_data, csv_filename):
    try:
        df = pd.DataFrame(raw_data)

        df['vk_id'] = df['vk_id'].astype(int)
        df['test_score'] = df['test_score'].astype(int)
        custom_order = ['Базовый', 'Средний', 'Сложный']
        # Задаем категориальный тип данных с указанным порядком
        level_dtype = pd.CategoricalDtype(categories=custom_order, ordered=True)
        # Применяем категориальный тип данных к столбцу 'level'
        df['level'] = df['level'].astype(level_dtype)

        table = pd.pivot_table(df, values=['test_score', 'href'],
                               index=['user_email', 'user_name', 'vk_id', 'course', 'module', 'lesson'],
                               columns=['level'], aggfunc='max', fill_value=' ', observed=False).reset_index()

        # Переупорядочиваем уровни столбцов
        table.sort_values(by=['course', 'module', 'lesson'], ascending=False, inplace=True, ignore_index=True)
    except Exception as e:
        print(f'[ERROR] process data if fault, exception {e}')

    try:
        os.makedirs('excel_output', exist_ok=True)
        with pd.ExcelWriter(f'excel_output/{csv_filename}') as writer:
            try:
                table.to_excel(writer, sheet_name='Result')
            except Exception as e:
                pass
            df.to_excel(writer, sheet_name='Data')
    except Exception as e:
        print(f'[ERROR] save data if fault, exception {e}')