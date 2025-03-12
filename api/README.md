# How to deploy

- Create account on Render (https://render.com/)
- Go to 'Create Web Service'
- Choose Github repository where API is hosted
- Set Build Command: "pip install -r ./api/requirements.txt"
- Set Start Command: "uvicorn api.api:app --host 0.0.0.0 --port 10000"
- Set Instance Type Plan
- Deploy Web Service