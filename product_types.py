import re

# Ordered (specific -> general). First matching rule wins.
# Each rule: (Product Type label, [substring keywords searched in lowercased name])
RULES = [
    # --- Bathroom / cleaning fixtures ---
    ("Health Faucet", ["health faucet"]),
    ("Faucet / Tap", ["faucet", "bib cock", "tap extender", " cock "]),
    ("Water/Shower Filter", ["shower filter", "tap & shower", "shower & tap", "water filter", "filter cartridge", "sfu", "sfc"]),
    ("Toilet Roll Holder", ["toilet roll", "tissue holder", "paper holder"]),
    ("Toilet Brush", ["toilet brush"]),
    ("Bathrobe", ["bathrobe"]),
    ("Bathroom Set", ["bathroom set"]),
    ("Soap Dispenser", ["soap dispenser", "dishwash dispenser", "lotion dispenser", "sanitizer dispenser"]),
    ("Bath/Hand/Face Towel", ["bath towel", "hand towel", "face towel", "towel set", "towel rack", "bath linen", " towel"]),
    # --- Cleaning tools ---
    ("Spin Mop", ["spin mop"]),
    ("Mop / Refill", ["mop", "paucha"]),
    ("Broom", ["broom", "jhadu"]),
    ("Wiper", ["wiper", "sqeezee", "squeegee"]),
    ("Duster", ["duster"]),
    ("Dustpan", ["dustpan"]),
    ("Dustbin", ["dustbin", "trash", "garbage", "pedal bin"]),
    ("Cleaning Brush", ["cleaning brush", "tile brush", "bottle brush", "scrub brush", "cloth brush"]),
    ("Gloves", ["gloves", "glove"]),
    ("Cleaning Wipes", ["wipes", "wipe "]),
    ("Sponge / Scrub", ["sponge", "scrub pad", "scrubber"]),
    ("Microfiber/Cleaning Cloth", ["microfiber cloth", "mop cloth", "cleaning cloth", "dish cloth", "duster cloth"]),
    ("All-Purpose Cleaner", ["all purpose cleaner", "cleaner spray", "floor cleaner", "disinfectant", "wd-40", "wd40"]),
    # --- Home improvement / hardware ---
    ("Pad Lock", ["pad lock", "padlock", "cycle lock", "locking pad"]),
    ("Key Chain", ["key chain", "keychain"]),
    ("Key Holder", ["key holder"]),
    ("Wall Hook", ["wall hook", "adhesive hook", "self adhesive hook", "hanging hook", "hooks", " hook"]),
    ("Ladder", ["ladder"]),
    ("Ironing Board", ["ironing board"]),
    ("Garden Hose / Nozzle", ["hose", "nozzle"]),
    ("Measuring Tape", ["measuring tape"]),
    ("Sewing Kit", ["sewing kit"]),
    ("Adhesive / Sealant", ["m-seal", "epoxy", "adhesive compound", "glue gun", "wood adhesive"]),
    ("Mouse/Pest Control", ["mouse trap", "fire extinguisher", "boric acid", "moisture absorber"]),
    ("Connection Pipe", ["connection pipe", "gas hose", "rubber pipe", "hose pipe"]),
    ("Water Dispenser Pump", ["dispenser pump", "water dispenser"]),
    ("TDS / Water Tester", ["tds", "water tester"]),
    ("Furniture Pads", ["furniture pads", "bumper pads", "floor & furniture"]),
    # --- Storage & organization ---
    ("Laundry Basket", ["laundry basket", "laundry bag"]),
    ("Shoe Rack", ["shoe rack"]),
    ("Cloth Hanger", ["cloth hanger", "hanger set", "velvet hanger", " hanger"]),
    ("Cloth Clip / Peg", ["cloth clip", "cloth peg", "clip -", "clips"]),
    ("Cloth Rope / Drying", ["cloth rope", "drying rope", "clothesline", "cloth dryer", "drying stand"]),
    ("Wardrobe/Cloth Organizer", ["wardrobe", "cloth organizer", "cloth organiser", "innerwear", "blouse", "saree cover", "jewellery organizer", "jewellery organiser"]),
    ("Storage Box / Organizer", ["storage box", "storage organiser", "storage organizer", "organiser", "organizer", "drawer organizer", "spice organiser", "shelf divider", "lazy susan", "under-bed", "under bed"]),
    ("Storage Bag / Pouch", ["storage bag", "zip lock", "ziplock", "drawstring", "storage pouch", "fridge bag"]),
    ("Medicine / First Aid Box", ["medicine box", "first aid"]),
    ("Shelf / Rack", ["shelf", "rack", "spice rack"]),
    ("Bangle / Vanity Box", ["bangle box", "makeup organizer", "makeup organiser", "vanity"]),
    # --- Home decor ---
    ("Tea Light Candle", ["tea light", "tealight"]),
    ("Scented Candle", ["scented candle", "soy wax", "wax candle", "candle set", "candle "]),
    ("Candle / Diya Holder", ["candle holder", "tealight holder", "diya holder", "candle stand"]),
    ("Candle", ["candle"]),
    ("Diya", ["diya"]),
    ("Reed Diffuser", ["diffuser", "oil diffuser", "kapoor dani"]),
    ("Wall Clock", ["wall clock", "clock"]),
    ("Wall Art / Print", ["art print", "wall art", "wall decor", "wall hanging", "painting", "poster"]),
    ("Wall Mirror", ["mirror"]),
    ("Showpiece / Figurine", ["showpiece", "figurine", "statue", "idol", "miniature", "globe", "decor plates", "table accent"]),
    ("Photo Frame", ["photo frame", "picture frame"]),
    ("Vase / Pot", ["vase", "flower pot", "planter"]),
    # --- Kitchen & dining ---
    ("Pressure Cooker", ["pressure cooker"]),
    ("Cookware / Pan", ["kadai", "frying pan", "fry pan", "tawa", "saucepan", "cookware", "wok", "skillet"]),
    ("Casserole", ["casserole", "serving pot", "hot pot", "hot case"]),
    ("Water Bottle", ["bottle"]),
    ("Thermal/Insulated Flask", ["thermal", "insulated", "flask", "tumbler", "vacuum"]),
    ("Drinking Glass", ["whiskey glass", "water glass", "shot glass", "glass set", "wine glass", "juice glass", "drinking glass"]),
    ("Mug / Cup", ["mug", "cup"]),
    ("Bowl", ["bowl"]),
    ("Dinner Set / Plate", ["dinner set", "dinner plate", "plate set", "quarter plate", "thali", "platter", "plate"]),
    ("Serving Tray", ["tray"]),
    ("Jar / Canister", ["jar", "canister"]),
    ("Storage Container", ["container", "containers"]),
    ("Lunch Box / Tiffin", ["lunch box", "lunchbox", "tiffin"]),
    ("Spice Box", ["spice box", "masala box", "masala dabba"]),
    ("Cutlery (Spoon/Fork)", ["spoon", "fork", "cutlery", "ladle", "server set", "cake knife"]),
    ("Knife", ["knife", "knives"]),
    ("Chopping Board", ["chopping board", "cutting board"]),
    ("Vegetable Chopper", ["chopper", "cutter", "slicer", "grater", "peeler"]),
    ("Hand Blender / Mixer", ["blender", "hand mixer", "whisk", "beater"]),
    ("Baking Mould / Tray", ["baking", "mould", "mold", "muffin"]),
    ("Kitchen Cloth / Apron", ["kitchen cloth", "apron", "kitchen towel", "napkin"]),
    ("Gift Box / Hamper", ["gift box", "gift set", "hamper"]),
    ("Colander / Strainer", ["colander", "strainer", "sieve", "sink strainer"]),
    ("Rolling Pin / Roti Maker", ["belan", "rolling pin", "chakla", "roti maker"]),
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
    ("Bucket", ["bucket"]),
    ("Bath Stool / Stool", ["stool"]),
    ("Toothbrush Holder", ["toothbrush holder", "tooth brush holder"]),
    ("Soap Case / Dish", ["soap case", "soap dish"]),
    ("Floor Drainer / Trap", ["floor drainer", "drainer", "floor trap"]),
    ("Hair Wrap / Towel", ["hair wrap", "hair towel"]),
    ("Washing Machine Accessory", ["washing machine", "anti-vibration", "anti vibration"]),
    # --- Appliances & kitchen extras ---
    ("Induction Cooktop", ["induction cooktop", "induction cook top", "induction stove", "induction"]),
    ("Gas Stove", ["gas stove", "gas burner", "cooktop", "burners", "burner"]),
    ("Gas Lighter", ["gas lighter", "lighter"]),
    ("Teapot / Kettle", ["teapot", "tea pot", "kettle"]),
    ("Sauce Pan / Appe Pan", ["sauce pan", "appe pan", "cast iron", "pre seasoned", "pre-seasoned"]),
    ("Tong / Pakad", ["tong", "pakad", "chimta"]),
    ("Butter / Serving Dish", ["butter dish", "serving dish"]),
    ("Ice Cream Scoop", ["scoop"]),
    ("Trivet / Pot Holder", ["trivet", "pot holder"]),
    ("Jug", ["jug"]),
    ("Lunch Set", ["lunch set"]),
    # --- Storage / bags / covers ---
    ("Shopping / Lunch Bag", ["lunch bag", "shopping bag", "jute bag", "bag for fruit", "grocery bag", "bag - big", "tote"]),
    ("Cylinder Trolley", ["cylinder trolley", "trolley"]),
    ("Appliance Cover", ["refrigerator cover", "fridge cover", "appliance cover"]),
    ("Table Cover / Cloth", ["table cover", "table cloth", "tablecloth"]),
    ("Drying Mat", ["drying mat", "dish mat", "drain mat"]),
    ("Spatula / Turner", ["spatula", "turner", "flipper"]),
    ("Oil Dispenser", ["oil dispenser", "oil bottle", "oil container"]),
    ("Idli / Steamer Maker", ["idli", "paniyarakal", "paniyaram", "dosa", "steamer", "modak"]),
    ("Milk Boiler", ["milk boiler", "boiler"]),
    ("Kitchen Scissors", ["scissors", "scissor"]),
    ("Tea Infuser", ["infuser"]),
    ("Drinking Straw", ["straw"]),
    ("Bread / Atta Maker", ["bread maker", "atta maker", "bread & atta"]),
    ("Cake Stand", ["cake stand"]),
    ("Coffee Maker", ["coffee maker", "filter coffee", "moka", "french press"]),
    ("Rice / Food Server", ["rice server", "food server", "serving spoon"]),
    ("Basket (Multipurpose)", ["basket"]),
    ("Sealant / Gap Filler", ["sealant", "gap filler", "filler"]),
    ("Label / Sticker", ["label", "sticker"]),
    ("Repair / Cleaning Kit", ["cleaning kit", "repair kit", "tool kit", " kit "]),
    ("Glassware", ["glass"]),
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
