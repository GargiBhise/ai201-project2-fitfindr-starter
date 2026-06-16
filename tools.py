"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────


def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
        max_price:   Maximum price, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance.
        Returns an empty list if nothing matches.
    """
    # Guard against empty description
    if not description or not description.strip():
        return []

    # Load all listings from the mock dataset
    listings = load_listings()

    # Filter by price and size if provided
    filtered = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue

        if size is not None and size.lower() not in item["size"].lower():
            continue

        filtered.append(item)

    # Score each remaining item by keyword overlap with the description
    keywords = description.lower().split()
    scored = []

    for item in filtered:
        searchable = " ".join([
            item["title"],
            item["description"],
            item["category"],
            " ".join(item["style_tags"]),
            " ".join(item["colors"]),
            item.get("brand") or "",
        ]).lower()

        score = sum(1 for kw in keywords if kw in searchable)

        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]
    


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    if not new_item:
        return "I need a selected item before I can suggest an outfit."
    item_title = new_item.get("title", "this item")
    item_category = new_item.get("category", "clothing")
    item_colors = ", ".join(new_item.get("colors", []))
    item_tags = ", ".join(new_item.get("style_tags", []))

    wardrobe_items = wardrobe.get("items", []) if wardrobe else []

    if not wardrobe_items:
        prompt = f"""You are a fashion stylist. A user is considering buying this secondhand item:

Item: {item_title}
Category: {item_category}
Colors: {item_colors}
Style tags: {item_tags}

They haven't shared their wardrobe yet. Give them 1-2 general outfit ideas for this item.
Suggest what types of pieces would pair well with it. Be specific about styles, colors, and the overall vibe.
Keep the tone casual and helpful."""
    else:
        wardrobe_text = "\n".join([
            f"- {item.get('name', 'Unnamed item')} "
            f"({item.get('category', 'unknown category')}, "
            f"{', '.join(item.get('colors', []))})"
            for item in wardrobe_items
        ])

        prompt = f"""You are a fashion stylist. A user is considering buying this secondhand item:

Item: {item_title}
Category: {item_category}
Colors: {item_colors}
Style tags: {item_tags}

Their current wardrobe includes:
{wardrobe_text}

Suggest 1-2 complete outfit combinations using the new item and specific pieces from their wardrobe.
Be specific about which wardrobe pieces to pair together and why.
Keep the tone casual and helpful."""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return (
            f"I had trouble generating an outfit right now, but {item_title} would work best with pieces "
            "that match its colors, category, and overall style. Try pairing it with simple basics, "
            "balanced proportions, and shoes that fit the same vibe."
        )
    

# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """
    if not outfit or not outfit.strip():
        return (
            "I couldn't create a full fit card because the outfit suggestion was missing. "
            "Please create an outfit first, then I can turn it into a caption."
        )

    if not new_item:
        return (
            "I couldn't create a full fit card because the selected item was missing. "
            "Please choose a listing first."
        )

    item_title = new_item.get("title", "this thrifted find")
    price = new_item.get("price", "a good price")
    platform = new_item.get("platform", "a secondhand platform")
    colors = ", ".join(new_item.get("colors", []))
    style_tags = ", ".join(new_item.get("style_tags", []))

    prompt = f"""You are FitFindr, a secondhand fashion assistant.

Create a short, shareable outfit caption for this thrifted item and outfit.

Item:
- Title: {item_title}
- Price: ${price}
- Platform: {platform}
- Colors: {colors}
- Style tags: {style_tags}

Outfit:
{outfit}

Write 2-4 short sentences.
Make it sound like a real casual outfit caption, not a product description.
Mention the item, price, and platform naturally.
Make it specific to this outfit."""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            max_tokens=200,
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return (
            f"Found {item_title} for ${price} on {platform}, and it totally pulls the outfit together. "
            "The whole look feels easy, wearable, and thrifted in the best way."
        )
