import pymysql
import time
import _thread


HOST = 'tslow.cn'
USER = 'test'
PASSWORD = 'test'
DATABASE = 'test_isolation'


def new_session():
    conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE, autocommit=True)
    return conn.cursor()


def reset():
    cursor = new_session()
    cursor.execute('truncate example_people')
    cursor.execute('insert into example_people values(1, "张三", 0)')
    print('-----')
    time.sleep(1)


def lost_update_a(use_transaction=False):
    cursor = new_session()
    if use_transaction:
        cursor.execute('begin')
    # 查张三当前余额
    cursor.execute('select money from example_people where name="张三" for update')
    old_money = cursor.fetchone()[0]
    # 假设业务处理花了一段时间
    time.sleep(2)
    new_money = old_money + 100
    # 更新张三余额 +100
    cursor.execute(f'update example_people set money={new_money} where name="张三"')
    if use_transaction:
        cursor.execute('commit')


def lost_update_b(use_transaction=False):
    cursor = new_session()
    if use_transaction:
        cursor.execute('begin')
    # 查张三当前余额
    cursor.execute('select money from example_people where name="张三" for update')
    old_money = cursor.fetchone()[0]
    # 假设业务处理花了一段时间
    time.sleep(1)
    new_money = old_money + 200
    # 更新张三余额 +200
    cursor.execute(f'update example_people set money={new_money} where name="张三"')
    if use_transaction:
        cursor.execute('commit')


def dirty_read_a(level='READ UNCOMMITTED'):
    cursor = new_session()
    cursor.execute(f'SET SESSION TRANSACTION ISOLATION LEVEL {level}')
    cursor.execute('begin')
    # 查张三当前余额
    cursor.execute('select money from example_people where name="张三" for update')
    old_money = cursor.fetchone()[0]
    # 更新张三余额 -500
    new_money = old_money - 500
    cursor.execute(f'update example_people set money={new_money} where name="张三"')
    # 假设业务处理花了一段时间
    time.sleep(2)
    # 发现异常，不应该 -500 的，rollback 恢复原状
    cursor.execute('rollback')


def dirty_read_b(level='READ UNCOMMITTED'):
    cursor = new_session()
    cursor.execute(f'SET SESSION TRANSACTION ISOLATION LEVEL {level}')
    cursor.execute('begin')
    time.sleep(1)
    # 查张三当前余额
    cursor.execute('select * from example_people where name="张三"')
    print(cursor.fetchall())
    cursor.execute('commit')


def unrepeatable_read_a(level='READ COMMITTED'):
    cursor = new_session()
    cursor.execute(f'SET SESSION TRANSACTION ISOLATION LEVEL {level}')
    cursor.execute('begin')
    # 查张三余额
    cursor.execute('select * from example_people where name="张三"')
    print(cursor.fetchall())
    time.sleep(2)
    # 过来一会再次查张三余额
    cursor.execute('select * from example_people where name="张三"')
    print(cursor.fetchall())
    cursor.execute('commit')


def unrepeatable_read_b(level='READ COMMITTED'):
    cursor = new_session()
    cursor.execute(f'SET SESSION TRANSACTION ISOLATION LEVEL {level}')
    cursor.execute('begin')
    time.sleep(1)
    # 更新张余额为 999
    cursor.execute('update example_people set money=999 where name="张三"')
    cursor.execute('commit')


def phantom_problem_a(level='REPEATABLE READ'):
    cursor = new_session()
    cursor.execute(f'SET SESSION TRANSACTION ISOLATION LEVEL {level}')
    cursor.execute('begin')
    # 以 “快照读” 形式查看所有数据列表
    cursor.execute('select * from example_people')
    print(cursor.fetchall())
    time.sleep(2)
    # 过了一会儿，以 “当前读” 形式再次查看所有数据列表
    cursor.execute('select * from example_people for update')
    print(cursor.fetchall())
    cursor.execute('commit')


def phantom_problem_b(level='REPEATABLE READ'):
    cursor = new_session()
    cursor.execute(f'SET SESSION TRANSACTION ISOLATION LEVEL {level}')
    cursor.execute('begin')
    time.sleep(1)
    # 插入新数据
    cursor.execute('insert into example_people values(2, "李四", 200)')
    cursor.execute('commit')



reset()
cursor = new_session()
cursor.execute('select * from example_people')
print(cursor.fetchall())
print('每次重置数据 都将张三余额置为 0')

print('====== 不使用事务隔离 ======')

reset()

print('两个线程分别读取张三余额，然后分别加 100 和 200')
_thread.start_new_thread(lost_update_a, (False,))
_thread.start_new_thread(lost_update_b, (False,))
time.sleep(3)

cursor.execute('select * from example_people')
print(cursor.fetchall())
print('现在读到张三最新的余额是 100，理论上应该是 0 + 100 + 200 = 300，这就是 “更新丢失”')


print('====== 使用事务隔离 ======')

reset()

print('两个线程分别读取张三余额，然后分别加 100 和 200')
_thread.start_new_thread(lost_update_a, (True,))
_thread.start_new_thread(lost_update_b, (True,))
time.sleep(4)

cursor.execute('select * from example_people')
print(cursor.fetchall())
print('读到张三最新的余额为 300，说明使用事务隔离能解决 “更新丢失” 问题！')


print('====== 使用 READ UNCOMMITTED 级别隔离 ======')

reset()

print('A 线程读取张三余额，期间会改动余额值，但最后会回滚')
_thread.start_new_thread(dirty_read_a, ('READ UNCOMMITTED',))

print('B 线程读取张三余额')
_thread.start_new_thread(dirty_read_b, ('READ UNCOMMITTED',))
time.sleep(3)

print('发现 B 线程读到了 -500, 这是 A 事务过程中产生的临时的脏数据，这就是 “脏读”')


print('====== 使用 READ COMMITTED 级别隔离 ======')

reset()

print('A 线程读取张三余额，期间会改动余额值，但最后会回滚')
_thread.start_new_thread(dirty_read_a, ('READ COMMITTED',))

print('B 线程读取张三余额')
_thread.start_new_thread(dirty_read_b, ('READ COMMITTED',))
time.sleep(3)

print('发现 B 线程读到的是 0, 说明使用 READ COMMITTED 级别能解决了 “脏读” 问题！')

# ------
reset()

print('A 线程分前后两次读取张三余额')
_thread.start_new_thread(unrepeatable_read_a, ('READ COMMITTED',))

print('B 线程去会修改张三的余额')
_thread.start_new_thread(unrepeatable_read_b, ('READ COMMITTED',))
time.sleep(3)

print('发现 A 线程在同一个事务中前后两次读到的数据不一样，这就是 “不可重复读”')


print('====== 使用 REPEATABLE READ 级别隔离 ======')

reset()

print('A 线程分前后两次读取张三余额')
_thread.start_new_thread(unrepeatable_read_a, ('REPEATABLE READ',))

print('B 线程会去修改张三的余额')
_thread.start_new_thread(unrepeatable_read_b, ('REPEATABLE READ',))
time.sleep(3)

print('前后两次读到的数据一致，说明使用 REPEATABLE READ 级别能解决了 “不可重复读” 问题！')

# ------
reset()

print('A 线程分前后两次读取所有数据列表')
_thread.start_new_thread(phantom_problem_a, ('REPEATABLE READ',))

print('B 线程会新增一行记录')
_thread.start_new_thread(phantom_problem_b, ('REPEATABLE READ',))
time.sleep(3)

print('发现 A 线程第二次读到的数据比前一次多了一行，这就是 “幻读”')


print('====== 使用 SERIALIZABLE 级别隔离 ======')

reset()

print('A 线程分前后两次读取所有数据列表')
_thread.start_new_thread(phantom_problem_a, ('SERIALIZABLE',))

print('B 线程会新增一行记录')
_thread.start_new_thread(phantom_problem_b, ('SERIALIZABLE',))
time.sleep(4)

print('前后两次读到的数据一致，说明使用 SERIALIZABLE 级别能解决了 “幻读” 问题！')

time.sleep(10)

