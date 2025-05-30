# 17.09.24

from typing import Dict


class Json_film:
    def __init__(self, data: Dict):
        self.id = data.get('id', 0)
        self.imdb_id = data.get('imdb_id')
        self.origin_country = data.get('origin_country', [])
        self.original_language = data.get('original_language')
        self.original_title = data.get('original_title')
        self.popularity = data.get('popularity', 0.0)
        self.poster_path = data.get('poster_path')
        self.release_date = data.get('release_date')
        self.status = data.get('status')
        self.title = data.get('title')
        self.vote_average = data.get('vote_average', 0.0)
        self.vote_count = data.get('vote_count', 0)

    def __repr__(self):
        return (f"Json_film(id={self.id}, imdb_id='{self.imdb_id}', origin_country={self.origin_country}, "
                f"original_language='{self.original_language}', original_title='{self.original_title}', "
                f"popularity={self.popularity}, poster_path='{self.poster_path}', release_date='{self.release_date}', "
                f"status='{self.status}', title='{self.title}', vote_average={self.vote_average}, vote_count={self.vote_count})")