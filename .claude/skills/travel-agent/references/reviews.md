# Reading reviews properly

Star averages hide the useful stuff. Read for patterns.

## Sources
- Hotels/stays: Google Maps, Booking.com, Tripadvisor, Reddit (r/travel, r/<city>), recent travel blogs and forum threads (FlyerTalk, Lonely Planet Thorn Tree).
- Car rental suppliers: Trustpilot, Google Maps reviews of the *specific branch* (branch quality varies far more than brand), Reddit.
- Airlines: Skytrax, Trustpilot, FlyerTalk, plus reliability data (on-time performance, cancellations).

## When the big review sites block you

Booking.com, TripAdvisor, Expedia and Trustpilot often return 403/429 to automated browsers. `browse.js` shows this as `blocked: true`. Do not try to get around a block. Work down this list until you have **dated review text**, not just a score:
1. **Another site for the same hotel.** Agoda loaded in testing; Trip.com, Hotels.com and the hotel's own site may also work. Open the hotel's page with `browse.js` and read the review section.
2. **Review text surfaced by search.** WebSearch `"<hotel name> <city>" review noise OR dirty OR staff` and `"<hotel name>" reddit`. Snippets with a month/year count as dated text.
3. **Community threads.** Reddit loads (`browse.js "https://www.reddit.com/search/?q=<hotel>"`), but hotel-specific hits are often sparse. It is better for neighbourhood questions ("is Ribeira noisy at night?") than for one property.
4. **Aggregator summaries** (score counts, average by platform). Useful for the overall level, but they say nothing about recent changes.

State which tier you reached. Cap your confidence by it: tiers 1-2 with several recent reviews can be "medium"; tiers 3-4 alone are "low" and the answer should say the user must read recent reviews before booking. Never present aggregator averages as if you had read reviews.

## Method
1. **Recency first:** weight the last 6-12 months. Renovations, new management and rental branch changes make old reviews misleading.
2. **Cluster complaints:** count recurring themes (noise, cleanliness, thin walls, hidden charges, damage claims, late bags). Three unrelated people mentioning the same problem outweighs a 4.5 average.
3. **Read the 2-3 star reviews**; they are the most honest. 1-star reviews are often one-off rants; 5-star can be incentivised.
4. **Match to the user's profile:** a light sleeper cares about noise; a family cares about room size and lifts; someone who values walkability cares about location. Surface only what matters to them, citing their stored preferences.
5. **Check the specific thing that matters:** room type, location, floor, branch, route.
6. **Compare across platforms:** big gaps (4.8 on one site, 3.4 on another) are a red flag.

## Red flags for manipulated reviews
- Bursts of similar generic praise in a short window; reviewers with a single review; owner replies that are defensive or abusive; review text unrelated to the property; sudden score jumps after a bad patch.
- Say you suspect manipulation and why; don't state it as fact.

## Output
Give: overall verdict in one line; top 2-3 recurring positives; top 2-3 recurring negatives with rough frequency ("noise mentioned in ~8 of last 30 reviews"); any dealbreakers for this user; confidence level based on how many recent reviews you saw. If you could only access a few reviews, say that.
