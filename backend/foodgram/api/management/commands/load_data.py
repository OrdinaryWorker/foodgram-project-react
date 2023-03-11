import json

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient, Tag

TABLES = (
    (Ingredient, "ingredients.json"),
    (Tag, "tags.json"),
)


class Command(BaseCommand):
    help = "Загружает данные из файлов (data/*.json) в базу данных"

    def handle(self, *args, **options):
        verbosity = options["verbosity"]
        if verbosity > 0:
            self.stdout.write("Загрузка тестовых данных...")
        for model, file_name in TABLES:
            file_path = f"data/{file_name}"
            try:
                with open(file_path, "rt", encoding="utf-8") as json_file:
                    json_data = json.load(json_file)
                    for data in json_data:
                        obj, created = model.objects.get_or_create(**data)
                        if verbosity > 1:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"{obj} - создан: {'да' if created else 'нет'}"
                                )
                            )
                    if verbosity > 0:
                        self.stdout.write(
                            self.style.SUCCESS(f"{file_name} - готово")
                        )
            except Exception as error:
                raise CommandError(
                    f"При загрузке файла {file_name} произошла ошибка." f"\r\n{error}"
                )
