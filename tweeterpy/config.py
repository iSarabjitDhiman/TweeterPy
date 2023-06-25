# Configuration File
_DEFAULT_SESSION = None  # Used to reuse generated session. DON'T CHANGE IT

_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'

# Maximun number of retries for each request
MAX_RETRIES = 3

# request timeout - in seconds
TIMEOUT = 5

# Example {"http":"proxy_here","https":"proxy_here"} Accepts python dictionary.
PROXY = None

# Directory path/name to save and load logged in sessions/cookies. Default path is current directory. i.e. current_path/Twitter Saved Sessions
SESSION_DIRECTORY = "Twitter Saved Sessions"

if __name__ == "__main__":
    pass
