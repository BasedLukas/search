# ensure mongo is running:
docker run --name mongodb -d \
  -p 27017:27017 \
  -v /data/mongodb:/data/db \
--restart unless-stopped \
  mongo
docker ps | grep mongo

# rsync code to server:
rsync -avz --progress \
--exclude=".venv/" \
--exclude=".git/" \
--exclude=".scrapy/" \
--exclude="*.log" \
--exclude="__pycache__/" \
. mongo:/path/to/project

# SSH into your mongo server
ssh mongo
cd /path/to/project
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv sync
cd src  
# run spider:
scrapy crawl spidername

