class CartData():
    def __init__(self):
        self.cart = {}
        self.promo_code = None
        self.promo_code_id = None
        self.promo_discount = 0

    def clear(self):
        self.cart = {}
        self.promo_code = None
        self.promo_code_id = None
        self.promo_discount = 0
    
    def add_promo_code(self, code, id, discount):
        self.promo_code = code
        self.promo_code_id = id
        self.promo_discount = discount
    
    def get_promo_code(self):
        return self.promo_code
    
    def add_to_cart(self, product_id, price, name):
        if product_id in self.cart.keys():
            self.cart[product_id]["qty"] += 1
        else:
            self.cart[product_id] = {"qty": 1, "price": price, "name": name}
    
    def get_items(self):
        return self.cart.items()
    
    def remove_from_cart(self, product_id):
        if product_id in self.cart.keys():
            if self.cart[product_id]["qty"] > 1:
                self.cart[product_id]["qty"] -= 1
            else:
                del self.cart[product_id]

    def calculate_sub_total(self):
        total = 0.00
        for item in self.cart.items():
            price = float(item[1]["price"].split("$")[1])
            total += item[1]["qty"] * price
        return total
    
    def calculate_grand_total(self):
        sub_total = self.calculate_sub_total()
        if self.promo_code is not None:
            sub_total -= (self.promo_discount / 100) * sub_total
        
        return round(sub_total, 2)
    
    def is_empty(self):
        return len(self.cart.keys()) == 0

    def get_product_quantity(self, product_id):
        if product_id not in self.cart.keys():
            return 0
        return self.cart[product_id]["qty"]