# This is from https://medium.com/@mahmudahsan/how-to-use-python-sqlite3-using-sqlalchemy-158f9c54eb32
# tinkering w/ it to learn sqlalchemy

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
# Global Variables
SQLITE                  = 'sqlite'

# Table Names
QUIZZES           = 'quizzes'
DISTRACTORS       = 'distractors'

class QuizLibDB:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}'
    }


    # Main DB Connection Ref Obj
    db_engine = None
    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
            print(self.db_engine)
        else:
            print("DBType is not found in DB_ENGINE")


    def create_db_tables(self):
        metadata = MetaData()
        sqliteusers = Table(QUIZZES, metadata,
                      Column('id', Integer, primary_key=True),
                      Column('title', String, nullable=False),
                      Column('question', String, nullable=False),
                      Column('answer',String, nullable=False)
                      )
        address = Table(DISTRACTORS, metadata,
                        Column('id', Integer, primary_key=True),
                        Column('quiz_id', None, ForeignKey('quizzes.id')),
                        Column('answer', String, nullable=False)
                        )
        try:
            metadata.create_all(self.db_engine)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!")
            print(e)

    # Insert, Update, Delete
    def execute_query(self, query=''):
        if query == '' : return
        #print (query)
        with self.db_engine.connect() as connection:
            try:
                connection.execute(query)
            except Exception as e:
                print(e)

    def print_all_data(self, table='', query=''):
        query = query if query != '' else "SELECT * FROM '{}';".format(table)
        print(query)
        with self.db_engine.connect() as connection:
            try:
                result = connection.execute(query)
            except Exception as e:
                print(e)
            else:
                for row in result:
                    print(row) # print(row[0], row[1], row[2])
                result.close()
        print("\n")

    def insert_quiz(self, title, question, answer):
        query = "INSERT INTO {TABLE}(id, title, question, answer)"\
                "VALUES (NULL, '{T}', '{Q}', '{A}');".format(TABLE=QUIZZES, T=title, Q=question, A=answer)
        self.execute_query(query)
        #self.print_all_data(QUIZZES)
    
    def insert_distractor(self, quiz_id, answer):
        query = "INSERT INTO {TABLE}(id, quiz_id, answer)"\
                "VALUES (NULL, '{Q}', '{A}');".format(TABLE=DISTRACTORS, Q=quiz_id, A=answer)
        self.execute_query(query)
        

    # Examples
    '''
    def sample_query(self):
        # Sample Query
        query = "SELECT first_name, last_name FROM {TBL_USR} WHERE " \
                "last_name LIKE 'M%';".format(TBL_Q=QUIZZES)
        self.print_all_data(query=query)
        # Sample Query Joining
        query = "SELECT u.last_name as last_name, " \
                "a.email as email, a.address as address " \
                "FROM {TBL_USR} AS u " \
                "LEFT JOIN {TBL_ADDR} as a " \
                "WHERE u.id=a.user_id AND u.last_name LIKE 'M%';" \
            .format(TBL_USR=USERS, TBL_ADDR=ADDRESSES)
        self.print_all_data(query=query)
    '''

    '''
    def sample_delete(self):
        query = "DELETE FROM {} WHERE id=3".format(USERS)
        self.execute_query(query)
        self.print_all_data(USERS)
        #query = "DELETE FROM {}".format(USERS)
        #self.execute_query(query)
        #self.print_all_data(USERS)
    '''    

    '''
    def sample_update(self):
        query = "UPDATE {} set first_name='XXXX' WHERE id={id}"\
            .format(USERS, id=3)
        self.execute_query(query)
        self.print_all_data(USERS)
    '''

def main():
    db = QuizLibDB(SQLITE, dbname='quizlib.sqlite')
    # Create Tables
    db.create_db_tables()
    db.insert_quiz(
        title=u'Sir Lancelot and the bridge keeper, part 1',
        question=u'What... is your name?',
        answer=u'Sir Lancelot of Camelot')
    db.insert_quiz(
        title=u'Sir Lancelot and the bridge keeper, part 2',
        question=u'What... is your quest?', 
        answer=u'To seek the holy grail'
    )
    db.insert_quiz(
        title=u'Sir Lancelot and the bridge keeper, part 3',
        question=u'What... is your favorite colour?', 
        answer=u'Blue'
    )

    db.print_all_data('quizzes')

    dists = {
    1: [ u'Sir Galahad of Camelot',
         u'Sir Arthur of Camelot',
         u'Sir Bevedere of Camelot',
         u'Sir Robin of Camelot'
        ],
    2: [ u'To bravely run away',
         u'To spank Zoot',
         u'To find a shrubbery'
        ],
    3: [ u'Green', u'Red', u'Yellow'
        ]
    }

    db.insert_distractor(
        quiz_id=1,
        answer=u''
    )
    

if __name__ == '__main__':
    main()
