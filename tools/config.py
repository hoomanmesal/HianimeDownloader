import json
import os

DEFAULT_CONFIG = {
    "hianime": {
        "server": "HD-2",
        "type": "sub"
    },
    "output_dir": "output",
    "aria": False,
    "no_subtitles": False
}

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    config = DEFAULT_CONFIG.copy()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)
                # Deep merge for hianime dict
                if "hianime" in user_config:
                    config["hianime"].update(user_config["hianime"])
                
                # Merge other top-level keys
                for key, value in user_config.items():
                    if key != "hianime":
                        config[key] = value
        except Exception as e:
            print(f"Error loading config.json: {e}")
    
    # Expand output_dir
    if config["output_dir"].startswith("~"):
        config["output_dir"] = os.path.expanduser(config["output_dir"])
    
    return config

def save_session(session_data):
    session_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".last_session.json")
    try:
        with open(session_path, "w") as f:
            json.dump(session_data, f, indent=4)
    except Exception as e:
        print(f"Error saving session: {e}")

def load_session():
    session_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".last_session.json")
    if os.path.exists(session_path):
        try:
            with open(session_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
    return None
