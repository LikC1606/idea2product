from config import config_by_name

def test_config():
    try:
        config = config_by_name['development']
        print("Config loaded successfully:", config)
    except Exception as e:
        print("Error loading config:", e)

if __name__ == "__main__":
    test_config()