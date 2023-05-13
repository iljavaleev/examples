from django.shortcuts import render

from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created


def order_create(request):
    cart = Cart(request)
    form = OrderCreateForm()
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                         product=item['product'],
                                         price=item['price'],
                                         quantity=item['quantity'])
                cart.clear()
                order_created.delay(order.id) # delay() method of the task to execute it asynchronously
            return render(request, 'orders/order/created.xhtml',
                          {'order': order})
    return render(request,
                  'orders/order/create.xhtml',
                  {'cart': cart, 'form': form})
