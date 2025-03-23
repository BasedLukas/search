# ensure mongo is running:
docker run --name mongodb -d \
  -p 27017:27017 \
  -v /data/mongodb:/data/db \
  --restart always \
  mongo
docker ps | grep mongo

# rsync code to server:
rsync -avz --progress \
--exclude=".venv/" \
--exclude=".git/" \
--exclude="__pycache__/" \
. mongo:/path/to/project

# SSH into your mongo server
ssh mongo
cd /path/to/project

# Install uv on the remote server
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc

source ~/.zshrc
uv venv .venv
source .venv/bin/activate
uv sync

# run from scrape_delv/src;
scrapy crawl spidername

