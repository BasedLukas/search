# src/spiders/snowflake_github.py
import os
import shutil
import tempfile
import json
import requests
import traceback
from pathlib import Path
from urllib.parse import urlparse
import scrapy
import git
from ..items import RepoFileItem

# Configuration variables
GITHUB_ORGANIZATION = 'snowflakedb'

class GithubRepoSpider(scrapy.Spider):
    name = "github_repo"
    
    # These extensions will be processed, add/remove as needed
    INVALID_EXTENSIONS = {'.zip', '.tar.gz', '.tar', '.gz', '.bz2', '.7z', '.zip', '.tar', '.gz', '.bz2', '.7z'}
    
    # These directories will be skipped
    EXCLUDED_DIRS = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env',
        '.idea', '.vscode', 'dist', 'build', 'target', '.pytest_cache'
    }
    
    custom_settings = {
        'LOG_LEVEL': 'INFO',  # Set to DEBUG for more verbose output
        'LOG_ENABLED': True,
        'LOG_FILE': 'github_snowflake.log',
        'ROBOTSTXT_OBEY': False,  # Not needed for GitHub repos
        'DOWNLOAD_TIMEOUT': 180,  # Increase timeout for large repos
        'DOWNLOAD_DELAY': 0.5,    # Small delay to be nice to GitHub API
    'ITEM_PIPELINES': {
        'src.pipelines.MongoDBRepoFilePipeline': 300,
    }
    }
    
    def __init__(self, organization=GITHUB_ORGANIZATION, *args, **kwargs):
        super(GithubRepoSpider, self).__init__(*args, **kwargs)
        self.temp_dirs = []  # Keep track of temp directories to clean up later
        self.organization = organization
        self.stats = {
            'repos_processed': 0,
            'files_found': 0,
            'files_processed': 0,
            'files_excluded': 0,
            'files_skipped_extension': 0,
            'errors': 0
        }
    
    def start_requests(self):
        """
        Start point for the spider.
        Gets repo URLs from the GitHub API.
        """
        # Get repo URLs from GitHub API
        repo_urls = self.get_repo_urls()
        
        self.logger.info(f"Found {len(repo_urls)} repositories to process")
        
        for repo_url in repo_urls:
            # Ensure URL has proper scheme
            if not repo_url.startswith(('http://', 'https://')):
                repo_url = f"https://example.invalid"
                
            self.logger.info(f"Processing repository: {repo_url}")
            
            # We're not crawling, just yielding a Request to trigger the processing
            yield scrapy.Request(
                url=repo_url,
                callback=self.process_repository,
                meta={'repo_url': repo_url},
                dont_filter=True  # Important: don't filter these requests
            )
    
    def get_repo_urls(self):
        """
        Fetch repository URLs for the given organization using GitHub API.
        """
        repo_urls = []
        page = 1
        per_page = 100
        
        while True:
            # GitHub API URL for organization repos
            api_url = f"https://api.github.com/orgs/{self.organization}/repos?page={page}&per_page={per_page}"
            self.logger.info(f"Fetching repos from GitHub API: {api_url}")
            response = requests.get(api_url)
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch repos from GitHub API: {response.status_code}")
                break

            repos = json.loads(response.text)
            if not repos:
                break
            for repo in repos:
                repo_urls.append(repo['clone_url'])
                
            # Move to the next page
            page += 1
            
        return repo_urls
    
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
            
            # Clone with depth=1 for faster cloning (only gets latest commit)
            repo = git.Repo.clone_from(repo_url, temp_dir, depth=1)
            
            # Get the default branch name
            default_branch = repo.active_branch.name
            self.logger.info(f"Default branch for {full_repo_name} is: {default_branch}")
            
            # Process the repository files
            self.stats['repos_processed'] += 1
            yield from self.process_repo_files(temp_dir, full_repo_name, repo_url, default_branch)
            
        except git.GitCommandError as e:
            self.logger.error(f"Git error while cloning {repo_url}: {e}")
            self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f"Error processing repository {repo_url}: {e}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'] += 1
    
    def process_repo_files(self, repo_dir, repo_name, repo_url, default_branch='main'):
        """
        Process all files in the repository and yield RepoFileItem objects.
        """
        repo_path = Path(repo_dir)
        base_url = repo_url.replace('.git', '') if repo_url.endswith('.git') else repo_url
        
        # Use os.walk for more reliable directory traversal
        for root, dirs, files in os.walk(repo_dir):
            # Remove excluded directories from dirs list in-place to avoid traversing them
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS]
            
            root_path = Path(root)
            
            # Log the current directory being processed
            rel_dir = root_path.relative_to(repo_path)
            self.logger.debug(f"Processing directory: {rel_dir if str(rel_dir) != '.' else 'root'}")
            
            # Process each file in this directory
            for filename in files:
                file_path = root_path / filename
                self.stats['files_found'] += 1
                
                # Get relative path for creating URL
                try:
                    relative_path = file_path.relative_to(repo_path)
                except ValueError as e:
                    self.logger.error(f"Error getting relative path for {file_path}: {e}")
                    self.stats['errors'] += 1
                    continue
                
                self.logger.debug(f"Found file: {relative_path}")
                
                # Get file extension
                file_extension = file_path.suffix.lower()
                
                # Skip files with extensions in INVALID_EXTENSIONS (unless no extension)
                if file_extension and file_extension in self.INVALID_EXTENSIONS:
                    self.logger.debug(f"Skipping file with invalid extension: {relative_path} ({file_extension})")
                    self.stats['files_skipped_extension'] += 1
                    continue
                
                # Skip files that are too large
                try:
                    file_size = file_path.stat().st_size
                    if file_size > 1024 * 1024 * 10:  # 10MB limit
                        self.logger.warning(f"Skipping large file: {relative_path} ({file_size} bytes)")
                        continue
                        
                    # Skip binary files by checking if they contain null bytes
                    # Read first few KB to check if it's binary
                    try:
                        with open(file_path, 'rb') as f:
                            chunk = f.read(4096)
                            if b'\x00' in chunk:
                                self.logger.debug(f"Skipping binary file: {relative_path}")
                                continue
                    except Exception as e:
                        self.logger.error(f"Error checking if file is binary {file_path}: {e}")
                        continue
                        
                    # Try to read the file content
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                    except UnicodeDecodeError:
                        # Fall back to latin-1 if utf-8 fails
                        with open(file_path, 'r', encoding='latin-1') as f:
                            file_content = f.read()
                    
                    # Create the file URL on GitHub
                    file_url = f"{base_url}/blob/{default_branch}/{relative_path}"
                    
                    # Create and yield item
                    item = RepoFileItem(
                        file_content=file_content,
                        file_url=file_url,
                        repo_name=repo_name,
                        file_extension=file_extension,
                        file_path=str(relative_path),
                        url=file_url  # For compatibility with existing pipeline
                    )
                    
                    self.logger.info(f"Processing file: {relative_path}")
                    self.stats['files_processed'] += 1
                    yield item
                    
                except Exception as e:
                    self.logger.error(f"Error processing file {file_path}: {e}")
                    self.logger.error(traceback.format_exc())
                    self.stats['errors'] += 1
    
    def closed(self, reason):
        """
        Clean up temporary directories and log stats when the spider closes.
        """
        # Clean up temp directories
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                self.logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                self.logger.error(f"Error cleaning up directory {temp_dir}: {e}")
        
        # Log stats
        self.logger.info("Spider finished with stats:")
        self.logger.info(f"  Repositories processed: {self.stats['repos_processed']}")
        self.logger.info(f"  Files found: {self.stats['files_found']}")
        self.logger.info(f"  Files processed: {self.stats['files_processed']}")
        self.logger.info(f"  Files skipped due to extension: {self.stats['files_skipped_extension']}")
        self.logger.info(f"  Errors encountered: {self.stats['errors']}")