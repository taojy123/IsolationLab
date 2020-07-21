# MySQL 隔离级别实验室

使用 InnoDB 引擎

http://127.0.0.1:8000/reset 每一次实验前可以先重置一下张三的余额为 0

1、不使用事务隔离，会产生 “更新丢失” 问题。
    先请求 http://127.0.0.1:8000/add_100
    约 3-5 秒后，请求 http://127.0.0.1:8000/add_200
    等两个请求都成功返回后，再请求 http://127.0.0.1:8000/get_zhang3
    理论上，看到余额应为 0 + 100 + 200 = 300，实际上余额为 100 或 200，这就是 “更新丢失”

2、read uncommitted 事务隔离级别，避免了 “更新丢失” ，但还会产生 “脏读” 问题。
    settings.py 中设置 OPTIONS: {'isolation_level': 'read uncommitted'}
    先请求 http://127.0.0.1:8000/add_100_atomic
    约 3-5 秒后，请求 http://127.0.0.1:8000/add_200_atomic
    等两个请求都成功返回后，再请求 http://127.0.0.1:8000/get_zhang3
    查看到余额为 300，说明避免了 “更新丢失”

    先请求 http://127.0.0.1:8000/add_300_atomic
    约 1 秒后，请求 http://127.0.0.1:8000/get_zhang3
    读取到的张三余额出现了 -200，这是读到了 add_300_atomic 事务过程中的 “脏数据”，产生了 “脏读” 问题

3、read committed 事务隔离级别，避免了 “脏读” ，但还会产生 “不可重复读” 问题。
    settings.py 中设置 OPTIONS: {'isolation_level': 'read committed'}
    先请求 http://127.0.0.1:8000/add_300_atomic
    约 1 秒后，请求 http://127.0.0.1:8000/get_zhang3
    这时读到的余额是 0，等第一个请求成功返回后再次请求 get_zhang3，可以看到 300，说明避免了 “脏读”

    先请求 http://127.0.0.1:8000/get_zhang3_twice
    约 3 秒后，请求 http://127.0.0.1:8000/add_200_atomic
    在一个事务里我们期望前后两次对同一个数据的读取结果应该是一致的
    第一个请求返回结果 {"money1": 0, "money2": 200, "result": "事务内前后读取数值不一致"}，说明遇到了 “不可重复读” 问题

4、repeatable read 事务隔离级别，避免了 “不可重复读” ，但还会产生 “幻读” 问题。
    settings.py 中设置 OPTIONS: {'isolation_level': 'repeatable read'}
    先请求 http://127.0.0.1:8000/get_zhang3_twice
    约 3 秒后，请求 http://127.0.0.1:8000/add_200_atomic
    第一个请求返回结果 {"money1": 0, "money2": 0, "result": "事务内前后读取数值一致"}，说明避免了 “不可重复读” 问题

    先请求 http://127.0.0.1:8000/get_all_twice
    约 3 秒后，请求 http://127.0.0.1:8000/add_people
    第一个请求返回结果 {"names1": ["张三"], "names2": ["张三", "杨九"], "result": "事务内前后读取列表不一致"}，说明遇到了 “幻读” 问题

5、serializable 事务隔离级别，避免了 “幻读” 问题。
    settings.py 中设置 OPTIONS: {'isolation_level': 'serializable'}
    先请求 http://127.0.0.1:8000/get_all_twice
    约 3 秒后，请求 http://127.0.0.1:8000/add_people
    第一个请求返回结果 {"names1": ["张三"], "names2": ["张三"], "result": "事务内前后读取列表一致"}，说明避免了 “幻读” 问题

事务的隔离级别越高，数据的准确性越高，但效率越低下，需要根据业务场景选择合适的隔离级别。 
