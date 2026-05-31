import re

# Ordered (specific -> general). First matching rule wins.
# Each rule: (Product Type label, [substring keywords searched in lowercased name])
RULES = [
    # --- Non-home items Instamart sweeps into these categories (classified so
    #     they leave the "Other" bucket; clearly named so they can be ignored) ---
    ("USB / Pen Drive", ["pen drive", "pendrive", "flash drive", "external ssd", " ssd", "memory card", "micro sd", "microsd", "sandisk", "usb 2.0", "usb 3"]),
    ("Umbrella", ["umbrella"]),
    ("Raincoat / Rain Gear", ["raincoat", "rain coat", "poncho", "rainwear", "rain suit", "rainsuit", "rain cover", "rain cape", "rain pant", "rain jacket", "rain trouser", "hiking jacket", "waterproof jacket"]),
    # --- Bathroom / cleaning fixtures ---
    ("Health Faucet", ["health faucet"]),
    ("Faucet / Tap", ["faucet", "bib cock", "tap extender", " cock ", "tapset", "shower head", "pillar tap", "bib tap", "swan neck", " tap ", "tap (", "diverter", "spout", "angle valve", "overhead shower", "rain shower", "shower arm"]),
    ("Water Saver / Aerator", ["aerator", "water saver", "water saving"]),
    ("Water/Shower Filter", ["shower filter", "tap & shower", "shower & tap", "water filter", "water purifier", "filter cartridge", "sfu", "sfc"]),
    ("Toilet Roll Holder", ["toilet roll", "tissue holder", "paper holder"]),
    ("Toilet Brush", ["toilet brush"]),
    ("Bathrobe", ["bathrobe", "bath robe"]),
    ("Bath Mat", ["bathmat", "bath mat"]),
    ("Shower Curtain", ["shower curtain"]),
    ("Bath Salt", ["bath salt"]),
    ("Bathroom Set", ["bathroom set"]),
    ("Soap Dispenser", ["soap dispenser", "dishwash dispenser", "lotion dispenser", "sanitizer dispenser"]),
    ("Soap Case / Dish", ["soap case", "soap dish", "soap holder"]),
    ("Bath/Hand/Face Towel", ["bath towel", "hand towel", "face towel", "towel set", "towel rack", "bath linen", " towel"]),
    # --- Cleaning tools ---
    ("Spin Mop", ["spin mop"]),
    ("Mop / Refill", ["mop", "paucha"]),
    ("Dustpan", ["dustpan", "dust pan"]),
    ("Broom", ["broom", "jhadu"]),
    ("Wiper", ["wiper", "sqeezee", "squeegee"]),
    ("Duster", ["duster"]),
    ("Dustbin", ["dustbin", "dust bin", "trash", "garbage", "pedal bin"]),
    ("Cleaning Brush", ["cleaning brush", "tile brush", "bottle brush", "scrub brush", "cloth brush"]),
    ("Gloves", ["gloves", "glove"]),
    ("Cleaning Wipes", ["wipes", "wipe ", "tissue roll", "kitchen tissue"]),
    ("Sponge / Scrub", ["sponge", "scrub pad", "scrubber", "scubber"]),
    ("Microfiber/Cleaning Cloth", ["microfiber cloth", "mop cloth", "cleaning cloth", "dish cloth", "duster cloth"]),
    ("All-Purpose Cleaner", ["all purpose cleaner", "cleaner spray", "cleaning spray", "degreaser", "oven cleaner", "floor cleaner", "disinfectant", "tile cleaner", "surface cleaner", "wd-40", "wd40"]),
    # --- Home improvement / hardware ---
    ("Pad Lock", ["pad lock", "padlock", "cycle lock", "locking pad", "cable lock", "anti theft lock", "wheel clamp", "number lock"]),
    ("Door Stopper / Strip", ["door stopper", "door sealing", "door strip", "door guard", "door silencer", "door buffer"]),
    ("Door Lock / Hardware", ["cylindrical lock", "mortise", "door lock", "door closer", "door handle", "lever lock", "locking mechanism", "smart lock", "tower bolt", "aldrop", "main door", "latch"]),
    ("Furniture", ["end table", "laptop table", "study table", "office table", "side table", "coffee table", "folding table", "dining table", "plastic table", "round table", "portable table", "center table", "bedside table", "tv table", "recliner", "armchair", "arm chair", " chair"]),
    ("Pen Stand / Desk Organizer", ["pen stand", "pen holder", "desk organizer", "desk organiser"]),
    ("Paint / Primer", ["metal paint", " paint ", "primer", "masking tape", "wall putty"]),
    ("Floor Tile / Mat", ["interlocking tile", "floor tile"]),
    ("Key Chain", ["key chain", "keychain"]),
    ("Key Holder", ["key holder"]),
    ("Cloth Hanger", ["cloth hanger"]),
    ("Wall Hook", ["wall hook", "adhesive hook", "self adhesive hook", "hanging hook", "hooks", " hook"]),
    ("Ladder", ["ladder"]),
    ("Ironing Board", ["ironing board"]),
    ("Garden Hose / Nozzle", ["hose", "nozzle"]),
    ("Measuring Tape", ["measuring tape"]),
    ("Sewing Kit", ["sewing kit"]),
    ("Adhesive / Sealant", ["m-seal", "epoxy", "adhesive compound", "glue gun", "wood adhesive"]),
    ("Mouse/Pest Control", ["mouse trap", "fire extinguisher", "boric acid", "moisture absorber"]),
    ("Connection Pipe", ["connection pipe", "gas hose", "rubber pipe", "hose pipe", "flexible tube", "metallic tube", "pvc connection", "connection deluxe"]),
    ("Water Dispenser Pump", ["dispenser pump", "water dispenser"]),
    ("TDS / Water Tester", ["tds", "water tester"]),
    ("Furniture Pads", ["furniture pads", "bumper pads", "floor & furniture"]),
    # --- Storage & organization ---
    ("Laundry Basket", ["laundry basket", "laundry bag"]),
    ("Shoe Rack", ["shoe rack"]),
    ("Cloth Hanger", ["cloth hanger", "hanger set", "velvet hanger", " hanger"]),
    ("Cloth Clip / Peg", ["cloth clip", "cloth peg", "clothes peg", "clip -", "clips", "seal clip", " peg "]),
    ("Cloth Drying Stand", ["cloth dryer", "drying stand", "cloth drying stand", "dryer stand", "cloth stand", "hang dryer", "hanging dryer"]),
    ("Cloth Rope / Line", ["cloth rope", "drying rope", "clothesline", "cloth line", "wire rope"]),
    ("Wardrobe/Cloth Organizer", ["wardrobe", "cloth organizer", "cloth organiser", "innerwear", "blouse", "saree cover", "saree bag", "coat cover", "blanket cover", "shirt cover", "garment cover", "jewellery organizer", "jewellery organiser", "jewellery storage", "jewellery case", "jewellery box"]),
    ("Storage Box / Organizer", ["storage box", "cotton box", "storage organiser", "storage organizer", "organiser", "organizer", "drawer organizer", "spice organiser", "shelf divider", "lazy susan", "under-bed", "under bed"]),
    ("Storage Bag / Pouch", ["storage bag", "zip lock", "ziplock", "seal bag", "zip seal", "slide seal", "drawstring", "storage pouch", "fridge bag", "potli", "toiletry bag", "toiletry pouch", "travel pouch", "cosmetic bag", "cosmetic pouch", "compression pouch", "makeup pouch", "vanity bag", "travel bag", "sling bag", "wine bag", "luggage", "blanket storage"]),
    ("Medicine / First Aid Box", ["medicine box", "first aid"]),
    ("Shelf / Rack", ["shelf", "rack", "spice rack", "corner stand", "tier stand", "step stand", "multipurpose stand"]),
    ("Bangle / Vanity Box", ["bangle box", "makeup organizer", "makeup organiser", "vanity"]),
    # --- Home decor ---
    ("Candle / Diya Holder", ["candle holder", "tealight holder", "tea light holder", "t-light holder", "diya holder", "candle stand", "votive", "candle holders"]),
    ("Tea Light Candle", ["tea light", "tealight"]),
    ("Scented Candle", ["scented candle", "soy wax", "wax candle", "candle set", "candle "]),
    ("Candle", ["candle"]),
    ("Diya", ["diya", "oil lamp", "wick holder"]),
    ("Reed Diffuser", ["diffuser", "oil diffuser", "kapoor dani"]),
    ("Air Freshener / Fragrance", ["air freshener", "room freshener", "fragrance oil", "camphor", "incense", "agarbatti", "dhoop", "room spray", "aroma oil"]),
    ("Artificial Plant / Flower", ["artificial", "bonsai", "potted plant"]),
    ("Curtain", ["curtain", "drape"]),
    ("Fridge Magnet", ["fridge magnet", "refrigerator magnet"]),
    ("Cushion / Cover", ["cushion"]),
    ("Wall Clock", ["wall clock", " clock", "table clock", "alarm clock"]),
    ("Wall Art / Print", ["art print", "wall art", "wall decor", "wall hanging", "wallpaper", "painting", "poster"]),
    ("Wall Mirror", ["mirror"]),
    ("Showpiece / Figurine", ["showpiece", "figurine", "statue", "idol", "miniature", "globe", "home decor", "decorative", "table decor", "decor plates", "table accent"]),
    ("Photo Frame", ["photo frame", "picture frame"]),
    ("Vase / Pot", ["vase", "flower pot", "planter", "desk pot"]),
    # --- Kitchen tools (Instamart's deeper catalog) ---
    ("Lemon Squeezer", ["lemon squeezer", "squeezer"]),
    ("Masher", ["masher", "smasher"]),
    ("Sprout Maker", ["sprout maker", "sprout diet"]),
    ("Bar Tool / Corkscrew", ["corkscrew", "muddler", "cocktail", "jigger", "bar tool", "peg measure", "bottle stopper", "wine stopper"]),
    ("Tissue Box", ["tissue box"]),
    ("Can / Jar Opener", ["can opener", "coconut opener", "tin opener", "jar opener"]),
    ("Bread / Roti Box", ["bread box", "chapati box", "roti box"]),
    ("Dehumidifier", ["dehumidifier"]),
    ("Juicer", ["juicer", "juice press", "salad spinner"]),
    ("Kitchen Scale", ["weighing scale", "kitchen scale", "food scale"]),
    ("Ice Tray / Pop Mould", ["ice tray", "ice pop", "ice cube", "ice pail", "popsicle"]),
    ("Dough Press / Maker", ["dough press", "kitchen press", "puran maker", "puran machine", "muruku", "sev sancha", "sancha", "samosa", "samosha", "gujiya", "karanji", "kachori", "modak maker"]),
    ("Funnel", ["funnel"]),
    ("Baking Paper / Foil", ["bake & wrap", "bake and wrap", "parchment", "butter paper", "aluminium foil", "aluminum foil", "cling film", "cling wrap"]),
    ("Idli / Steamer Maker", ["menduwada", "medu vada", "vada maker", "wada maker"]),
    ("Grill / Toaster Pan", ["grill pan", "grill toaster", "waffle toaster", "sandwich toaster", "gas toaster", "griller", "barbeque", "barbecue", "bbq", "tandoor"]),
    ("Milk Pan / Tope", ["milk pan", " tope", "patila", "bhagona", "tea pan", "sauce pot"]),
    ("Puja Item / Lota", ["lota", "kalash", "puja", "pooja", "urli", "haldi kumkum"]),
    # --- Kitchen & dining ---
    ("Pressure Cooker", ["pressure cooker"]),
    ("Cookware / Pan", ["kadai", "kadhai", "handi ", "roaster", "frying pan", "fry pan", "tawa", "saucepan", "cookware", "wok", "skillet", "multi pan", "tadka pan", "mini pan"]),
    ("Casserole", ["casserole", "serving pot", "hot pot", "hot case"]),
    ("Lunch Box / Tiffin", ["lunch box", "lunchbox", "tiffin", "meal box", "clip carrier"]),
    ("Lunch Set", ["lunch set"]),
    ("Thermal/Insulated Flask", ["thermal", "insulated", "flask", "tumbler", "vacuum"]),
    ("Bottle Opener", ["bottle opener"]),
    ("Oil Dispenser", ["oil dispenser", "oil bottle", "oil container"]),
    ("Bottle / Wine Holder", ["bottle holder", "wine holder", "wine rack"]),
    ("Water Bottle", ["bottle"]),
    ("Drinking Glass", ["whiskey glass", "water glass", "shot glass", "glass set", "wine glass", "juice glass", "drinking glass"]),
    ("Mug / Cup", ["mug", "cup", "kulhad", "kulhar"]),
    ("Bowl", ["bowl", "katori"]),
    ("Plate Stand / Rack", ["plate stand", "plate rack", "plate holder", "plate display"]),
    ("Dinner Set / Plate", ["dinner set", "dinner plate", "plate set", "quarter plate", "thali", "bhojan patra", "parat", "platter", "meal set", "kids meal", "chip n dip", "chip and dip", "opalware", "plate"]),
    ("Serving Tray", ["tray"]),
    ("Jar / Canister", ["jar", "canister"]),
    ("Storage Container", ["container", "containers", "dabba", "apple pot"]),
    ("Spice Box", ["spice box", "masala box", "masala dabba"]),
    ("Cutlery Holder / Caddy", ["cutlery holder", "cutlery caddy", "utensil holder"]),
    ("Ladle / Skimmer", ["ladle", "skimmer", "cooking spoon"]),
    ("Cutlery (Spoon/Fork)", ["spoon", "fork", "cutlery", "chopstick", "server set", "cake knife"]),
    ("Knife", ["knife", "knives"]),
    ("Chopping Board", ["chopping board", "cutting board", "wooden board", "serving board", "cheese board"]),
    ("Chopper / Peeler / Grater", ["chopper", "cutter", "slicer", "multislice", "grater", "scraper", "coconut scraper", "peeler"]),
    ("Hand Blender / Mixer", ["blender", "hand mixer", "whisk", "beater"]),
    ("Baking Mould / Tray", ["baking", "mould", "mold", "muffin", "cake pan"]),
    ("Napkin Holder / Ring", ["napkin holder", "napkin ring", "tissue box holder"]),
    ("Kitchen Cloth / Apron", ["kitchen cloth", "apron", "kitchen towel", "roti cloth", "rumal", "napkin"]),
    ("Gift Box / Hamper", ["gift box", "gift set", "hamper"]),
    ("Colander / Strainer", ["colander", "strainer", "sieve", "sink strainer"]),
    ("Rolling Pin / Roti Maker", ["belan", "rolling pin", "chakla", "roti maker"]),
    ("Salt & Pepper / Cruet", ["salt & pepper", "salt and pepper", "salt n pepper", "salt-pepper", "cruet"]),
    ("Shaker / Sipper", ["shaker", "sipper", "sippy"]),
    ("Table Linen / Mat", ["table runner", "table mat", "placemat", "place mat", "coaster", "dining mat"]),
    # --- Cleaning extras ---
    ("Lint Roller", ["lint roller"]),
    ("Floor Cloth / Pocha", ["floor cloth", "pocha", "pocha", "floor wipe"]),
    ("Screen / Lens Cleaner", ["screen cleaning", "screen cleaner", "lens cleaner", "gadget", "smartphone wipes"]),
    ("Dish / Sink Brush", ["dish and kitchen sink", "sink brush", "dish brush", "dishwash brush"]),
    ("Plunger", ["plunger"]),
    # --- Bathroom extras ---
    ("Bathroom Accessory Set", ["bathroom accessory", "bathroom accessories"]),
    ("Bucket", ["bucket", "tub "]),
    ("Bath Stool / Stool", ["stool"]),
    ("Toothbrush Holder", ["toothbrush holder", "tooth brush holder"]),
    ("Soap Case / Dish", ["soap case", "soap dish"]),
    ("Floor Drainer / Trap", ["floor drainer", "drainer", "floor trap", "grating", "flange"]),
    ("Hair Wrap / Towel", ["hair wrap", "hair towel"]),
    ("Washing Machine Accessory", ["washing machine", "anti-vibration", "anti vibration"]),
    # --- Appliances & kitchen extras ---
    ("Induction Cooktop", ["induction cooktop", "induction cook top", "induction stove", "induction"]),
    ("Gas Stove", ["gas stove", "gas burner", "cooktop", "burners", "burner"]),
    ("Gas Lighter", ["gas lighter", "lighter"]),
    ("Teapot / Kettle", ["teapot", "tea pot", "kettle"]),
    ("Sauce Pan / Appe Pan", ["sauce pan", "appe pan", "appam", "appe patra", "cast iron", "pre seasoned", "pre-seasoned"]),
    ("Tong / Pakad", ["tong", "pakad", "pakkad", "chimta"]),
    ("Butter / Serving Dish", ["butter dish", "serving dish"]),
    ("Ice Cream Scoop", ["scoop"]),
    ("Trivet / Pot Holder", ["trivet", "pot holder", "pot stand", "cork pot", "table ring"]),
    ("Jug", ["jug"]),
    # --- Storage / bags / covers ---
    ("Shopping / Lunch Bag", ["lunch bag", "shopping bag", "jute bag", "bag for fruit", "grocery bag", "bag - big", "tote"]),
    ("Cylinder Trolley", ["cylinder trolley", "trolley"]),
    ("Appliance Cover", ["refrigerator cover", "fridge cover", "appliance cover"]),
    ("Table Cover / Cloth", ["table cover", "table cloth", "tablecloth"]),
    ("Drying Mat", ["drying mat", "dish mat", "drain mat", "dry mat"]),
    ("Spatula / Turner", ["spatula", "turner", "flipper", "palta"]),
    ("Idli / Steamer Maker", ["idli", "paniyarakal", "paniyaram", "dosa", "steamer", "modak"]),
    ("Milk Boiler", ["milk boiler", "boiler"]),
    ("Kitchen Scissors", ["scissors", "scissor"]),
    ("Tea Infuser", ["infuser"]),
    ("Drinking Straw", ["straw"]),
    ("Bread / Atta Maker", ["bread maker", "atta maker", "bread & atta"]),
    ("Cake Stand", ["cake stand"]),
    ("Coffee Maker", ["coffee maker", "filter coffee", "moka", "french press"]),
    ("Rice / Food Server", ["rice server", "food server", "serving spoon", "pizza server", "salad server", " server"]),
    ("Basket (Multipurpose)", ["basket"]),
    ("Sealant / Gap Filler", ["sealant", "gap filler", "filler"]),
    ("Label / Sticker", ["label", "sticker"]),
    ("Repair / Cleaning Kit", ["cleaning kit", "repair kit", "tool kit", " kit "]),
    ("Glassware", ["glass"]),
    # catch-all for leftover generic boxes (all specific *box rules above win first)
    ("Storage Container", [" box", "box "]),
]


def classify(name):
    n = str(name).lower()
    if "dummy" in n:
        return "Other"
    for label, keys in RULES:
        for k in keys:
            if k in n:
                return label
    return "Other"


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_excel("blinkit_rca_combined.xlsx")
    df = df[df["Date"].astype(str) == "2026-04-01"]
    names = df["Product Name"].dropna().unique()
    from collections import Counter
    c = Counter(classify(n) for n in names)
    other = [n for n in names if classify(n) == "Other"]
    total = len(names)
    classified = total - c.get("Other", 0)
    print(f"Coverage: {classified}/{total} = {classified/total*100:.1f}% classified")
    print(f"Product types: {len(c)}")
    print("\n=== Type distribution (by SKU count) ===")
    for t, n in c.most_common():
        print(f"  {t:<30}{n}")
    print(f"\n=== Sample of UNCLASSIFIED ({len(other)}) ===")
    for o in other[:40]:
        print("  ", o[:70])
