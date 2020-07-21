import random
import time

from django.core import serializers
from django.db import transaction
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect

from example.models import People


People.objects.get_or_create(name='张三')


def all_people_response():
    ps = People.objects.order_by('id')
    r = serializers.serialize('python', ps)
    return JsonResponse(r, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 4})


def index(request):
    return HttpResponseRedirect('/reset/')


def reset(request):
    p = People.objects.get(name='张三')
    p.money = 0
    p.save()
    People.objects.exclude(name='张三').delete()
    text = """<pre>
    # 隔离级别实验室
    
    使用 MySQL InnoDB 引擎
    
    每一次实验前可以通过 http://127.0.0.1:8000/reset 重置一下张三的余额为 0
    
    ## 1 不使用事务隔离，会产生 “更新丢失” 问题。
    
        先请求 http://127.0.0.1:8000/add_100
        约 3-5 秒后，请求 http://127.0.0.1:8000/add_200
        等两个请求都成功返回后，再请求 http://127.0.0.1:8000/get_zhang3
        理论上，看到余额应为 0 + 100 + 200 = 300，实际上余额为 100 或 200，这就是 “更新丢失”
    
    ## 2 read uncommitted 事务隔离级别，避免了 “更新丢失” ，但还会产生 “脏读” 问题。
    
        settings.py 中设置 OPTIONS: {'isolation_level': 'read uncommitted'}
        先请求 http://127.0.0.1:8000/add_100_atomic
        约 3-5 秒后，请求 http://127.0.0.1:8000/add_200_atomic
        等两个请求都成功返回后，再请求 http://127.0.0.1:8000/get_zhang3
        查看到余额为 300，说明避免了 “更新丢失”
    
        先请求 http://127.0.0.1:8000/add_300_atomic
        约 1 秒后，请求 http://127.0.0.1:8000/get_zhang3
        读取到的张三余额出现了 -200，这是读到了 add_300_atomic 事务过程中的 “脏数据”，产生了 “脏读” 问题
    
    ## 3 read committed 事务隔离级别，避免了 “脏读” ，但还会产生 “不可重复读” 问题。
    
        settings.py 中设置 OPTIONS: {'isolation_level': 'read committed'}
        先请求 http://127.0.0.1:8000/add_300_atomic
        约 1 秒后，请求 http://127.0.0.1:8000/get_zhang3
        这时读到的余额是 0，等第一个请求成功返回后再次请求 get_zhang3，可以看到 300，说明避免了 “脏读”
    
        先请求 http://127.0.0.1:8000/get_zhang3_twice
        约 3 秒后，请求 http://127.0.0.1:8000/add_200_atomic
        在一个事务里我们期望前后两次对同一个数据的读取结果应该是一致的
        第一个请求返回结果 {"money1": 0, "money2": 200, "result": "事务内前后读取数值不一致"}，说明遇到了 “不可重复读” 问题
    
    ## 4 repeatable read 事务隔离级别，避免了 “不可重复读” ，但还会产生 “幻读” 问题。
    
        settings.py 中设置 OPTIONS: {'isolation_level': 'repeatable read'}
        先请求 http://127.0.0.1:8000/get_zhang3_twice
        约 3 秒后，请求 http://127.0.0.1:8000/add_200_atomic
        第一个请求返回结果 {"money1": 0, "money2": 0, "result": "事务内前后读取数值一致"}，说明避免了 “不可重复读” 问题
    
        先请求 http://127.0.0.1:8000/get_all_twice
        约 3 秒后，请求 http://127.0.0.1:8000/add_people
        第一个请求返回结果 {"names1": ["张三"], "names2": ["张三", "杨九"], "result": "事务内前后读取列表不一致"}，说明遇到了 “幻读” 问题
    
    ## 5 serializable 事务隔离级别，避免了 “幻读” 问题。
    
        settings.py 中设置 OPTIONS: {'isolation_level': 'serializable'}
        先请求 http://127.0.0.1:8000/get_all_twice
        约 3 秒后，请求 http://127.0.0.1:8000/add_people
        第一个请求返回结果 {"names1": ["张三"], "names2": ["张三"], "result": "事务内前后读取列表一致"}，说明避免了 “幻读” 问题
    
    事务的隔离级别越高，数据的准确性越高，但效率越低下，需要根据业务场景选择合适的隔离级别。 
    </pre>"""
    return HttpResponse(text)


def info(request):
    return all_people_response()


def add_100(request):
    p = People.objects.get(name='张三')
    money_old = p.money
    print('开始等10秒')
    time.sleep(10)
    print('等10秒完成')
    money_new = money_old + 100
    p.money = money_new
    p.save()
    return HttpResponse('ok')


def add_200(request):
    p = People.objects.get(name='张三')
    money_old = p.money
    print('开始等5秒')
    time.sleep(5)
    print('等5秒完成')
    money_new = money_old + 200
    p.money = money_new
    p.save()
    return HttpResponse('ok')


@transaction.atomic()
def add_100_atomic(request):
    p = People.objects.select_for_update().get(name='张三')
    money_old = p.money
    print('开始等10秒')
    time.sleep(10)
    print('等10秒完成')
    money_new = money_old + 100
    p.money = money_new
    p.save()
    return HttpResponse('ok')


@transaction.atomic()
def add_200_atomic(request):
    p = People.objects.select_for_update().get(name='张三')
    money_old = p.money
    print('开始等5秒')
    time.sleep(5)
    print('等5秒完成')
    money_new = money_old + 200
    p.money = money_new
    p.save()
    return HttpResponse('ok')


@transaction.atomic()
def add_300_atomic(request):
    p = People.objects.select_for_update().get(name='张三')
    p.money -= 200
    p.save()
    print('开始等6秒')
    time.sleep(6)
    print('等6秒完成')
    p.money += 500
    p.save()
    return HttpResponse('ok')


@transaction.atomic()
def get_zhang3(request):
    p = People.objects.get(name='张三')
    money = p.money
    r = {'money': money}
    return JsonResponse(r)


@transaction.atomic()
def get_zhang3_twice(request):
    p = People.objects.get(name='张三')
    print('money1:', p.money)
    money1 = p.money
    print('开始等12秒')
    time.sleep(12)
    print('等12秒完成')
    p = People.objects.get(name='张三')
    print('money2:', p.money)
    money2 = p.money
    if money1 == money2:
        result = '事务内前后读取数值一致'
    else:
        result = '事务内前后读取数值不一致'
    r = {
        'money1': money1,
        'money2': money2,
        'result': result,
    }
    return JsonResponse(r, json_dumps_params={'ensure_ascii': False})


@transaction.atomic()
def get_all_twice(request):
    ps = People.objects.all()  # 快照读
    names1 = []
    for p in ps:
        names1.append(p.name)
    names1.sort()
    print(names1)
    print('开始等8秒')
    time.sleep(8)
    print('等8秒完成')
    ps = People.objects.select_for_update().all()  # 当前读
    names2 = []
    for p in ps:
        names2.append(p.name)
    names2.sort()
    print(names2)
    if names1 == names2:
        result = '事务内前后读取列表一致'
    else:
        result = '事务内前后读取列表不一致'
    r = {
        'names1': names1,
        'names2': names2,
        'result': result,
    }
    # https://zhuanlan.zhihu.com/p/103580034
    # 可重复读隔离级别下，一个事务中只使用当前读，或者只使用快照读也能避免幻读。
    return JsonResponse(r, json_dumps_params={'ensure_ascii': False})


@transaction.atomic()
def add_people(request):
    People.objects.create(name=random.choice(['李四', '王五', '赵六', '钱七', '孙八', '杨九', '吴十']))
    time.sleep(2)
    return HttpResponse('ok')

