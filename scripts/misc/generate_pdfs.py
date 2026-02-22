"""Generate fake PDF files for testing document upload feature."""
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "fake_pdfs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DOCUMENTS = {
    "my_meal_plan.pdf": """My Weekly Meal Plan - January 2025

Monday
  Breakfast: Oatmeal with berries and honey (350 cal)
  Lunch: Grilled chicken salad with olive oil dressing (480 cal)
  Dinner: Salmon with roasted vegetables (520 cal)
  Snack: Greek yogurt with almonds (200 cal)

Tuesday
  Breakfast: Scrambled eggs with spinach and toast (400 cal)
  Lunch: Lentil soup with whole grain bread (420 cal)
  Dinner: Stir-fried tofu with quinoa and broccoli (490 cal)
  Snack: Apple with peanut butter (180 cal)

Wednesday
  Breakfast: Smoothie bowl with banana, mango, granola (380 cal)
  Lunch: Mediterranean wrap with hummus and veggies (450 cal)
  Dinner: Chicken stir fry with brown rice (560 cal)
  Snack: Mixed nuts and dried fruit (220 cal)

Weekly Nutrition Goals:
  Calories: 1800-2000/day
  Protein: 120g/day
  Carbs: 200g/day
  Fat: 65g/day
""",

    "dietary_restrictions.pdf": """Personal Dietary Restrictions & Preferences

Name: Alice
Last Updated: January 2025

ALLERGIES (Strict - Must Avoid):
  - Tree nuts (almonds, cashews, walnuts)
  - Shellfish (shrimp, crab, lobster)

INTOLERANCES (Prefer to Avoid):
  - Lactose - use dairy-free alternatives where possible
  - Gluten - prefer gluten-free options but not strict

DIETARY PREFERENCES:
  - Mostly plant-based, occasional fish and chicken
  - No red meat or pork
  - Prefer organic produce when available
  - Low sodium diet (max 1500mg/day)

HEALTH GOALS:
  - Weight management: maintain current weight
  - Increase protein intake for muscle recovery
  - Reduce processed sugar
  - Eat more leafy greens and cruciferous vegetables

FAVOURITE CUISINES:
  - Mediterranean
  - Japanese
  - Thai
  - Indian (mild spice level)
""",

    "grocery_list.pdf": """Weekly Grocery List

Produce:
  [ ] Spinach (200g bag)
  [ ] Cherry tomatoes (punnet)
  [ ] Broccoli (1 head)
  [ ] Zucchini (2)
  [ ] Bell peppers - red and yellow (2 each)
  [ ] Avocados (3)
  [ ] Lemons (4)
  [ ] Garlic (1 bulb)
  [ ] Ginger (small piece)
  [ ] Sweet potatoes (3)

Proteins:
  [ ] Salmon fillets (400g)
  [ ] Chicken breast (500g)
  [ ] Firm tofu (2 blocks)
  [ ] Eggs (12 pack)
  [ ] Canned chickpeas (2 tins)
  [ ] Red lentils (500g bag)

Grains & Pantry:
  [ ] Quinoa (500g)
  [ ] Brown rice (1kg)
  [ ] Rolled oats (1kg)
  [ ] Whole grain bread (1 loaf)
  [ ] Olive oil (500ml)
  [ ] Coconut milk (2 tins)
  [ ] Vegetable stock (1L)

Dairy & Alternatives:
  [ ] Greek yogurt (500g)
  [ ] Oat milk (1L)
  [ ] Feta cheese (150g)

Estimated Total: ~$85
""",
}


def make_pdf(text: str) -> bytes:
    """Build a minimal valid single-page PDF containing the given text."""
    lines = text.strip().splitlines()
    # Build BT (text) stream
    stream_lines = ["BT", "/F1 11 Tf", "50 750 Td", "14 TL"]
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"({safe}) Tj T*")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines)
    stream_bytes = stream.encode("latin-1", errors="replace")

    objects = []

    # obj 1: catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # obj 2: pages
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # obj 3: page
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 595 842] "
        b"/Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    # obj 4: content stream
    stream_obj = (
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode()
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )
    objects.append(stream_obj)
    # obj 5: font
    objects.append(
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    header = b"%PDF-1.4\n"
    body = b""
    offsets = []
    pos = len(header)
    for obj in objects:
        offsets.append(pos)
        body += obj
        pos += len(obj)

    xref_pos = len(header) + len(body)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n"

    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    )

    return header + body + xref.encode() + trailer.encode()


for filename, content in DOCUMENTS.items():
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "wb") as f:
        f.write(make_pdf(content))
    print(f"Created: {path}")

print(f"\nDone! {len(DOCUMENTS)} PDFs saved to: {os.path.abspath(OUTPUT_DIR)}")
