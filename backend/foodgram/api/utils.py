from os import path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from foodgram.settings import PDF_APP_STATIC


def get_data_for_shopping_list(items):
    final_list = {}
    for item in items:
        name = item['name']
        if name not in final_list:
            final_list[name] = {
                'measurement_unit': item['ingredient__measurement_unit'],
                'amount': item['total']
            }
    app_path = PDF_APP_STATIC
    font_path = path.join(app_path, 'Slimamif.ttf')
    pdfmetrics.registerFont(TTFont('Slimamif', font_path))
    return final_list


def create_shopping_list_pdf(response, final_list):
    page = canvas.Canvas(response)
    page.setFont('Slimamif', size=24)
    page.drawString(200, 800, 'Список ингредиентов')
    page.setFont('Slimamif', size=16)
    height = 750
    for i, (name, data) in enumerate(final_list.items(), 1):
        page.drawString(75, height, (f'{i}. {name} - {data["amount"]}, '
                                     f'{data["measurement_unit"]}'))
        height -= 25
    page.showPage()
    page.save()
    return response
