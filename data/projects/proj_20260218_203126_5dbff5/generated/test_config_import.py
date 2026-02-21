from config import get_config

def test_import():
    config = get_config()
    print("Config imported successfully:", config)

if __name__ == "__main__":
    test_import()