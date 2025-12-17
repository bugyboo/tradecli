import os

def get_project_root():
    # Get the directory of the current script, then go up to the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_exec_path( name: str ) -> str:
    return os.path.join( name )

def get_db_path( account_name: str ) -> str:
    return get_exec_path( f'{account_name}.db' )