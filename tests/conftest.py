# conftest.py
import pytest
from app import app

# @pytest.fixture(scope='module') - scoped to, will run once per module, the .py file
# @pytest.fixture(scope='function') - scoped to, will run once per function, a 'def' function
# @pytest.fixture(scope='session') - scoped to, will run once per session

@pytest.fixture(scope='session') # scoped to, will run once per session
def flask_app():
    
    



