class Dish:
    def __init__(self, dish_id: str = "", name: str = "", image: str = "", 
                 description: str = "", ingredients: str = "", price: float = 0.0, 
                 is_available: bool = True, category_id: str = ""):
        self.dishID = dish_id
        self.categoryID = category_id
        self.name = name
        self.image = image
        self.description = description
        self.ingredients = ingredients
        self.price = price
        self.isAvailable = is_available