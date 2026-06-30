"""Super-Category roll-up: maps each platform Category -> one of 5 Super Categories.
Kitchen · Soft Furnishings · Appliances · General Home Improvement / Decor · Others.
Shared across platforms, so Super Category is an apples-to-apples cross-platform axis.
"""
SUPER_CAT = {
    # ---- Kitchen ----
    'Kitchen & Dining Needs': 'Kitchen', 'Cookware': 'Kitchen', 'Bakeware & Bbq': 'Kitchen',
    'Barware': 'Kitchen', 'Bottles Flasks Tiffins': 'Kitchen', 'Cutlery & Ladles': 'Kitchen',
    'Drinkware & Bar': 'Kitchen', 'Gas Stove & Accessories': 'Kitchen', 'Glasses Cups Mugs': 'Kitchen',
    'Jars Containers Holders': 'Kitchen', 'Kitchen Aids': 'Kitchen', 'Kitchen Cleaning': 'Kitchen',
    'Kitchen Storage': 'Kitchen', 'Kitchen Tools': 'Kitchen', 'Lunch Boxes': 'Kitchen',
    'Plates Bowls Crockery': 'Kitchen', 'Pressure Cooker': 'Kitchen', 'Serveware': 'Kitchen',
    'Steel Utensils': 'Kitchen', 'Tableware': 'Kitchen', 'Storage & Organizers': 'Kitchen',
    # ---- Soft Furnishings ----
    'Home Furnishing': 'Soft Furnishings', 'Linen And Furnishing': 'Soft Furnishings',
    # ---- Appliances ----
    'Appliances': 'Appliances', 'Home Appliances': 'Appliances', 'Kitchen Appliances': 'Appliances',
    'Personal Care Appliances': 'Appliances',
    # ---- General Home Improvement / Decor ----
    'Home Decor': 'General Home Improvement / Decor', 'Home Improvement': 'General Home Improvement / Decor',
    'Cleaning Tools': 'General Home Improvement / Decor', 'Cleaning Aids': 'General Home Improvement / Decor',
    'Bathroom Essentials': 'General Home Improvement / Decor', 'Bath & Laundry': 'General Home Improvement / Decor',
    'Bathware & Laundry': 'General Home Improvement / Decor', 'Household Utility': 'General Home Improvement / Decor',
    'Utility & Tools': 'General Home Improvement / Decor', 'Gardening': 'General Home Improvement / Decor',
    'Flowers, Plants & Gardening': 'General Home Improvement / Decor', 'Pooja Needs': 'General Home Improvement / Decor',
    'Pooja & Worship Needs': 'General Home Improvement / Decor', 'Festive & Occasion Needs': 'General Home Improvement / Decor',
    'Festive Gifting': 'General Home Improvement / Decor', 'Party Essentials': 'General Home Improvement / Decor',
    'Garbage Bags': 'General Home Improvement / Decor', 'Tissues & Disposables': 'General Home Improvement / Decor',
    'Decorative Lights': 'General Home Improvement / Decor', 'Bulbs & Lights': 'General Home Improvement / Decor',
    'Lights & Bulbs': 'General Home Improvement / Decor',
    # ---- Others (electronics/electricals + non-home lifestyle) ----
    'Powerbanks Chargers Cables': 'Others', 'Extensions & Switches': 'Others', 'Hardware & Fittings': 'Others',
    'Sports & Fitness': 'Others', 'Sports & Gym': 'Others', 'Clothing, Footwear & Accessories': 'Others',
    'Bags': 'Others', 'Travel And Luggage': 'Others', 'Stationery Needs': 'Others', 'Stationery & Crafts': 'Others',
}
SUPER_ORDER = ['Kitchen', 'Appliances', 'Soft Furnishings', 'General Home Improvement / Decor', 'Others']


def super_of(category):
    return SUPER_CAT.get(str(category).strip(), 'Others')
