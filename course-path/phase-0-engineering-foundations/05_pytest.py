from Sample import add,div,UserManager
import pytest

def test_add():
    assert add(1,2)==3

def test_div():
    assert div(4,2)==2

def test_div_by_zero():
    with pytest.raises(ZeroDivisionError):
        div(4,0)


@pytest.fixture

def user_manager():
    return UserManager()

def test_add_user(user_manager):
    user_manager.add_user("John", "[EMAIL_ADDRESS]")
    assert user_manager.get_user("John") == "[EMAIL_ADDRESS]"

def test_get_user(user_manager):
    user_manager.add_user("John", "[EMAIL_ADDRESS]")
    assert user_manager.get_user("John") == "[EMAIL_ADDRESS]"

def test_delete_user(user_manager):
    user_manager.add_user("John", "[EMAIL_ADDRESS]")
    user_manager.delete_user("John")
    assert user_manager.get_user("John") is None

def test_update_user(user_manager):
    user_manager.add_user("John", "[EMAIL_ADDRESS]")
    user_manager.update_user("John", "[EMAIL_ADDRESS]")
    assert user_manager.get_user("John") == "[EMAIL_ADDRESS]"

def test_list_users(user_manager):
    user_manager.add_user("John", "[EMAIL_ADDRESS]")
    user_manager.add_user("Jane", "[EMAIL_ADDRESS]")
    assert user_manager.list_users() == {"John": "[EMAIL_ADDRESS]", "Jane": "[EMAIL_ADDRESS]"}


import pytest

def process_withdrawal(balance, amount):
    if amount > balance:
        return False, balance
    return True, balance - amount

@pytest.mark.parametrize(
    "initial, withdrawal, expected_success, expected_balance",
    [
        (100, 40, True, 60),    # Normal withdrawal
        (100, 100, True, 0),    # Exact balance
        (50, 100, False, 50),   # Insufficient funds
    ]
)
def test_withdrawals(initial, withdrawal, expected_success, expected_balance):
    success, new_balance = process_withdrawal(initial, withdrawal)
    assert success == expected_success
    assert new_balance == expected_balance

# test_database.py
import sqlite3
import pytest

@pytest.fixture(scope="module")
def sqlite_db():
    # Setup: runs ONCE before all tests in this module
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE inventory (sku TEXT PRIMARY KEY, qty INT)")
    conn.commit()

    yield conn  # Hand control over to tests

    # Teardown: runs ONCE after all tests in this module finish
    conn.close()

def test_insert_stock(sqlite_db):
    cursor = sqlite_db.cursor()
    cursor.execute("INSERT INTO inventory VALUES ('LAPTOP-01', 15)")
    sqlite_db.commit()

    cursor.execute("SELECT qty FROM inventory WHERE sku='LAPTOP-01'")
    assert cursor.fetchone()[0] == 15


import pytest

def is_prime(n):
    if n<1:
        return False
    for i in range(2,n):
        if n%i==0:
            return False
    return True

@pytest.mark.parametrize("number, expected",[
    (2, True),
    (3, True),
    (22, False),
    (97, True)
])

def test_is_prime(number, expected):
    assert is_prime(number)==expected

def add(a,b):
    if a==0 and b==0:
        raise ValueError("Both numbers cannot be zero")
    return a+b

def test_add():
    assert add(1,2)==3
    with pytest.raises(ValueError):
        add(0,0)
    assert add(1,0)==1
    assert add(0,1)==1
    assert add(0.3,0.1)==pytest.approx(0.4)

import os

def get_db_host():
    return os.getenv("DB_HOST", "localhost")

def test_custom_db_host(monkeypatch):
    # Temporarily set an environment variable
    monkeypatch.setenv("DB_HOST", "prod-cluster.internal")
    assert get_db_host() == "prod-cluster.internal"
    # Reverts automatically after test finishes

def test_detailed_failure():
    list_a = [1, 2, 3]
    list_b = [1, 2, 4]
    assert list_a == list_b

if __name__ == "__main__":
    pytest.main(["-v", __file__])
