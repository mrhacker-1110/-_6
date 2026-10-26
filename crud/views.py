from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItemForm
from .models import Item


def item_list(request):
    q = request.GET.get('q', '').strip()
    items = Item.objects.all()
    if q:
        items = items.filter(name__icontains=q)
    return render(request, 'crud/item_list.html', {'items': items, 'q': q})


def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, 'crud/item_detail.html', {'item': item})


def item_create(request):
    form = ItemForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Запись создана.')
        return redirect('crud:item_list')
    return render(request, 'crud/item_form.html', {'form': form, 'title': 'Создать'})


def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = ItemForm(request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Запись обновлена.')
        return redirect('crud:item_detail', pk=item.pk)
    return render(request, 'crud/item_form.html', {'form': form, 'title': 'Изменить'})


def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Запись удалена.')
        return redirect('crud:item_list')
    return render(request, 'crud/item_confirm_delete.html', {'item': item})
