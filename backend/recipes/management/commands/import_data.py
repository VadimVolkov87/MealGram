"""Модуль пользовательского скрипта загрузки файла."""
import csv
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для импорта данных из CSV файла по указанной
    директории в модель."""

    def handle(self, *args, **kwargs):
        try:
            directory = os.path.join(
                os.path.dirname(__file__), '../../../data')
            os.chdir(directory)

            self.import_data('ingredients.csv', self.import_ingredients)

            self.stdout.write(
                self.style.SUCCESS('Импорт данных из CSV файла завершен.'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Произошла ошибка при импорте данных: {e}'))

    def import_data(self, file_name, import_function):
        """Метод для импорта данных из CSV файла."""
        with open(
                file_name, mode='r', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['name', 'measurement_unit']
            csv_reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            for row in csv_reader:
                import_function(row)

    def import_ingredients(self, row):
        """Импорт данных в модель Ingredient."""
        obj, created = Ingredient.objects.get_or_create(
            name=row['name'],
            measurement_unit=row['measurement_unit']
        )
        self.log_result(obj, created, 'ингредиент')

    def log_result(self, obj, created, model_name):
        """Метод вывода результатов импорта."""
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Добавлен {model_name} "{obj}"'))
        else:
            self.stdout.write(
                f'{model_name.capitalize()} "{obj}" уже существует!')
