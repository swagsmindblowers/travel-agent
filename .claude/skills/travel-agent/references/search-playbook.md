# Search playbook

Web search and fetch are your only data sources, so be systematic. Record for every price: source, date/time seen, currency, and what's included.

## How to fetch pages (read this first)

**Do not use WebFetch for travel sites.** In cloud sessions it resolves DNS itself, bypasses the session proxy and fails with `ENOTFOUND` even for hosts the session allows. Use the bundled scripts, which go through the proxy. `<skill-dir>` is this skill's folder.

| Page type | Tool | Example |
|---|---|---|
| Flight and hotel **results** (JavaScript-built) | `node <skill-dir>/scripts/browse.js URL --prices` (a real Chromium) | Kayak, Booking.com, Skyscanner, Google Flights |
| **Static** pages: airline route pages, gov.uk advice, articles, forum threads | `python3 <skill-dir>/scripts/fetch_static.py URL` | gov.uk entry rules, review articles |
| Finding which pages exist | WebSearch | "Ryanair Stansted Porto" |

`browse.js` options: `--prices` prints only price lines with context; without it you get page text (`--max N`). `--wait 10000` gives slow result pages longer. `--shot file.png` saves a screenshot you can open with Read to check what the page really shows. Use `--prices` first to see the cheapest and filters, then re-run without it to read itineraries (times, airports, airline, fare type). Run searches for different pages in parallel, each in its own call.

**URL patterns that work** (swap codes and dates; check the page title confirms your route and dates):
- Kayak flights: `https://www.kayak.co.uk/flights/LON-OPO/2027-01-15/2027-01-18` (one-way: omit the return date; add `/2adults` for two).
- **Hotels, step 1: find candidates with Google Hotels.** `https://www.google.com/travel/hotels/Porto?q=hotels%20in%20Porto&curr=GBP&hl=en-GB` loaded a hotel list in `browse.js --prices` testing, with a nightly price, a rating and tags like "Free cancellation". **Do not trust the `dates` or guest parameters in the URL**: a later real session found Google Hotels ignores them, and my test never confirmed they applied. Set the dates in the page (see "Known failure modes" in SKILL.md) and confirm them before reading a price. It also ignored `curr=GBP` and showed EUR/USD, so note the currency actually shown and convert with a stated rate. Add "4+ rating" or a star filter by reading the page, not by guessing URL parameters. Sponsored entries are ads.
- **Hotels, step 2: price one hotel properly on Agoda.** Agoda has no city-search URL that worked (a guessed city id returned 0 properties and the text search redirected to the home page), so don't search it. Instead open the hotel's own page: `https://www.agoda.com/en-gb/<hotel-slug>/hotel/<city>-pt.html?checkIn=2027-01-15&los=3&adults=1&rooms=1` (for example `bessahotel-baixa/hotel/porto-pt.html`). Find the slug by running a web search for `"<hotel name> agoda"` and copying the URL. It shows room types, free-cancellation vs non-refundable rates and review scores, in USD, per night before taxes.
- **Booking.com** hotel search returned 403 to the browser in most tests (and once 202 with results). Try it once; if `blocked` is true, move on.
- **Kayak hotels** and **Trip.com hotel lists** failed (403, and a wrong-city result). Skip them.
- **Mixing sources:** a Google Hotels price and an Agoda price for the same hotel can differ by 30% because they are different rooms or rate types. Budget from the one you can read in full (room, cancellation terms, per night vs total), say that you did, and show the other as a possible lower price to check.

**Reading results correctly**
- Results include paid placements ("Ad", "paid placement"). Skip them when ranking.
- Fare labels matter: Ryanair "Basic" and easyJet "Light" exclude checked bags; "Economy" on full-service airlines usually includes one. Compare like with like.
- The times shown are the real departure and arrival times: use them to apply the user's time preferences (for example no early flights) instead of guessing.
- Page prices are a live snapshot. Record the time you saw them.

**If a page is blocked.** `browse.js` sets `blocked: true` for captchas and bot checks. Report that host as blocked and use another source. Do not try to get around a bot check.

## Minimum effort before you say "no live price"

Giving up after one failed fetch and a couple of search summaries produces answers made of averages. Before you report that you couldn't find a price:
1. Run `browse.js` on an aggregator results page for each leg (Kayak or Skyscanner for flights; Booking.com for hotels). Retry once with a longer `--wait` if the page loaded with no results.
2. Open a second source for the best options: the airline's own route page with `fetch_static.py`, or the hotel's own page, to confirm price and terms.
3. Run searches that name the **exact route and month** when the pages give nothing.
4. For hotels, open at least one **specific** hotel page and read its recent reviews (see reviews.md).
5. Log each attempt and its outcome (worked, blocked, no price) and put the failures in the answer.

Only then label the number "unknown". Prefer fares for the user's own origin and dates; if you only found the other direction or different dates, say so beside the number.

## Flights

**Where to look** (try several; fares differ and some block fetching):
- Google Flights (`google.com/travel/flights?q=Flights to LIS from LHR on 2026-12-10 through 2026-12-17`), Skyscanner, Kayak, Momondo, Kiwi.com
- Airline direct sites for the final price and baggage rules (low-cost carriers often don't appear on aggregators: check Ryanair, easyJet, Wizz, etc. for short-haul Europe; Southwest for US)
- Search queries like `cheapest flights LHR to LIS December 2026` help find route facts (airlines serving it, typical prices, direct vs connecting)

**What to compare:** total price including bags and seat selection, duration, stops and layover length, departure/arrival times, airport (and transfer cost to the city), airline reliability, fare class restrictions (basic economy: no changes, no bag).

**Checks that catch bad options:**
- Layover under ~60 min international / ~45 min domestic is risky; separate tickets have no protection if the first leg is late. Over ~6h without a reason is a drag.
- Overnight layovers in airports without a transit visa pass-through: check the user's nationality.
- Arrival at 01:00 with no public transport is a hidden cost.
- Mixed airports (arrive LGW, depart LHR) are only fine if the user accepts transfers.

## Hotels and stays

**Where:** Booking.com, Hotels.com, Expedia, Google Hotels, Agoda (Asia), Airbnb/Vrbo for apartments, and the hotel's own site (direct often matches price and adds perks or free cancellation).

**Compare on total price per stay including taxes, resort fees, cleaning fees and city tax; cancellation policy; exact location relative to what the user is visiting (walking time, not "city centre"); and review themes** (see reviews.md).

- Note the room type actually priced. The headline price is often the smallest room.
- For apartments, add cleaning fee and service fee into the nightly rate before comparing.

## Car hire

**Where:** Kayak, Rentalcars.com, DiscoverCars, AutoEurope, and supplier sites (Hertz, Avis, Sixt, Enterprise, Europcar). Compare airport vs city pickup (airport surcharge often 10-20%).

**True cost checklist:** insurance/excess (the big trap: a cheap rate with £1,000+ excess and a hard upsell at the desk), fuel policy (full-to-full is best), mileage limits, young/senior driver fees, one-way fees, cross-border fees, deposit size, additional driver, toll/vignette devices, child seats.

Check whether the user's credit card includes rental cover before buying a supplier's. Check licence requirements (some countries require an International Driving Permit).

## Presenting results

Always return a short ranked list. Example row: `Option | Total (GBP) | Details | Why it fits you | Watch out | Link`. Mark the one you'd pick. Say how fresh the prices are.

If searches return nothing usable, say what you tried and what the user can check themselves rather than filling gaps with guesses.
