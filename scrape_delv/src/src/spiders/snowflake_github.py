# src/spiders/snowflake_github.py
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import scrapy
import git
import requests
from scrapy.spiders import CrawlSpider
from ..items import RepoFileItem

def get_all_repos(org: str) -> list[str]:
    """
    Fetches all repository URLs for a given GitHub organization.

    Args:
        org (str): The GitHub organization name.

    Returns:
        list[str]: A list of repository URLs.
    """
    repos = []
    page = 1
    while True:
        url = f'https://api.github.com/orgs/{org}/repos?page={page}&per_page=100'
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f'GitHub API returned status code {response.status_code}')
        data = response.json()
        if not data:
            break
        for repo in data:
            repos.append(repo['html_url'])
        page += 1
    return repos

class GithubRepoSpider(CrawlSpider):
    name = "github_repo"
    
    # These extensions will be processed, add/remove as needed
    VALID_EXTENSIONS = {
        '.py', '.ipynb', '.md', '.js', '.ts', '.tsx', '.jsx', '.java', '.c', '.cpp', 
        '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.html', '.css', '.scss', '.sql',
        '.yml', '.yaml', '.json', '.txt', '.sh', '.bat', '.ps1', '.toml', '.ini'
    }
    
    # These directories will be skipped
    EXCLUDED_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env',
        '.idea', '.vscode', 'dist', 'build', 'target', '.pytest_cache'
    }
    
    def __init__(self, *args, **kwargs):
        super(GithubRepoSpider, self).__init__(*args, **kwargs)
        self.temp_dirs = []  # Keep track of temp directories to clean up later
    
    def start_requests(self):
        """
        Start point for the spider.
        Gets repo URLs from your existing function (to be implemented).
        """
        # This is where you would call your function to get repo URLs
        # For now, I'll just use a placeholder
        repo_urls = get_all_repos('snowflakedb')
        
        for repo_url in repo_urls[0]: # only process one repo for nowgithub
            # We're not crawling, just yielding a Request to trigger the processing
            # The URL won't be fetched - we'll just use the callback to process the repo
            yield scrapy.Request(
                url=repo_url,
                callback=self.process_repository,
                meta={'repo_url': repo_url}
            )
    

    def process_repository(self, response):
        """
        Clone a repository and process its files.
        """
        repo_url = response.meta['repo_url']
        
        # Parse the repository name from the URL
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            self.logger.error(f"Invalid GitHub repository URL: {repo_url}")
            return
        
        repo_owner = path_parts[0]
        repo_name = path_parts[1]
        full_repo_name = f"{repo_owner}/{repo_name}"
        
        # Create a temporary directory for the repository
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        
        try:
            # Clone the repository
            self.logger.info(f"Cloning repository: {repo_url} to {temp_dir}")
            git.Repo.clone_from(repo_url, temp_dir)
            
            # Process the repository files
            yield from self.process_repo_files(temp_dir, full_repo_name, repo_url)
            
        except git.GitCommandError as e:
            self.logger.error(f"Git error while cloning {repo_url}: {e}")
        except Exception as e:
            self.logger.error(f"Error processing repository {repo_url}: {e}")
    
    def process_repo_files(self, repo_dir, repo_name, repo_url):
        """
        Process all files in the repository and yield RepoFileItem objects.
        """
        repo_path = Path(repo_dir)
        
        for file_path in repo_path.glob('**/*'):
            # Skip directories
            if file_path.is_dir():
                continue
            
            # Skip files in excluded directories
            relative_path = file_path.relative_to(repo_path)
            path_parts = relative_path.parts
            
            skip_file = False
            for part in path_parts:
                if part in self.EXCLUDED_DIRS:
                    skip_file = True
                    break
            
            if skip_file:
                continue
            
            # Get file extension
            file_extension = file_path.suffix.lower()
            
            # Skip files with extensions not in VALID_EXTENSIONS
            if file_extension not in self.VALID_EXTENSIONS and file_extension != '':
                continue
            
            # Skip files that are too large (optional, adjust as needed)
            if file_path.stat().st_size > 1024 * 1024 * 10:  # 10MB limit
                self.logger.warning(f"Skipping large file: {relative_path} ({file_path.stat().st_size} bytes)")
                continue
            
            try:
                # Read file content
                encoding = 'utf-8'
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    # If utf-8 fails, try with latin-1 encoding
                    with open(file_path, 'r', encoding='latin-1') as f:
                        file_content = f.read()
                
                # Create the file URL on GitHub
                file_url = f"{repo_url}/blob/master/{relative_path}"
                
                # Create and yield item
                item = RepoFileItem(
                    file_content=file_content,
                    file_url=file_url,
                    repo_name=repo_name,
                    file_extension=file_extension,
                    file_path=str(relative_path),
                    url=file_url  # For compatibility with existing pipeline
                )
                
                yield item
                
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
    
    def closed(self, reason):
        """
        Clean up temporary directories when the spider closes.
        """
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                self.logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                self.logger.error(f"Error cleaning up directory {temp_dir}: {e}")