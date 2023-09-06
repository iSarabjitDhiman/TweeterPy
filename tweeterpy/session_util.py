import pickle
import requests
import os
import logging.config
from . import config

logging.config.dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def _create_session_directory(directory_path=None):
    if directory_path is None:
        directory_path = config.SESSION_DIRECTORY or os.getcwd()

    directory_path = os.path.realpath(os.path.expanduser(directory_path))
    os.makedirs(directory_path, exist_ok=True)
    return directory_path


def _show_saved_sessions(directory_path=None):
    if directory_path is None:
        directory_path = _create_session_directory()
    all_files = os.listdir(directory_path)
    session_files = [f"{count}. {os.path.splitext(file)[0]}" for count, file in enumerate(
        all_files, start=1) if file.endswith(".pkl")]
    print("\n".join(session_files))
    file_number = int(
        input("\nChoose a Number to Load an Exising Session : ").strip())
    while file_number >= len(all_files)+1 or file_number == 0:
        file_number = int(input("\nChoose a vaild Number : ").strip())
    else:
        file_path = os.path.join(directory_path, all_files[file_number-1])
    return file_path


def save_session(filename=None, path=None, session=None):
    if session is None or not isinstance(session, requests.Session):
        logger.warn(
            "No Session object given. Trying to save existing/default Session...")
        if config._DEFAULT_SESSION:
            session = config._DEFAULT_SESSION
        else:
            raise TypeError(f'{session} is not a requests Session Object...')
    if filename is None:
        filename = str(
            input("Enter Username/Account Name to Save the Session : ")).strip()
    if path is None:
        path = _create_session_directory()
    filename = f"{filename}.pkl"
    file_path = os.path.join(path, filename)
    with open(file_path, "wb") as file:
        pickle.dump([session.headers, session.cookies], file)
    return file_path


def load_session(file_path=None, session=None):
    if file_path is None:
        file_path = _show_saved_sessions()
    with open(file_path, "rb") as file:
        headers, cookies = pickle.load(file)
    if session is None:
        session = config._DEFAULT_SESSION or requests.Session()
    session.headers = headers
    session.cookies = cookies
    config._DEFAULT_SESSION = session
    return session


if __name__ == "__main__":
    pass
