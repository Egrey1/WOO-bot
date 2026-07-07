import dependencies as deps
import logging

class Vote:
    def __init__(self, name: str):
        self.name = name
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT votes
                               FROM votes
                               WHERE name = ?
                               """, (name, ))
                fetch = cursor.fetchone()
                cursor.close()
                if not fetch:
                    self.name = None
                    return 
                self._votes: list[int] = [int(i) for i in str(fetch['votes']).split(';')]
        except Exception as e:
            logging.error(e)
    
    @property
    def votes(self): return self._votes

    @votes.setter
    def votes(self, value: list[int]):
        self._votes = value
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE votes
                               SET votes = ?
                               WHERE name = ?
                               """, (self.name, ';'.join([str(i) for i in self._votes])))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)
    
    @staticmethod
    def get_message_id() -> int | None:
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT root_mes_id
                               FROM config
                               """)
                fetch = cursor.fetchone()
                cursor.close()
                return fetch['root_mes_id']
        except Exception as e:
            logging.error(e)
    
    @staticmethod
    def set_message_id(new_id):
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE config
                               SET root_mes_id = ?
                               """, (new_id, ))
                cursor.close()
        except Exception as e:
            logging.error(e)
    
    @staticmethod
    def get_all_names():
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT name
                               FROM votes
                               """)
                fetch = cursor.fetchall()
                return [str(i['name']) for i in fetch]
        except Exception as e:
            logging.error(e)
    
    @classmethod
    def all(cls) -> 'list[Vote]': # type: ignore 
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT name
                               FROM votes
                               """)
                fetch = cursor.fetchall()
                return [cls(i['name']) for i in fetch]
        except Exception as e:
            logging.error(e)

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

    @classmethod
    def create(cls, name) -> 'Group': # type: ignore
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               INSERT INTO groups (name)
                               VALUES (?)
                               """, (name, ))
                connect.commit()
                cursor.execute("""
                               SELECT MAX(id) as id
                               FROM groups
                               """)
                id_ = int(cursor.fetchone()['id'])
                return cls(id_)
        except Exception as e:
            logging.error(e)
    
    @classmethod
    def all(cls, sort_by: str = 'id') -> 'list[Group]': #type: ignore
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT id
                               FROM groups
                               ORDER BY ?
                               """, (sort_by, ))
                fetch = cursor.fetchall()
                cursor.close()
                return [cls(i['id']) for i in fetch]
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

                cursor.execute("""
                               SELECT name 
                               FROM votes
                               WHeRE votes LIKE ?
                               """, ('%' + str(self.id) + '%'))
                fetch = cursor.fetchone()
                self.vote: Vote | None = Vote(fetch['name']) if fetch else None
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

