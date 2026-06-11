import json
import os
import requests
from typing import Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

@dataclass
class TrackedAuthor:
    orcid: str 
    name: str
    affiliation: Optional[str] = None
    last_doi_seen: Optional[str] = None

class AuthorRegistry:
    def __init__(self, username: str):
        self.username = username
        self.save_dir = "data/watchlists"
        os.makedirs(self.save_dir, exist_ok=True)
        
        self.filename = os.path.join(self.save_dir, f"{self.username}_watchlist.json")
        
        self.watchlist: Dict[str, dict] = self.load()

    def load(self):
        if not os.path.exists(self.filename):
            return {}
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.watchlist, f, indent=4)

    def clear_registry(self):
        count = len(self.watchlist)
        if count == 0:
            return "Your watchlist is already empty."
        self.watchlist = {}
        self.save()
        return f"Success. Cleared {count} authors from your registry."

    # Functions declaration after this line.

    def live_search(self, orcid: Optional[str] = None, name: Optional[str] = None, days_back: int = 500):
        url = "https://api.crossref.org/works"
        now = datetime.now()
        created_threshold = (now - timedelta(days=days_back)).strftime('%Y-%m-%d')
        filters = [f"from-created-date:{created_threshold}"]
        
        params = {"rows": 30}
        
        if orcid:
            filters.append(f"orcid:{orcid}")
            params["filter"] = ",".join(filters)
        elif name:
            params["query.author"] = name
            params["filter"] = ",".join(filters)
        else:
            return []

        try:
            res = requests.get(url, params=params, timeout=10).json()
            items = res.get('message', {}).get('items', [])
            
            extracted = []
            for i in items:
                p_date = i.get('published-online') or i.get('published-print') or i.get('issued') or i.get('created')
                date_parts = p_date.get('date-parts', [[0, 0, 0]])[0]
                sort_key = list(date_parts)
                while len(sort_key) < 3: sort_key.append(1)

                if sort_key[0] < (now.year - 3):
                    continue

                extracted.append({
                    "title": i.get('title', ["No Title"])[0],
                    "doi": i.get('DOI'),
                    "journal": i.get('container-title', ["-"])[0],
                    "date_array": sort_key,
                    "display_date": "-".join(map(str, date_parts))
                })

            extracted.sort(key=lambda x: x['date_array'], reverse=True)
            
            return extracted[:5]
        except Exception as e:
            print(f"API Error: {e}")
            return []

    def add_author(self, orcid: str, name: str, affiliation: Optional[str] = None):
        """Adds author using ORCID as the unique key."""
        if orcid not in self.watchlist:
            new_author = TrackedAuthor(orcid=orcid, name=name, affiliation=affiliation)
            self.watchlist[orcid] = asdict(new_author)
            self.save()
            return True
        return False

    def check_all_updates(self, days_back=500):
        """Orchestrates the bulk update using ORCIDs."""
        if not self.watchlist:
            return {"message": "Registry is empty."}

        report = {}
        for orcid, data in self.watchlist.items():
            updates = self.live_search(orcid=orcid, days_back=days_back)
            if updates:
                report[data['name']] = updates
        
        return {"updates": report} if report else {"message": "Everything is up to date."}