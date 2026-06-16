# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.


---

## Project Implementation Notes

## Tool Inventory

FitFindr uses three main tools. Each tool has a specific role in the agent flow. The first tool searches for listings, the second tool suggests an outfit, and the third tool creates a short fit card caption.

### `search_listings`

**Purpose:**  
`search_listings` looks through the mock secondhand listings and finds items that match the user's request. It checks the listing title, description, category, style tags, colors, and brand. It also uses the user's size and budget if they include those details.

**Inputs:**
- `description` (`str`): The item or style the user is looking for, such as `"vintage graphic tee"` or `"black combat boots"`.
- `size` (`str | None`): The requested size, such as `"M"`, `"S/M"`, or `"8"`. If the user does not give a size, this is `None`.
- `max_price` (`float | None`): The highest price the user wants to pay. If the user does not give a budget, this is `None`.

**Output:**  
A list of matching listing dictionaries, with the best matches first. Each listing includes details like title, description, category, style tags, size, condition, price, colors, brand, and platform. If nothing matches, the tool returns an empty list instead of crashing.

### `suggest_outfit`

**Purpose:**  
`suggest_outfit` takes the selected thrifted item and suggests how the user could style it. If the user has wardrobe items, the tool uses those pieces to make the outfit personal. If the wardrobe is empty, it gives general styling advice instead.

**Inputs:**
- `new_item` (`dict`): The listing selected from `search_listings`. This is the thrifted item the user is thinking about buying.
- `wardrobe` (`dict`): The user's wardrobe data. It contains an `"items"` list with clothing pieces the user already owns. This list can also be empty.

**Output:**  
A non-empty string with one or two outfit ideas. If the wardrobe has items, the response mentions specific pieces from the user's closet. If the wardrobe is empty, the response gives general outfit ideas based on the item’s color, category, and style tags.

### `create_fit_card`

**Purpose:**  
`create_fit_card` turns the outfit suggestion into a short caption that the user could save or share. The goal is to make the result feel like a real outfit caption, not just a product description.

**Inputs:**
- `outfit` (`str`): The outfit suggestion returned by `suggest_outfit`.
- `new_item` (`dict`): The selected thrifted listing. This gives the caption details like the item title, price, platform, colors, and style tags.

**Output:**  
A short caption string for the outfit. The caption usually mentions the thrifted item, the price, the platform, and the overall outfit vibe. If the outfit string is missing or empty, the tool returns a clear message explaining that it cannot create a full fit card without an outfit suggestion.


## Planning Loop

The agent first reads the user's message and pulls out the item description, size, and max price if the user included them. Then it calls `search_listings` with those details.

If `search_listings` returns no results, the agent stops early. It tells the user that nothing matched and suggests changing something specific, like raising the budget, removing the size filter, or using a broader search term.

If listings are found, the agent chooses the best match and saves it as `selected_item`. Then it calls `suggest_outfit` using that selected item and the user's wardrobe.

If the wardrobe is empty, the outfit suggestion is more general. If the wardrobe has items, the suggestion uses pieces from the user's closet. After an outfit suggestion exists, the agent calls `create_fit_card` to make a short caption.

The final response includes the selected listing, the outfit suggestion, and the fit card. The tools are not called unconditionally. Each later step depends on the previous step succeeding.


## State Management

The agent keeps track of important information in a session dictionary while it helps the user. This lets the result from one tool be reused by the next tool without asking the user to repeat anything.

The session stores the original query, parsed search details, search results, selected item, wardrobe, outfit suggestion, fit card, and any error message.

After `search_listings` finds results, the agent saves the best match as `session["selected_item"]`. Then `suggest_outfit` uses that same saved item along with `session["wardrobe"]`. After the outfit is created, it is saved as `session["outfit_suggestion"]`. Then `create_fit_card` uses both `session["outfit_suggestion"]` and `session["selected_item"]`.

If a failure happens, the session stores the error in `session["error"]`. For example, when search returns no listings, the agent saves an error message and returns early without creating an outfit or fit card.


## Error Handling

| Tool | Failure mode tested | What happens |
|---|---|---|
| `search_listings` | No listings match the query, such as `designer ballgown` with size `XXS` and max price `$5` | The tool returns an empty list `[]`. The agent stops early, stores a helpful message in `session["error"]`, and suggests raising the budget, removing the size filter, or using a broader search term. |
| `suggest_outfit` | The wardrobe is empty | The tool still returns a useful string with general styling advice. It does not crash or return an empty string. |
| `create_fit_card` | The outfit input is an empty string | The tool returns a descriptive message explaining that it cannot create a full fit card because the outfit suggestion is missing. |


## Spec Reflection

One way the spec helped during implementation was that it made the tool order very clear. I already knew that the agent should search first, save the best listing, use that saved listing to suggest an outfit, and only create a fit card after an outfit existed. This helped me avoid calling all three tools unconditionally.

One way the implementation diverged from the spec was the query parsing. In the spec, the query parsing was described more generally as extracting the description, size, and max price. In the actual implementation, I used simple regex and string cleanup instead of a more advanced parser or LLM-based parser because the project examples were predictable enough for that approach.

## AI Usage

I used AI when implementing `search_listings`. I gave the AI my Tool 1 plan, including the inputs `description`, `size`, and `max_price`, and asked it to help write a function that searched the mock listings. I kept the basic structure, but I reviewed the code and made sure it returned an empty list for an empty or impossible search instead of crashing.

I also used AI when implementing the planning loop in `agent.py`. I shared my Planning Loop and State Management sections and asked for help wiring the tools together. I changed the generated code by making sure it stored values in the session dictionary, returned early when `search_listings` found no results, and did not call `suggest_outfit` or `create_fit_card` when earlier steps failed.

I used AI again while debugging. When the happy path still returned `"Planning loop not yet implemented"`, I used AI to identify that the old placeholder code was still inside `run_agent()` and was overwriting the completed session. I removed the leftover placeholder lines so the agent returned the real session state.