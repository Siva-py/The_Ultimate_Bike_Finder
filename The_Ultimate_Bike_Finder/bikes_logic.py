import json
import os
# ------- Path to your data -------
DATA_PATH = os.path.join("data", "bikes_data.json")

# ------- Helpers --------
def safe_int(s, default=None):
    if s is None:
        return default
    s = s.strip()
    if s == "":
        return default
    try:
        return int(float(s))
    except Exception:
        return default

def safe_float(s, default=None):
    if s is None:
        return default
    s = s.strip()
    if s == "":
        return default
    try:
        return float(s)
    except Exception:
        return default

def get_height_range_mm(user_height_cm):
    """Return comfortable seat height range (in mm) based on rider height."""
    if user_height_cm is None:
        return (0, 9999)
    if user_height_cm < 160:
        return (0, 785)
    elif 160 <= user_height_cm <= 175:
        return (760, 820)
    else:
        return (800, 9999)

def prompt_yes_no(prompt, default=False):
    ans = input(prompt + (" [y/N]: " if not default else " [Y/n]: ")).strip().lower()
    if ans == "":
        return default
    return ans[0] == "y"

# ------- Load Data -------
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        bikes = json.load(f)
except FileNotFoundError:
    print(f"Data file not found at: {DATA_PATH}")
    bikes = []

if not bikes:
    print("No bike data loaded. Fix DATA_PATH and re-run.")
    exit(1)

# ------- Interactive Input -------
def get_user_preferences():
    print("\n🏍️  Ultimate Bike Finder — interactive\n(press Enter to skip any question)\n")

    brand = input("Preferred brand (e.g. 'hero', 'honda', skip to accept any): ").strip()
    if brand == "":
        brand = None
    else:
        brand = brand.lower()

    bmin = safe_int(input("Min budget (INR): ").strip(), default=None)
    bmax = safe_int(input("Max budget (INR): ").strip(), default=None)
    if bmin is None and bmax is None:
        bmin, bmax = 0, 10**7
    elif bmin is None:
        bmin = int(max(0, bmax * 0.5))
    elif bmax is None:
        bmax = int(bmin * 1.5)

    min_mileage = safe_float(input("Minimum mileage (kmpl) (skip for no minimum): ").strip(), default=0.0)

    # Engine CC range
    engine_input = input("Engine CC (e.g. 'below 125', '125-200', 'above 200', or skip): ").strip()
    engine_min, engine_max = None, None
    if engine_input:
        e = engine_input.lower().replace("cc", "")
        if "-" in e:
            try:
                parts = e.split("-")
                engine_min, engine_max = int(parts[0]), int(parts[1])
            except:
                pass
        elif "below" in e or "<" in e:
            num = ''.join(ch for ch in e if ch.isdigit())
            engine_max = int(num) if num else None
        elif "above" in e or ">" in e:
            num = ''.join(ch for ch in e if ch.isdigit())
            engine_min = int(num) if num else None
        else:
            try:
                val = int(''.join(ch for ch in e if ch.isdigit()))
                engine_min, engine_max = val, val
            except:
                pass
    if engine_min is None and engine_max is None:
        engine_min, engine_max = 0, 5000

    user_height_cm = safe_int(input("Your height in cm (used for seat-height suitability, skip if unknown): ").strip(), default=None)

    ride_type = input("Ride type ('city', 'highway', 'both') [default both]: ").strip().lower()
    if ride_type not in ("city", "highway", "both"):
        ride_type = "both"

    wants_lightweight = prompt_yes_no("Prefer lightweight bikes? (improves maneuverability in city)", default=False)
    long_rides = prompt_yes_no("Do you plan many long rides/touring? (affects tank preference)", default=False)

    # 🚀 New: Bike type filter
    bike_type = input("Are you looking for a specific type (sport / commuter / adventure / cruiser)? (skip for any): ").strip().lower()
    if bike_type not in ("sports", "commuter", "adventure", "cruiser"):
        bike_type = None

    prefs = {
        "brand": brand,
        "budget_min": bmin,
        "budget_max": bmax,
        "min_mileage": min_mileage,
        "engine_min": engine_min,
        "engine_max": engine_max,
        "user_height_cm": user_height_cm,
        "ride_type": ride_type,
        "wants_lightweight": wants_lightweight,
        "long_rides": long_rides,
        "bike_type": bike_type,
    }

    print("\nApplied filters summary:", prefs)
    return prefs

# ------- Filtering & Scoring -------
def matches_engine(cc, mn, mx):
    try:
        cc = float(cc)
    except:
        return False
    if mn is not None and cc < mn:
        return False
    if mx is not None and cc > mx:
        return False
    return True

def filter_and_score(bikes, prefs):
    filtered = []
    min_price = prefs["budget_min"] * 0.9
    max_price = prefs["budget_max"] * 1.1
    seat_min_mm, seat_max_mm = get_height_range_mm(prefs["user_height_cm"])

    for b in bikes:
        if any(k not in b for k in ("price_inr", "engine_cc", "mileage_kmpl", "seat_height_mm", "kerb_weight_kg", "fuel_tank_l")):
            continue

        # Brand filter
        if prefs["brand"] and prefs["brand"] not in b.get("brand", "").lower():
            continue

        # 🏍️ Type filter
        if prefs["bike_type"] and prefs["bike_type"] not in b.get("category_group", "").lower():
            continue

        # Price filter
        price = b.get("price_inr", 0)
        if not (min_price <= price <= max_price):
            continue

        # Mileage filter
        if b.get("mileage_kmpl", 0) < prefs["min_mileage"]:
            continue

        # Engine filter
        if not matches_engine(b.get("engine_cc", 0), prefs["engine_min"], prefs["engine_max"]):
            continue

        # Seat height
        sh = b.get("seat_height_mm", None)
        if sh is None:
            continue
        if not (seat_min_mm - 20 <= sh <= seat_max_mm + 20):
            continue

        filtered.append(b)

    if not filtered:
        return []

    min_m = min(b["mileage_kmpl"] for b in filtered)
    max_m = max(b["mileage_kmpl"] for b in filtered)
    min_e = min(b["engine_cc"] for b in filtered)
    max_e = max(b["engine_cc"] for b in filtered)
    min_t = min(b["fuel_tank_l"] for b in filtered)
    max_t = max(b["fuel_tank_l"] for b in filtered)
    min_w = min(b["kerb_weight_kg"] for b in filtered)
    max_w = max(b["kerb_weight_kg"] for b in filtered)

    def norm(v, a, b):
        if b == a:
            return 0.0
        return (v - a) / (b - a)

    scored = []
    for b in filtered:
        mileage_score = norm(b["mileage_kmpl"], min_m, max_m)
        perf_score = norm(b["engine_cc"], min_e, max_e)
        tank_score = norm(b["fuel_tank_l"], min_t, max_t)
        weight_pen = norm(b["kerb_weight_kg"], min_w, max_w)
        comfort = b.get("comfort_level", 3) / 5.0

        w_mileage = 0.4 if prefs["min_mileage"] > 0 else 0.2
        w_perf = 0.2

        if prefs["ride_type"] == "city":
            w_weight, w_tank = 0.2, 0.1
        elif prefs["ride_type"] == "highway":
            w_weight, w_tank = 0.1, 0.3
        else:
            w_weight, w_tank = 0.15, 0.2

        light_bonus = 0.1 if (prefs["wants_lightweight"] and b["kerb_weight_kg"] < 140) else 0
        tank_bonus = 0.1 if (prefs["long_rides"] and b["fuel_tank_l"] > 12) else 0

        score = (w_mileage * mileage_score +
                 w_perf * perf_score +
                 0.3 * comfort +
                 w_tank * tank_score -
                 w_weight * weight_pen +
                 light_bonus + tank_bonus)

        scored.append((b, round(score, 3)))

    scored.sort(key=lambda x: (x[1], x[0]["mileage_kmpl"], x[0].get("comfort_level", 3)), reverse=True)
    return scored

# ------- Main -------
def main():
    prefs = get_user_preferences()
    scored = filter_and_score(bikes, prefs)

    print("\n🔎 Results:")
    if not scored:
        print("No bikes matched your filters. Try relaxing budget, engine range, or height preference.")
        return

    print(f"Found {len(scored)} matching bikes, showing top 10:\n")
    for i, (b, s) in enumerate(scored[:10], 1):
        print(f"{i}. {b.get('brand','').title()} {b.get('model','').title()}")
        print(f"    Type: {b.get('category_group','N/A').title()}")
        print(f"    Price: ₹{b.get('price_inr'):,}")
        print(f"    Mileage: {b.get('mileage_kmpl')} kmpl | Engine: {b.get('engine_cc')} cc")
        print(f"    Seat height: {b.get('seat_height_mm')/10:.1f} cm | Weight: {b.get('kerb_weight_kg')} kg")
        print(f"    Fuel tank: {b.get('fuel_tank_l')} L | Comfort: {b.get('comfort_level',3)}/5")
        print(f"    Score: {s}\n")




