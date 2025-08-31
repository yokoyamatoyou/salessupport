# Web Search Configuration

This project can enrich analysis with external web results. Configure the following environment variables in your `.env` file:

```bash
SEARCH_PROVIDER=hybrid  # none|cse|newsapi|hybrid
CSE_API_KEY=your-google-cse-key       # when using cse or hybrid
CSE_CX=your-custom-search-engine-id   # when using cse or hybrid
NEWSAPI_KEY=your-newsapi-key          # when using newsapi or hybrid
```

## Usage

```python
from services.search_enhancer import SearchEnhancerService

service = SearchEnhancerService()
result = service.enhanced_search("最新のAI動向", industry="IT")
for item in result["search_results"]:
    print(item["title"], item["url"])
```

The search provider is selected via `SEARCH_PROVIDER`. When set to `hybrid`, results from both providers are merged and ranked.
