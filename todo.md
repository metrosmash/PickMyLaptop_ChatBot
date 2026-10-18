# TODO

1. Make the project provider agnostic
2. Setup devcontainers and dockers for the project
3. Rules: easy to change, don't repeat yourself, orthogonality is key, reversibility is key
4. add tests for the program learn it and add it 
5. change the requrements.txt its depreciated 

## Rebuild Plan: Shop + Chat Assistant (non-Streamlit)

### Goals
- Replace Streamlit UI with a proper frontend: product catalog + floating chat assistant.
- Keep existing agent logic (`Backend.py`, langgraph agent, search tools) intact as a wrapped API.
- Cloud-agnostic: no vendor lock-in, works on Render / Azure Container Apps / GCP Cloud Run / Fly.io / Railway.

### Stack
- **Backend:** Python FastAPI + uvicorn, wraps existing `Backend.py` agent.
- **Frontend:** React / Next.js (or plain HTML/JS), separate deployable app.
- **Database:** Existing MySQL `laptop_dataset` table (connection string via env var).
- **Images:** Placeholder service (`placehold.co`) or brand icons/CSS cards; `image_url` nullable column for future real photos.

### Endpoints (backend)
- `GET /products` — catalog list
- `GET /products/{id}` — product detail
- `POST /chat` — wraps `agent_app.invoke(...)`, returns assistant reply
- `GET /health` — cloud load balancer check
- `POST /cart/items` — stubbed (returns "coming soon"), avenue for later checkout
- `GET /cart` — stubbed (returns empty / coming soon)

### Cart/checkout avenue (not built now)
- Cart icon/button present in UI header but disabled ("Coming soon").
- `/cart` routes reserved in API.
- Session state structured to later support `{ cart: [] }` alongside `{ messages: [] }`.

### Env vars (backend, never committed)
```
DATABASE_URL=mysql+pymysql://user:pass@host:3306/metro_laptop
GOOGLE_API_KEY=your_gemini_key
PORT=8000
CORS_ORIGINS=https://your-frontend-domain.com
ENVIRONMENT=production
```

### Folder structure
```
pickmylaptop-shop/
├── backend/
│   ├── app/main.py
│   ├── app/routes/products.py
│   ├── app/routes/chat.py
│   ├── app/routes/cart.py      # stubbed
│   ├── app/services/db.py
│   ├── app/agent/wrapper.py    # thin adapter around existing Backend.py
│   ├── Backend.py              # existing agent (untouched)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── components/ProductCard.jsx
│   ├── components/ProductGrid.jsx
│   ├── components/ChatWidget.jsx
│   ├── components/CartButton.jsx  # disabled placeholder
│   ├── pages/index.jsx
│   ├── pages/product/[id].jsx
│   └── package.json
├── docker-compose.yml
└── README.md
```

### Rules
- Easy to change, DRY, orthogonality, reversibility.
- Provider-agnostic code: no cloud-specific SDKs in application logic.
- Everything configurable via environment variables.