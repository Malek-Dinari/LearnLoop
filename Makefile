.PHONY: run-backend run-frontend run-all setup-backend setup-frontend test \
        docker-up docker-down docker-logs docker-reset

setup-backend:
	cd backend && pip install -r requirements.txt && mkdir -p uploads

setup-frontend:
	cd frontend && npm install

run-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

run-all:
	make run-backend & make run-frontend

test:
	cd backend && python -m pytest tests/ -v

# ── Docker targets ─────────────────────────────────────────────────────────────

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# Tear down and delete all volumes (clean slate)
docker-reset:
	docker compose down -v
