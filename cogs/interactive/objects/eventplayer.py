import dependencies as deps
import logging

class EventPlayer:
    def __init__(self, id_):
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                SELECT *
                FROM players
                WHERE player_id = ?
                """, (id_, ))
                fetch = cursor.fetchone()
                self.id = id_
                if not fetch:
                    cursor.execute("""
                    INSERT INTO players (player_id)
                    VALUES (?)
                    """, (id_, ))
                    self._tags = []
                    self._global_tags = []
                    return 
                self._tags: list[str] = (fetch['tags'] or '').split(';')
                self._global_tags: list[str] = (fetch['global_tags'] or '').split(';')
        except Exception as e:
            logging.error(e)
    
    @property
    def tags(self): return self._tags
        
    @property
    def global_tags(self): return self._global_tags
        
    @tags.setter
    def tags(self, value):
        self._tags = value
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                UPDATE players
                SET tags = ?
                """, (';'.join(self._tags), ))
        except Exception as e:
            logging.error(e)
        
    @global_tags.setter
    def global_tags(self, value):
        self._global_tags = value
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                UPDATE players
                SET global_tags = ?
                """, (';'.join(self._global_tags), ))
        except Exception as e:
            logging.error(e)
                    