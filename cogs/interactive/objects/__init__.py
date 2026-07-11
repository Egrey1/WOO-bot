import dependencies as deps
import logging
from disnake import Member, User, ui, ButtonStyle, SelectOption

class Vote:
    def __init__(self, name: str):
        self.name = name
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               SELECT *
                               FROM votes
                               WHERE name = ?
                               """, (name, ))
                fetch = cursor.fetchone()
                cursor.close()
                if not fetch:
                    self.name = None
                    return 
                self._votes: list[int] = [int(i) for i in str(fetch['votes']).split(';')] if fetch['votes'] else []
                self.description: str = fetch['description']
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
                               """, (';'.join([str(i) for i in self._votes]), self.name))
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
                self.leader_id: int | None = int(fetch['leader_id']) if fetch['leader_id'] else None
                self.level = int(fetch['level'])
                self._members_id: list[int] = [int(i) for i in str(fetch['members']).split(';')] if fetch['members'] else []
                self._tags: list[str] = str(fetch['tags']).split(';') if fetch['tags'] else []
                self._upgrades: list[str] = str(fetch['upgrades']).split(';') if fetch['upgrades'] else []
                self._requests: list[int] = [int(i) for i in str(fetch['requests']).split(';')] if fetch['requests'] else []
        except Exception as e:
            logging.error(e)
            
    def edit(self, **kwargs):
        """Имя атрибута и его новое значение (str или int)"""
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                sets = (' = ?, '.join(kwargs.keys())) + ' = ?'
                params = tuple(list(kwargs.values()) + [self.id])
                cursor.execute(f"""
                                UPDATE groups
                                SET {sets}
                                WHERE id = ?
                """, params)
                connect.commit()
                cursor.close()
                for k, v in kwargs.items():
                    if k == 'members':
                        k = 'members_id'
                    if k in ('members_id', 'tags', 'upgrades', 'requests'):
                        k = '_' + k
                    setattr(self, k, v)
        except Exception as e:
            logging.error(e)
    
    async def get_members(self, requests: bool = False, custom_members: list[int] | None = None):
        glist: list[User | Member] = []
        for member in (custom_members if custom_members is not None else (self.requests if requests else self.members_id)):
            try:
                glist.append(await deps.main_guild.fetch_member(member))
            except:
                continue
        return glist
    
    async def get_v2_info(self, leader_mode: bool = False):
        if leader_mode:
            return [
                ui.Container(
                    ui.Section(
                        ui.TextDisplay('# ' + self.name),
                        accessory=ui.Button(label='Изменить', custom_id='Group edit name ' + str(self.id))
                    ),
                    ui.Separator(),
                    ui.TextDisplay('Лидер: ' + '<@' + str(self.leader_id) + '>'),
                    ui.TextDisplay('Уровень: ' + str(self.level)),
                    ui.TextDisplay('Участники: ' + ', '.join([(member.mention + ' (' + member.display_name + ')') for member in (await self.get_members())])),
                    ui.Separator(),
                    (
                        ui.Section(
                            ui.TextDisplay('Есть заявки на вступление'),
                            accessory=ui.Button(label='Рассмотреть', custom_id='Group requests ' + str(self.id))
                        ) if self.requests else ui.TextDisplay('Заявок на вступление нет')
                    )
                ),
                ui.ActionRow(
                    ui.Button(label='Удалить', custom_id='Group ask delete ' + str(self.id), style=ButtonStyle.danger)
                )
            ]
        return [
            ui.Container(
                ui.TextDisplay('# ' + self.name),
                ui.Separator(),
                ui.TextDisplay('Лидер: ' + '<@' + str(self.leader_id) + '>'),
                ui.TextDisplay('Уровень: ' + str(self.level)),
                ui.TextDisplay('Участники: ' + ', '.join([(member.mention + ' (' + member.display_name + ')') for member in (await self.get_members())])),
                ui.Separator(),
                (
                    ui.TextDisplay('Есть заявки на вступление') if self.requests else ui.TextDisplay('Заявок на вступление нет')
                )
            )
        ]
    
    async def get_requests_menu(self):
        options = [
                    SelectOption(
                        label=member.display_name,
                        description=member.name,
                        value=str(member.id)
                    )
                    for member in (await self.get_members(True))
        ]
        return [
            ui.Container(
                ui.TextDisplay('# ' + self.name),
                ui.Separator(),
                ui.TextDisplay('Ниже представлен список запросов на вступление в вашу организацию'),
                ui.ActionRow(
                    ui.StringSelect(
                        placeholder='Принять заявку',
                        custom_id='Group accept request ' + str(self.id),
                        options=options
                    )
                ),
                ui.ActionRow(
                    ui.StringSelect(
                        placeholder='Отклонить заявку',
                        custom_id='Group reject request ' + str(self.id),
                        options=options
                    )
                )
            )
        ] if options else [
            ui.Container(
                ui.TextDisplay('# ' + self.name),
                ui.Separator(),
                ui.Section(
                    ui.TextDisplay('Запросов на вступление больше нет'),
                    accessory=ui.Button(label='Вернуться', custom_id='Group view ' + str(self.id))
                )
                
            )
        ]
    
    @property
    def members_id(self): return self._members_id

    @property
    def tags(self): return self._tags
        
    @property
    def upgrades(self): return self._upgrades
        
    @property
    def requests(self): return self._requests

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
                               SET tags = ?
                               WHERE id = ?
                               """, (';'.join(self._tags), self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)

    @upgrades.setter
    def upgrades(self, value: list[str]):
        try:
            with deps.interactive as connect:
                self._upgrades = value
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE groups 
                               SET upgrades = ?
                               WHERE id = ?
                               """, (';'.join(self._upgrades), self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)
            
    @requests.setter
    def requests(self, value: list[int]):
        try:
            with deps.interactive as connect:
                self._requests = value
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE groups 
                               SET requests = ?
                               WHERE id = ?
                               """, (';'.join(str(i) for i in self._requests), self.id))
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
                               """, ('%' + str(id_) + '%', ))
                fetch = cursor.fetchone()
                self.group: Group | None = Group(fetch['id']) if fetch else None

                cursor.execute("""
                               SELECT name 
                               FROM votes
                               WHERE votes LIKE ?
                               """, ('%' + str(self.id) + '%', ))
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


class Config:
    @staticmethod
    def get(key):
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute(f"""
                               SELECT {key}
                               FROM config
                               """)
                fetch = cursor.fetchone()[key]
                cursor.close()
                return fetch
        except Exception as e:
            logging.error(e)
            
    @staticmethod
    def set(key, value):
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute(f"""
                               UPDATE config
                               SET {key} = ?
                               """, (value, ))
                cursor.close()
        except Exception as e:
            logging.error(e)