.PHONY: run-backend run-frontend run-all setup-backend setup-frontend test

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
