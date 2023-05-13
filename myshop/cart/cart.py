from decimal import Decimal
from django.conf import settings
from shop.models import Product
from django.http import HttpResponseNotFound


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault(settings.CART_SESSION_ID, dict())

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in
                   self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        self.cart.setdefault(product_id, {
            'quantity': 0,
            'price': str(product.price)
        })
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        try:
            del self.cart[str(product.id)]
        except KeyError:
            return HttpResponseNotFound('This product doens\'t exists yet')
        self.save()

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()
