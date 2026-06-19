# FitFindr

Thrifting is already a sport. You are jumping between resale apps, trying to picture how a piece fits with what you already own, and guessing whether the price is worth it.

FitFindr makes that process smarter. A user describes what they are looking for in plain English, and the agent searches secondhand listings, suggests how to style the selected item with their wardrobe, and generates a short fit card caption.

This is a multi-tool AI agent built with Python, Gradio, Groq’s `llama-3.3-70b-versatile`, and a mock thrift dataset. The main focus is not just the individual tools, but the planning loop that decides which tool to call, when to stop, and how to pass state between steps.

## Features

* Search mock secondhand listings using natural language
* Filter listings by size and maximum price
* Suggest outfit ideas using a selected thrifted item and wardrobe data
* Generate short fit card captions
* Handle empty search results with a helpful early exit
* Handle empty wardrobes with general styling advice
* Use session state to pass data between tools
* Provide an end-to-end Gradio interface

## Tech Stack

* Python
* Gradio
* Groq API
* `llama-3.3-70b-versatile`
* JSON mock data
* Pytest

## Setup

Clone the project and create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

On macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root and add your Groq API key:

```text
GROQ_API_KEY=your_key_here
```

## Run the App

```bash
python app.py
```

This opens a Gradio UI locally. Try a query like:

```text
90s track jacket size M under $45
```

## Run Tests

```bash
pytest tests/
```

## How It Works

A user types a natural language query. The agent parses the query, searches the listings, picks the best match, generates outfit ideas using the user’s wardrobe, and writes a fit card caption.

If the search returns no results, the agent stops early and gives the user a helpful message instead of trying to run the outfit and fit card tools with missing data.

The important design constraint is that the agent should not just run the same three tools every time. Its behavior changes based on what each step returns.

## Tools

### `search_listings(description, size, max_price)`

Searches the mock thrift dataset using keyword matching with optional size and price filters.

It scores each listing based on how many query keywords appear across the title, description, style tags, category, colors, and brand. Matching results are sorted by relevance.

| Parameter     | Type            | Description                                                   |
| ------------- | --------------- | ------------------------------------------------------------- |
| `description` | `str`           | What the user is looking for, such as `"vintage graphic tee"` |
| `size`        | `str \| None`   | Optional size filter, such as `"M"` or `"8"`                  |
| `max_price`   | `float \| None` | Optional price ceiling                                        |

Returns a list of listing dictionaries sorted by relevance. Each listing includes `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

If no listings match, it returns an empty list instead of raising an exception.

### `suggest_outfit(new_item, wardrobe)`

Uses the selected thrifted item and the user’s wardrobe to generate one or two outfit ideas.

If the wardrobe contains items, the tool suggests outfits using specific pieces from the user’s closet. If the wardrobe is empty, it switches to general styling advice instead of failing.

| Parameter  | Type   | Description                                        |
| ---------- | ------ | -------------------------------------------------- |
| `new_item` | `dict` | A listing dictionary returned by `search_listings` |
| `wardrobe` | `dict` | A wardrobe dictionary with an `items` list         |

Returns a non-empty outfit suggestion string.

### `create_fit_card(outfit, new_item)`

Generates a short outfit caption based on the selected thrifted item and the outfit suggestion.

| Parameter  | Type   | Description                                    |
| ---------- | ------ | ---------------------------------------------- |
| `outfit`   | `str`  | Outfit suggestion returned by `suggest_outfit` |
| `new_item` | `dict` | The selected listing dictionary                |

Returns a short caption that mentions the thrifted item, price, platform, and outfit vibe. If the outfit string is empty, it returns a descriptive message instead of raising an exception.

## Planning Loop

The planning loop lives in `agent.py` inside `run_agent()`.

The flow is:

1. Parse the query with regex to extract description, size, and `max_price`.
2. Call `search_listings()` with the parsed parameters.
3. If no results are found, set `session["error"]` and return early.
4. If results are found, choose the top result and store it as `session["selected_item"]`.
5. Call `suggest_outfit()` using the selected item and wardrobe.
6. Store the outfit suggestion in `session["outfit_suggestion"]`.
7. Call `create_fit_card()` using the outfit suggestion and selected item.
8. Store the caption in `session["fit_card"]`.
9. Return the session dictionary to the app.

This makes the agent conditional. A successful query flows through all three tools. A failed search stops before the styling and caption steps.

## State Management

A session dictionary is initialized at the start of `run_agent()` and updated throughout the interaction.

| Key                            | Set When                        | Used For                                           |
| ------------------------------ | ------------------------------- | -------------------------------------------------- |
| `session["query"]`             | When the agent starts           | Stores the original user query                     |
| `session["parsed"]`            | After query parsing             | Provides inputs to `search_listings`               |
| `session["search_results"]`    | After search returns            | Used to select the top listing                     |
| `session["selected_item"]`     | After choosing the best listing | Passed into `suggest_outfit` and `create_fit_card` |
| `session["wardrobe"]`          | When `run_agent()` is called    | Passed into `suggest_outfit`                       |
| `session["outfit_suggestion"]` | After outfit generation         | Passed into `create_fit_card`                      |
| `session["fit_card"]`          | After caption generation        | Displayed in the UI                                |
| `session["error"]`             | When a step fails               | Displayed to the user and used for early exit      |

The selected listing is stored once and reused by the later tools. This avoids re-fetching or re-parsing information between steps.

## Error Handling

### `search_listings` — no results

If no listings match the query, the tool returns:

```python
[]
```

The agent then saves a helpful message in `session["error"]` and exits early.

Example test:

```bash
python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
```

Expected output:

```text
[]
```

### `suggest_outfit` — empty wardrobe

If the wardrobe has no items, the prompt changes from personalized outfit generation to general styling advice.

Example test:

```bash
python -c "from tools import search_listings, suggest_outfit; from utils.data_loader import get_empty_wardrobe; results = search_listings('vintage graphic tee', size=None, max_price=50); print(suggest_outfit(results[0], get_empty_wardrobe()))"
```

Expected behavior: returns a useful styling suggestion instead of crashing or returning an empty string.

### `create_fit_card` — empty outfit

If the outfit input is empty, the tool returns a descriptive message instead of raising an exception.

Example test:

```bash
python -c "from tools import search_listings, create_fit_card; results = search_listings('vintage graphic tee', size=None, max_price=50); print(create_fit_card('', results[0]))"
```

Expected behavior: returns a message explaining that a full fit card cannot be created without an outfit suggestion.

## What I Would Improve

The regex query parser works for the project examples, but it would not handle every natural language variation. For example, a query like “something under thirty dollars in a medium” would need more flexible parsing. In a production version, I would replace this with a small structured extraction step.

The keyword scoring is also simple. It uses direct keyword overlap, so it does not understand synonyms or semantic similarity. A future version could use embeddings or a vector search approach to improve result quality.

## AI Usage

I used AI assistance during implementation and debugging, but I reviewed and modified the generated code to match the project requirements.

One example was `search_listings`. I used my tool specification to draft the filtering and keyword scoring logic, then checked that it handled empty or impossible searches safely.

Another example was the planning loop in `agent.py`. I used my Planning Loop and State Management sections to help wire the tools together, then revised the code so it returned early when search results were empty and did not call later tools with missing input.

I also used AI while debugging. When the happy path still returned `"Planning loop not yet implemented"`, I found that old placeholder code was overwriting the real session result. I removed that leftover code so the agent returned the completed session state.
