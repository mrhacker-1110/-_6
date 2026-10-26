from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase
from django.urls import resolve, reverse

from . import views
from .forms import ItemForm
from .models import Item


def make_item(**kwargs):
    data = {'name': 'Тест', 'description': 'Описание', 'price': Decimal('100.00'), 'quantity': 5}
    data.update(kwargs)
    return Item.objects.create(**data)


class ItemModelTests(TestCase):
    """Тесты модели Item."""

    def test_create_item(self):
        """Объект создаётся и сохраняется в БД."""
        item = make_item()
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(item.name, 'Тест')

    def test_str_returns_name(self):
        """__str__ возвращает название."""
        self.assertEqual(str(make_item(name='Ноутбук')), 'Ноутбук')

    def test_default_quantity_is_zero(self):
        """Количество по умолчанию равно 0."""
        item = Item.objects.create(name='X', price=Decimal('1.00'))
        self.assertEqual(item.quantity, 0)

    def test_description_can_be_blank(self):
        """Описание может быть пустым."""
        item = Item.objects.create(name='X', price=Decimal('1.00'))
        self.assertEqual(item.description, '')

    def test_created_at_is_set(self):
        """Дата создания заполняется автоматически."""
        self.assertIsNotNone(make_item().created_at)

    def test_ordering_newest_first(self):
        """Сортировка: новые записи первыми."""
        first = make_item(name='Первый')
        second = make_item(name='Второй')
        self.assertEqual(list(Item.objects.all()), [second, first])

    def test_name_max_length(self):
        """Максимальная длина названия — 100."""
        self.assertEqual(Item._meta.get_field('name').max_length, 100)

    def test_price_required(self):
        """Цена обязательна (NULL запрещён)."""
        with self.assertRaises(IntegrityError):
            Item.objects.create(name='Без цены', price=None)


class ItemFormTests(TestCase):
    """Тесты формы ItemForm."""

    def test_valid_form(self):
        """Корректные данные проходят валидацию."""
        form = ItemForm(data={'name': 'A', 'description': '', 'price': '10.50', 'quantity': 1})
        self.assertTrue(form.is_valid())

    def test_empty_form_invalid(self):
        """Пустая форма не проходит валидацию."""
        form = ItemForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('price', form.errors)

    def test_negative_price_invalid(self):
        """Отрицательная цена отклоняется."""
        form = ItemForm(data={'name': 'A', 'price': '-5', 'quantity': 1})
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_negative_quantity_invalid(self):
        """Отрицательное количество отклоняется."""
        form = ItemForm(data={'name': 'A', 'price': '5', 'quantity': -1})
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_name_too_long_invalid(self):
        """Слишком длинное название отклоняется."""
        form = ItemForm(data={'name': 'a' * 101, 'price': '5', 'quantity': 1})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_saves_object(self):
        """Форма сохраняет объект в БД."""
        form = ItemForm(data={'name': 'Save', 'price': '7.00', 'quantity': 2})
        self.assertTrue(form.is_valid())
        item = form.save()
        self.assertEqual(Item.objects.get(pk=item.pk).name, 'Save')


class ItemUrlTests(TestCase):
    """Тесты маршрутов."""

    def test_list_url_resolves(self):
        """URL списка связан с item_list."""
        self.assertEqual(resolve(reverse('crud:item_list')).func, views.item_list)

    def test_create_url_resolves(self):
        """URL создания связан с item_create."""
        self.assertEqual(resolve(reverse('crud:item_create')).func, views.item_create)

    def test_detail_url_resolves(self):
        """URL просмотра связан с item_detail."""
        self.assertEqual(resolve(reverse('crud:item_detail', args=[1])).func, views.item_detail)

    def test_update_url_resolves(self):
        """URL изменения связан с item_update."""
        self.assertEqual(resolve(reverse('crud:item_update', args=[1])).func, views.item_update)

    def test_delete_url_resolves(self):
        """URL удаления связан с item_delete."""
        self.assertEqual(resolve(reverse('crud:item_delete', args=[1])).func, views.item_delete)


class ItemReadViewTests(TestCase):
    """Тесты чтения (R): список, поиск, детальная страница."""

    def test_list_status_and_template(self):
        """Список: код 200 и нужный шаблон."""
        response = self.client.get(reverse('crud:item_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_list.html')

    def test_list_empty_message(self):
        """Пустой список показывает сообщение."""
        response = self.client.get(reverse('crud:item_list'))
        self.assertContains(response, 'Записей нет.')

    def test_list_shows_items(self):
        """Список отображает записи."""
        make_item(name='Мышь')
        response = self.client.get(reverse('crud:item_list'))
        self.assertContains(response, 'Мышь')
        self.assertEqual(len(response.context['items']), 1)

    def test_search_filters_items(self):
        """Поиск фильтрует записи по названию."""
        make_item(name='Клавиатура')
        make_item(name='Монитор')
        response = self.client.get(reverse('crud:item_list'), {'q': 'Монит'})
        names = [i.name for i in response.context['items']]
        self.assertEqual(names, ['Монитор'])

    def test_search_no_results(self):
        """Поиск без совпадений возвращает пусто."""
        make_item(name='Клавиатура')
        response = self.client.get(reverse('crud:item_list'), {'q': 'zzz'})
        self.assertEqual(len(response.context['items']), 0)

    def test_detail_ok(self):
        """Детальная страница открывается."""
        item = make_item(name='Принтер')
        response = self.client.get(reverse('crud:item_detail', args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_detail.html')
        self.assertContains(response, 'Принтер')

    def test_detail_404(self):
        """Несуществующий объект — 404 (просмотр)."""
        response = self.client.get(reverse('crud:item_detail', args=[999]))
        self.assertEqual(response.status_code, 404)


class ItemCreateViewTests(TestCase):
    """Тесты создания (C)."""

    def test_get_form(self):
        """GET формы создания — код 200."""
        response = self.client.get(reverse('crud:item_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_form.html')

    def test_post_valid_creates_and_redirects(self):
        """Валидный POST создаёт запись и делает редирект."""
        response = self.client.post(reverse('crud:item_create'),
                                    {'name': 'Новый', 'description': 'd', 'price': '99.90', 'quantity': 3})
        self.assertRedirects(response, reverse('crud:item_list'))
        self.assertTrue(Item.objects.filter(name='Новый').exists())

    def test_post_invalid_does_not_create(self):
        """Невалидный POST не создаёт запись."""
        response = self.client.post(reverse('crud:item_create'), {'name': '', 'price': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.count(), 0)
        self.assertTrue(response.context['form'].errors)

    def test_post_negative_price_rejected(self):
        """POST с отрицательной ценой отклоняется."""
        self.client.post(reverse('crud:item_create'), {'name': 'A', 'price': '-1', 'quantity': 1})
        self.assertEqual(Item.objects.count(), 0)

    def test_success_message_shown(self):
        """После создания показывается сообщение."""
        response = self.client.post(reverse('crud:item_create'),
                                    {'name': 'A', 'price': '1', 'quantity': 1}, follow=True)
        self.assertContains(response, 'Запись создана.')


class ItemUpdateViewTests(TestCase):
    """Тесты изменения (U)."""

    def setUp(self):
        self.item = make_item(name='Старое')

    def test_get_form_prefilled(self):
        """Форма изменения заполнена данными объекта."""
        response = self.client.get(reverse('crud:item_update', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].instance, self.item)

    def test_post_valid_updates(self):
        """Валидный POST обновляет запись."""
        url = reverse('crud:item_update', args=[self.item.pk])
        response = self.client.post(url, {'name': 'Новое', 'description': '', 'price': '5.00', 'quantity': 9})
        self.assertRedirects(response, reverse('crud:item_detail', args=[self.item.pk]))
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Новое')
        self.assertEqual(self.item.quantity, 9)

    def test_post_invalid_keeps_data(self):
        """Невалидный POST не меняет данные."""
        url = reverse('crud:item_update', args=[self.item.pk])
        response = self.client.post(url, {'name': '', 'price': '5', 'quantity': 1})
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Старое')

    def test_update_404(self):
        """Несуществующий объект — 404 (изменение)."""
        response = self.client.get(reverse('crud:item_update', args=[999]))
        self.assertEqual(response.status_code, 404)


class ItemDeleteViewTests(TestCase):
    """Тесты удаления (D)."""

    def setUp(self):
        self.item = make_item()

    def test_get_confirm_page(self):
        """GET показывает подтверждение, объект не удалён."""
        response = self.client.get(reverse('crud:item_delete', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/item_confirm_delete.html')
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_post_deletes_and_redirects(self):
        """POST удаляет запись и делает редирект."""
        response = self.client.post(reverse('crud:item_delete', args=[self.item.pk]))
        self.assertRedirects(response, reverse('crud:item_list'))
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_delete_404(self):
        """Несуществующий объект — 404 (удаление)."""
        response = self.client.post(reverse('crud:item_delete', args=[999]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Item.objects.count(), 1)
