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

if __name__ == "__main__":
    pytest.main(["-v", __file__])
