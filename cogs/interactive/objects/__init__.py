import dependencies as deps
import logging
from disnake import Member, User, ui, ButtonStyle, SelectOption
import datetime as dt

class Ability:
    names = ('## Откаты откатов Эрнесто', )
    description = ('Бокировка решений Эрнесто об откате РП событий. Он больше не сможет безнаказанно мешать РП кураторам. Его откатом считается любое сообщение, начинающейся с `# Откат` без учета регистра', )

    @staticmethod
    def build_container(group: 'Group', buttons: bool = False):
        lvl1_cd = 60 * 60 * 2
        last_use_1 = group.last_use_ability.get(1, None)
        subs = dt.datetime.now() - last_use_1 if last_use_1 is not None else None
        lvl1 = [
            ui.Section(
                ui.TextDisplay(Ability.names[0]),
                accessory=ui.Button(
                    label='Использовать', 
                    custom_id='Ability use 1 ' + str(group.id), 
                    disabled= not (((subs.seconds >= lvl1_cd) if subs is not None else True) and (buttons)))
            ),
            ui.TextDisplay(Ability.description[0])
        ]
        return [
            ui.Container(
                *lvl1 if group.level >= 1 else []
            )
        ] if group.level > 0 else []

class Task:
    def __init__(self, id_: int):
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                              SELECT *
                              FROM tasks
                              WHERE id = ?
                """, (id_, ))
                fetch = cursor.fetchone()
                if not fetch: raise ValueError('Not found Task')
                self.id = id_
                self.name: str = fetch['name']
                self.description: str | None = fetch['description'] or None
                self.level: int = fetch['level']
                self.group: 'Group | None' = None
        except Exception as e:
            logging.error(e)
    
    @classmethod
    def all(cls, level = 1) -> 'list[Task]': # type: ignore
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                                SELECT id
                                from tasks
                                WHERE level = ?
                """, (level, ))
                fetches = cursor.fetchall()
                glist = []
                for fetch in fetches:
                    fetch = dict(fetch)
                    glist.append(cls(int(fetch['id'])))
                return glist
                # return [cls(int(fetch['id']) for fetch in fetches)] # type: ignore
        except Exception as e:
          logging.error(e)
    
    def get_v2_info(self, complete_button: bool = False):
        return [
            ui.Container (
                ui.TextDisplay('# ' + self.name),
                ui.Separator(),
                ui.TextDisplay(self.description or 'Описание отсутствует'),
                ui.ActionRow(
                    ui.Button(
                        label='Завершить задание', 
                        disabled= (self.group is None) or (not complete_button), 
                        custom_id=('Task complete ' + str(self.group.id)) if self.group is not None else None
                    )
                )
            )
        ]
          
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
                self._level = int(fetch['level'])
                self._upgrade_points: int = fetch['upgrade_points']
                self._members_id: list[int] = [int(i) for i in str(fetch['members']).split(';')] if fetch['members'] else []
                self._tags: list[str] = str(fetch['tags']).split(';') if fetch['tags'] else []
                self._upgrades: list[str] = str(fetch['upgrades']).split(';') if fetch['upgrades'] else []
                self._requests: list[int] = [int(i) for i in str(fetch['requests']).split(';')] if fetch['requests'] else []
                self._task: Task | None = Task(fetch['task']) if fetch['task'] else None
                self._completed_tasks: list[str] = str(fetch['completed_tasks']).split(';') if fetch['completed_tasks'] else []
                self._last_use_ability: dict[int, dt.datetime] = {}
                if fetch['last_use_ability']:
                    for kv in str(fetch["last_use_ability"]).split(';'):
                        k, v = kv.split(':')[0], ''.join(kv.split(':')[1:])
                        k = int(k)
                        v = dt.datetime.fromisoformat(v)
                        self._last_use_ability[k] = v
                if self._task:
                    self._task.group = self
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
    
    def delete(self):
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                               DELETE
                               FROM groups
                               WHERE id = ?
                               """, (self.id, ))
                connect.commit()
                cursor.close()
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
    
    async def get_v2_info(self, leader_mode: bool = False, ask_delete: bool = True):
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
                    ),
                    (
                        ui.Section(
                            ui.TextDisplay('Доступно задание: **' + self.task.name + '**'),
                            accessory=ui.Button(label='Посмотреть', custom_id='Task view ' + str(self.task.id) + ' ' + str(self.id))
                        )  if self.task is not None else ui.Section (
                            ui.TextDisplay('Задание не выбрано'),
                            accessory=ui.Button(label='Выбрать', custom_id='Task choice ' + str(self.id))
                        )
                    ),
                    *([ui.Section(
                        ui.TextDisplay('Посмотреть способности'),
                        accessory=ui.Button(
                            label='Посмотреть', 
                            custom_id='Group ability ' + str(self.id), 
                            disabled= not bool(Ability.build_container(self)))
                    )] if self.level > 0 else [])
                ),
                ui.ActionRow(
                    *(
                        [
                            ui.Button(
                                label='Удалить', 
                                custom_id='Group ask delete ' + str(self.id), 
                                style=ButtonStyle.danger
                            )
                        ] if ask_delete else 
                        [
                            ui.Button(
                                label='Вы уверены?',
                                custom_id='Group delete ' + str(self.id),
                                style=ButtonStyle.danger
                            ),
                            ui.Button(
                                label='Нет, не уверены',
                                custom_id='Group view ' + str(self.id)
                            )
                        ]
                    )
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
                ),
                (
                    ui.Section(
                        ui.TextDisplay('Доступно задание: **' + self.task.name + '**'),
                        accessory=ui.Button(label='Посмотреть', custom_id='Task view ' + str(self.task.id) + ' ' + str(self.id))
                    )  if self.task is not None else ui.Section (
                        ui.TextDisplay('Задание недоступно'),
                        accessory=ui.Button(label='Посмотреть', disabled=True)
                    )
                ),
                *([ui.Section(
                    ui.TextDisplay('Посмотреть способности'),
                    accessory=ui.Button(
                        label='Посмотреть', 
                        custom_id='Group ability ' + str(self.id), 
                        disabled= not bool(Ability.build_container(self)))
                )] if self.level > 0 else [])
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

    @property
    def completed_tasks(self): return self._completed_tasks

    @property
    def last_use_ability(self): return self._last_use_ability

    @property
    def task(self): return self._task

    @property
    def upgrade_points(self): return self._upgrade_points

    @property
    def level(self): return self._level

    @level.setter
    def level(self, value: int):
        try:
            self._level = value
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                              UPDATE groups
                              SET level = ?
                              WHERE id = ?
                """, (value, self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)

    @upgrade_points.setter
    def upgrade_points(self, value):
        try:
            self._upgrade_points = value
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                              UPDATE groups
                              SET upgrade_points = ?
                              WHERE id = ?
                """, (value, self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)
    
    @task.setter
    def task(self, value: Task | None):
        try:
            self._task = value
            if value is not None:
                self._task.group = self # type: ignore
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute("""
                              UPDATE groups
                              SET task = ?
                              WHERE id = ?
                """, (value.id if value else None, self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)
    
    @last_use_ability.setter
    def last_use_ability(self, value: dict[int, dt.datetime]):
        try:
            with deps.interactive as connect:
                self._last_use_ability = value
                items = []
                for k, v in value.items():
                    items.append(str(k) + ':' + v.isoformat())
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE groups
                               SET last_use_ability = ?
                               WHERE id = ?
                               """, (';'.join(items), self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)

    @completed_tasks.setter
    def completed_tasks(self, value): 
        try:
            with deps.interactive as connect:
                self._completed_tasks = value
                cursor = connect.cursor()
                cursor.execute("""
                               UPDATE groups 
                               SET completed_tasks = ?
                               WHERE id = ?
                               """, (';'.join(self._completed_tasks), self.id))
                connect.commit()
                cursor.close()
        except Exception as e:
            logging.error(e)

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
    
    @staticmethod
    def all_ids() -> list[int]:
        try:
            with deps.interactive as connect:
                cursor = connect.cursor()
                cursor.execute(r"""
                               SELECT *
                               FROM players
                               WHERE tags LIKE '%enabled%'
                               """)
                fetches = cursor.fetchall()
                return [int(fetch['player_id']) for fetch in fetches]
        except Exception as e:
            logging.warning(e)
            return []


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