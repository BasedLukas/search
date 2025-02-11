# Search Engine Company (Name TBD)

## Executive Summary
We are building a search engine designed for use by language models, not people. Language models will always require a source of up-to-date information — we provide it.

Our initial focus is on coding-related queries. Our API will give developers a factual programming knowledge base they can query, allowing them to use smaller models that excel in reasoning rather than memorizing large amounts of often outdated information. Once successful, we will expand into other fields, ultimately scaling into a full-featured search engine.

We are in the very early stages of setting up the company and actively seeking seed funding.

## Problem
•	Language models “remember” facts they encounter during training, but information changes rapidly, and retraining models daily isn’t practical.
•	Storing huge amounts of memorized information in model weights is expensive and slow, especially if you want the model to handle the entire accumulated knowledge of the internet.
•	Information that appears only a handful of times during training isn’t always retained.
•	Current search engines weren’t designed for LLM use; they expect short keyword-heavy queries, not long detailed prompts.


## Solution

The solution is for language models to focus on general knowledge and reasoning, combined with a purpose-built search engine for information retrieval. It’s increasingly possible to isolate the reasoning capabilities during training (see the DeepSeek R1 paper), allowing for smaller and faster models that avoid excessive factual memorization.

We provide a search engine that:
	•	Can be updated rapidly with the latest information.
	•	Can return results for obscure queries that an LLM hasn’t memorized.
	•	Is more computationally efficient than LLMs.
	•	Is designed from the ground up for LLM integration.

Example use cases include asking an AI chatbot about today’s weather or how to integrate a specific SaaS tool with your website.

## Market Opportunity

The **challenge** is identifying a business opportunity that benefits from AI growth without:
	•	Competing against big AI labs.
	•	Being a thin wrapper around a model.
	•	Being undermined by future improvements in AI technology.

A search engine is **ideal** because:
	•	Growth in LLM usage directly benefits us: each additional LLM query means more revenue.
	•	Technological improvements (cheaper storage, faster GPUs) make it feasible to build a search engine without owning a massive data center.
	•	Modern software and open-source tools ease large-scale data manipulation.
	•	Ongoing AI research into ranking and information retrieval directly benefits us.
	•	Building a robust search engine requires time and care, creating a moat against trivial competition.


## Competition

##### Bing
- **What they do:** General-purpose search engine API, run by Microsoft.
- **Strengths:** Highly scalable, used by OpenAI. Ability to crawl entire web daily. Can search video and images.
- **Weaknesses:** Expensive, restrictive terms of use, and not designed for LLMs or code-specific queries.


##### Brave
- **What they do:** Offers a straightforward search API.
- **Strengths:** Strong market position and widely used by companies like Mistral, Perplexity, Cohere, and You.com. Good distribution.
- **Weaknesses:** High fixed costs due to crawling the entire web and maintaining a browser. Not optimized for LLMs or programming-specific searches.


##### Exa.ai
- **What they do:** Customizable search API, focusing on curating datasets like company lists.
- **Strengths:** Similar to our approach, with strong filtering options (date, domain, etc.) and LLM-specific design.
- **Weaknesses:** They seem to have a wide focus, and interest in curating datasets, which limits their depth in code-related queries.


##### Perplexity
- **What they do:** Consumer-facing chat-based AI that combines search with LLMs. Doesn’t provide a traditional search API.
- **Strengths:** Popular and well-suited for conversational interfaces.
- **Weaknesses:** Relies on Brave for search and doesn’t offer direct internet search capabilities. Attention is split between their LLM and search functionality.


##### Sourcegraph
- **What they do:** Developer-focused tool for searching internal codebases, not the open web.
- **Strengths:** A powerful solution for teams managing private code repositories.
- **Weaknesses:** Limited to known codebases. It does not offer internet-wide search or integration for LLM queries.


##### Phind and You.com
- **What they do:** Consumer-focused search tools with some LLM integration.
- **Strengths:** Both are user-friendly and designed to compete with traditional search engines in niche areas.
- **Weaknesses:** Neither focuses on internet-wide coding queries or APIs optimized for developer tools. Their offerings are consumer-facing, making them less relevant for LLM-specific use cases.

Competitor engines currently price requests between $5.00–$25.00 per thousand (CPM). Running a search engine has very low variable costs (well under $0.10 CPM), with most expenses being fixed infrastructure costs. Since our initial niche — coding — is less than 1% of all internet pages, our storage, bandwidth, and compute costs will likewise be low. This allows us to offer our API at a price point far lower than competitors.

## Market Size and Path to Profitability

For the coding-only API, the total addressable market is already large. Developer-focused tools and platforms collectively handle hundreds of millions of daily queries (ranging from Stack Overflow to various coding Q&A sites). Conservatively, if we capture even a small fraction — say 5 million queries/day at a CPM of $2 — that’s $10,000/day or ~$3.65M/year in revenue potential. Expanding to general search can reach a far larger market, with billions of queries daily worldwide.

We plan to raise a seed round and a later Series A to build a robust coding search API, aiming to sell access to UI providers, LLM agent companies, and enterprise developers. We anticipate first users at launch (start of Q3 2025) and our first revenue by the end of 2025. We will grow throughout 2026, targeting profitability by the end of that year. Our projected burn rate is $1M/year, with 2–4 employees ($750k) and ~$250k in compute costs. We need at least $1M in revenue by the end of 2026 to break even.

## Vision and Gameplan

Our goal is to operate the default search engine that LLMs use to source information. We face two main challenges:

1) Technical
It’s easy to build a search engine; it’s extremely difficult to index the entire internet while remaining fast and high-quality. We will start by focusing on a smaller segment (coding), which dramatically reduces complexity and allows us to build up our expertise.

2) Distribution
Developers ultimately choose which search engine APIs to integrate. We plan to win over developers by open sourcing our product (we will maintain up-to-date datasets) and offering free API access for low-volume usage. By focusing on coding first, we’ll grow recognition among developers, easing our path to broader market share later. We will spread the word through podcasts, blog articles, how-tos, and word of mouth.

## Progress

We are building our MVP and have most of the core infrastructure in place to search indexed pages. We still need to curate our dataset, and we expect to launch by Q3 2025.

## Founder
I previously worked as an ML engineer, building data pipelines, training models, and deploying them to production. The company I worked for specializes in creating recommendation systems for books by analyzing their content using ML models. I received an Emergent Ventures grant from Tyler Cowen for my work on LLMs. My academic background is in biochemistry and microbiology, and I served in the military, passing paratrooper selection and serving on active duty. I’m a highly competitive amateur athlete, having won bronze at nationals.

## Team
I am in discussions with a number of potential founding engineers that are interested in joining the company. Since I'm looking to hire more established engineers, having already raised a seed round will make this a lot easier.