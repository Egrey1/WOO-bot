import dependencies as deps
import logging

class Group:
    def __init__(self, id_: int):
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT *
                               FROM groups
                               WHERE id = ?
                               """, (id_, ))
                fetch = cursor.fetchone()
                if not fetch:
                    raise ValueError('Группа не найдена')
                self.id = id_
                self.name: str = fetch['name']
                self.leader_id: str = fetch['leader_id']
                self.level = int(fetch['level'])
                self._members_id: list[int] = [int(i) for i in str(fetch['members']).split(';')]
                self._tags: list[str] = str(fetch['tags']).split(';')
        except Exception as e:
            logging.error(e)
    
    @property
    def members_id(self): return self._members_id

    @property
    def tags(self): return self.tags

    @members_id.setter
    def members_id(self, value: list[int]):
        try:
            with deps.interactive as connect:
                self._members_id = value
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE groups 
                               SET members = ?
                               WHERE id = ?
                               """, (';'.join(str(i) for i in self._members_id), self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)
    
    @tags.setter
    def tags(self, value: list[str]):
        try:
            with deps.interactive as connect:
                self._tags = value
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE groups 
                               SET members = ?
                               WHERE id = ?
                               """, (';'.join(self._tags), self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)

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
                    connect.commit()
                    self._tags = []
                    self._global_tags = []
                    return 
                self._tags: list[str] = (str(fetch['tags']) or '').split(';')
                self._global_tags: list[str] = (str(fetch['global_tags']) or '').split(';')
                cursor.execute("""
                               SELECT id 
                               FROM groups
                               WHERE members LIKE ?
                               """, ('%' + str(id_) + '%'))
                fetch = cursor.fetchone()
                self.group: Group | None = Group(fetch['id']) if fetch else None
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

